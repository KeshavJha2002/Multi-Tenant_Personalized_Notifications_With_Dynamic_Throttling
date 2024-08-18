"""
Consumes from comment_topic (partitions 0-1).
Comment events are higher priority than likes — a reply to someone's
content is more personal than a reaction.

Partition assignment:
    0 => COMMENT on COMMENT  (reply thread)
    1 => COMMENT on POST
"""

import json
import logging
import time
from confluent_kafka import Consumer, KafkaError, KafkaException, Producer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("consumer.comment")

# ── Kafka config ─────────────────────────────────────────────────────────────

CONSUMER_CONF = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "comment-consumer-group",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
    "max.poll.interval.ms": 300_000,
}

PRODUCER_CONF = {
    "bootstrap.servers": "localhost:9092",
    "client.id": "comment-consumer-producer",
}

TOPIC = "comment_topic"
DLQ_TOPIC = "comment_topic.dlq"
PRIORITY_TOPIC = "priority_queue"

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2
POLL_TIMEOUT = 1.0

# ── Priority mapping ──────────────────────────────────────────────────────────
# Comments on posts go to "high" — direct engagement with content.
# Replies in a thread go to "high" too, but could be "medium" if thread is deep.

ACTION_PRIORITY = {
    "COMMENT": {
        "POST":    "high",
        "COMMENT": "high",
    }
}

VALID_ACTION_TYPES = {"COMMENT"}
VALID_ACTION_ON    = {"POST", "COMMENT"}


# ── DB enrichment (stub) ──────────────────────────────────────────────────────

def fetch_user(user_id: str) -> dict:
    return {"user_id": user_id, "display_name": f"User_{user_id}", "push_enabled": True}


def fetch_entity(entity_id: str, entity_type: str) -> dict:
    """Fetch the parent entity (post or comment) the comment is on."""
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "preview": "…",            # first ~80 chars of the parent content
    }


# ── Notification payload builder ──────────────────────────────────────────────

def build_notification(data: dict, actor: dict, owner: dict, entity: dict) -> dict:
    action_on = data["action_on"]       # "POST" or "COMMENT"
    priority  = ACTION_PRIORITY["COMMENT"][action_on]

    if action_on == "POST":
        template = (
            f"{actor['display_name']} commented on your post: "
            f"\"{entity['preview']}\""
        )
    else:
        template = (
            f"{actor['display_name']} replied to your comment: "
            f"\"{entity['preview']}\""
        )

    return {
        "type": "comment_notification",
        "action_type": data["action_type"],
        "action_on": action_on,
        "recipient_id": data["action_to"],
        "actor_id": data["action_by"],
        "entity_id": data["action_on_id"],
        "entity_type": action_on.lower(),
        "message": template,
        "notify": owner.get("push_enabled", False),
        "priority": priority,
        "action_at": data["action_at"],
        "metadata": data.get("metadata", {}),
    }


# ── Handlers ──────────────────────────────────────────────────────────────────

def handle_comment(data: dict, dlq_producer: Producer) -> dict:
    actor  = fetch_user(data["action_by"])
    owner  = fetch_user(data["action_to"])
    entity = fetch_entity(data["action_on_id"], data["action_on"])
    return build_notification(data, actor, owner, entity)


HANDLERS = {
    "COMMENT": handle_comment,
}


# ── DLQ ───────────────────────────────────────────────────────────────────────

def send_to_dlq(producer: Producer, raw_value: bytes, reason: str) -> None:
    payload = {
        "source_topic": TOPIC,
        "reason": reason,
        "raw": raw_value.decode("utf-8", errors="replace"),
        "failed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    producer.produce(
        topic=DLQ_TOPIC,
        value=json.dumps(payload).encode("utf-8"),
        callback=lambda err, msg: log.error(f"DLQ delivery failed: {err}") if err else None,
    )
    producer.poll(0)
    log.warning(f"Sent message to DLQ. Reason: {reason}")


# ── Priority queue dispatch ───────────────────────────────────────────────────

def dispatch_to_priority_queue(producer: Producer, notification: dict) -> None:
    producer.produce(
        topic=PRIORITY_TOPIC,
        key=notification["priority"],
        value=json.dumps(notification).encode("utf-8"),
        callback=lambda err, msg: (
            log.error(f"Priority queue delivery failed: {err}") if err
            else log.debug(f"Dispatched [{notification['priority']}] notification")
        ),
    )
    producer.poll(0)


# ── Core processing ───────────────────────────────────────────────────────────

def process_message(msg, dlq_producer: Producer) -> dict:
    raw = msg.value()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON decode error: {e}") from e

    action_type = data.get("action_type")
    if action_type not in VALID_ACTION_TYPES:
        raise ValueError(f"Unknown action_type: '{action_type}'")

    action_on = data.get("action_on")
    if action_on not in VALID_ACTION_ON:
        raise ValueError(f"Unknown action_on: '{action_on}'")

    required = {"action_type", "action_on", "action_on_id", "action_by", "action_to", "action_at"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Missing fields: {missing}")

    return HANDLERS[action_type](data, dlq_producer)


def run():
    consumer = Consumer(CONSUMER_CONF)
    dlq_producer = Producer(PRODUCER_CONF)
    consumer.subscribe([TOPIC])
    log.info(f"Subscribed to '{TOPIC}' as group '{CONSUMER_CONF['group.id']}'")

    try:
        while True:
            msg = consumer.poll(timeout=POLL_TIMEOUT)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    log.debug(f"EOF reached: partition {msg.partition()}")
                else:
                    raise KafkaException(msg.error())
                continue

            last_exc = None
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    notification = process_message(msg, dlq_producer)
                    dispatch_to_priority_queue(dlq_producer, notification)
                    consumer.commit(message=msg)
                    log.info(
                        f"OK  partition={msg.partition()} "
                        f"offset={msg.offset()} "
                        f"action_on={json.loads(msg.value()).get('action_on')}"
                    )
                    last_exc = None
                    break
                except (ValueError, KeyError) as e:
                    log.error(f"Non-retryable error: {e}")
                    send_to_dlq(dlq_producer, msg.value(), str(e))
                    consumer.commit(message=msg)
                    last_exc = None
                    break
                except Exception as e:
                    last_exc = e
                    wait = RETRY_BACKOFF_BASE ** attempt
                    log.warning(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}. Retrying in {wait}s")
                    time.sleep(wait)

            if last_exc:
                log.error(f"Max retries exceeded. Sending to DLQ. Error: {last_exc}")
                send_to_dlq(dlq_producer, msg.value(), f"max retries exceeded: {last_exc}")
                consumer.commit(message=msg)

    except KeyboardInterrupt:
        log.info("Shutdown signal received.")
    finally:
        consumer.close()
        dlq_producer.flush()
        log.info("Consumer closed, DLQ producer flushed.")


if __name__ == "__main__":
    run()