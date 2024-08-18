"""
Consumes from like_topic (partitions 0-2).
Routes each action_type to the appropriate handler which builds
a notification payload and pushes it to the priority queue.

Partition assignment:
    0 => POST_LIKE / POST_UNLIKE
    1 => COMMENT_LIKE / COMMENT_UNLIKE
    2 => REPLY_LIKE / REPLY_UNLIKE
"""

import json
import logging
import time
from confluent_kafka import Consumer, KafkaError, KafkaException, Producer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("consumer.like")

# ── Kafka config ────────────────────────────────────────────────────────────

CONSUMER_CONF = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "like-consumer-group",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,        # manual commit after processing
    "max.poll.interval.ms": 300_000,
}

PRODUCER_CONF = {
    "bootstrap.servers": "localhost:9092",
    "client.id": "like-consumer-producer",
}

TOPIC = "like_topic"
DLQ_TOPIC = "like_topic.dlq"
PRIORITY_TOPIC = "priority_queue"

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2      # seconds; doubles each attempt
POLL_TIMEOUT = 1.0          # seconds

# ── Priority mapping ─────────────────────────────────────────────────────────
# Likes on comments/replies are lower priority than post likes.
# Account-level alerts (unlikes removing streaks, etc.) may escalate later.

ACTION_PRIORITY = {
    "POST_LIKE":      "high",
    "POST_UNLIKE":    "medium",
    "COMMENT_LIKE":   "medium",
    "COMMENT_UNLIKE": "low",
    "REPLY_LIKE":     "low",
    "REPLY_UNLIKE":   "low",
}

VALID_ACTION_TYPES = set(ACTION_PRIORITY.keys())


# ── DB enrichment (stub — replace with real DB/cache layer) ──────────────────

def fetch_user(user_id: str) -> dict:
    """Fetch display name and preferences for a user."""
    # TODO: replace with async DB call or Redis cache lookup
    return {"user_id": user_id, "display_name": f"User_{user_id}", "push_enabled": True}


def fetch_entity(entity_id: str, entity_type: str) -> dict:
    """Fetch title/preview text for the liked entity."""
    # TODO: replace with real entity lookup
    return {"entity_id": entity_id, "entity_type": entity_type, "preview": "…"}


# ── Notification payload builder ─────────────────────────────────────────────

def build_notification(data: dict, actor: dict, owner: dict, entity: dict) -> dict:
    action = data["action_type"]
    entity_type = action.split("_")[0].lower()          # "post" / "comment" / "reply"

    if action.endswith("_UNLIKE"):
        # Unlikes generally don't warrant a push — send a silent analytics event.
        template = f"{actor['display_name']} unliked your {entity_type}."
        notify = False
    else:
        template = f"{actor['display_name']} liked your {entity_type}: \"{entity['preview']}\""
        notify = owner.get("push_enabled", False)

    return {
        "type": "like_notification",
        "action_type": action,
        "recipient_id": data["action_to"],
        "actor_id": data["action_by"],
        "entity_id": data["action_on_id"],
        "entity_type": entity_type,
        "message": template,
        "notify": notify,
        "priority": ACTION_PRIORITY[action],
        "action_at": data["action_at"],
        "metadata": data.get("metadata", {}),
    }


# ── Handlers (one per action family) ─────────────────────────────────────────

def handle_like(data: dict, dlq_producer: Producer) -> dict | None:
    """Enrich and build notification for any *_LIKE / *_UNLIKE event."""
    actor = fetch_user(data["action_by"])
    owner = fetch_user(data["action_to"])
    entity_type = data["action_type"].split("_")[0]
    entity = fetch_entity(data["action_on_id"], entity_type)
    return build_notification(data, actor, owner, entity)


HANDLERS = {
    "POST_LIKE":      handle_like,
    "POST_UNLIKE":    handle_like,
    "COMMENT_LIKE":   handle_like,
    "COMMENT_UNLIKE": handle_like,
    "REPLY_LIKE":     handle_like,
    "REPLY_UNLIKE":   handle_like,
}


# ── DLQ ──────────────────────────────────────────────────────────────────────

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


# ── Core processing loop ──────────────────────────────────────────────────────

def process_message(msg, dlq_producer: Producer) -> dict | None:
    """
    Deserialize, validate, enrich, and handle one Kafka message.
    Returns the notification dict on success, None if silently skipped.
    Raises on unrecoverable errors (caller sends to DLQ).
    """
    raw = msg.value()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON decode error: {e}") from e

    action_type = data.get("action_type")
    if action_type not in VALID_ACTION_TYPES:
        raise ValueError(f"Unknown action_type: '{action_type}'")

    required = {"action_type", "action_on_id", "action_by", "action_to", "action_at"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Missing fields: {missing}")

    handler = HANDLERS[action_type]
    return handler(data, dlq_producer)


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

            # Retry loop with exponential backoff
            last_exc = None
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    notification = process_message(msg, dlq_producer)
                    if notification:
                        dispatch_to_priority_queue(dlq_producer, notification)
                    consumer.commit(message=msg)        # commit only on success
                    log.info(
                        f"OK  partition={msg.partition()} "
                        f"offset={msg.offset()} "
                        f"action={json.loads(msg.value()).get('action_type')}"
                    )
                    last_exc = None
                    break
                except (ValueError, KeyError) as e:
                    # Non-retryable: bad schema / unknown type — go straight to DLQ
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
                # Exhausted retries — send to DLQ and commit to unblock the partition
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