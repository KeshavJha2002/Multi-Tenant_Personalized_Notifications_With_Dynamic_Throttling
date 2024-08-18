"""
TOPIC  => mention_topic
PARTITIONS:
    0  => POST_MENTION       (user mentioned in a post body)
    1  => COMMENT_MENTION    (user mentioned in a comment)
    2  => STORY_MENTION      (user tagged in a story / media)
"""

"""
data = {
    action_type  : "POST_MENTION" | "COMMENT_MENTION" | "STORY_MENTION",
    action_on_id : <parent_entity_id>,   # post_id / comment_id / story_id
    action_by    : <mentioning_user_id>,
    action_to    : <mentioned_user_id>,  # the recipient of the notification
    action_at    : <iso_timestamp>,
    metadata     : {}                    # optional, e.g. {"position": 42}
                                         # character offset of @mention in body
}
"""

from confluent_kafka import Producer
import json

conf = {
    "bootstrap.servers": "localhost:9092",
    "client.id": "python-producer-mention",
}

producer = Producer(conf)

PARTITION_MAP = {
    "POST_MENTION":    0,
    "COMMENT_MENTION": 1,
    "STORY_MENTION":   2,
}

VALID_ACTION_TYPES = set(PARTITION_MAP.keys())
REQUIRED_KEYS = {"action_type", "action_on_id", "action_by", "action_to", "action_at"}


def delivery_callback(err, msg):
    if err is not None:
        print(f"[mention_topic] Delivery failed: {err}")
    else:
        print(
            f"[mention_topic] Delivered to partition {msg.partition()} "
            f"offset {msg.offset()}"
        )


def producer_for_mention_topic(data: dict) -> None:
    # --- Validation ---
    missing = REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(f"Missing required keys: {missing}")

    action_type = data["action_type"]
    if action_type not in VALID_ACTION_TYPES:
        raise ValueError(
            f"Invalid action_type '{action_type}'. "
            f"Must be one of: {VALID_ACTION_TYPES}"
        )

    if data["action_by"] == data["action_to"]:
        # Self-mentions are almost always upstream bugs (e.g. auto-tagging
        # the author). Reject early so consumers never see them.
        raise ValueError("action_by and action_to cannot be the same user.")

    # --- Routing ---
    partition = PARTITION_MAP[action_type]

    # Key: (mentioning_user, parent_entity) — groups all @mentions within
    # the same post/comment together, preserving order for the same context.
    message_key = f"{data['action_by']}:{data['action_on_id']}"

    try:
        producer.produce(
            topic="mention_topic",
            key=message_key,
            value=json.dumps(data),
            partition=partition,
            callback=delivery_callback,
        )
        producer.poll(0)
    except BufferError as e:
        print(f"[mention_topic] Producer queue full, flushing: {e}")
        producer.flush()
        producer.produce(
            topic="mention_topic",
            key=message_key,
            value=json.dumps(data),
            partition=partition,
            callback=delivery_callback,
        )
    except Exception as e:
        print(f"[mention_topic] Failed to produce message: {e}")
        raise
