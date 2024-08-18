"""
TOPIC  => like_topic
PARTITIONS:
    0  => POST_LIKE / POST_UNLIKE
    1  => COMMENT_LIKE / COMMENT_UNLIKE
    2  => REPLY_LIKE / REPLY_UNLIKE
"""

"""
data = {
    action_type : "POST_LIKE" | "POST_UNLIKE"
                | "COMMENT_LIKE" | "COMMENT_UNLIKE"
                | "REPLY_LIKE" | "REPLY_UNLIKE",
    action_on_id : <target_entity_id>,
    action_by    : <user_id>,
    action_to    : <owner_user_id>,   # owner of the liked entity
    action_at    : <iso_timestamp>,
    metadata     : {}                 # optional, e.g. {"reaction_type": "heart"}
}
"""

from confluent_kafka import Producer
import json

conf = {
    "bootstrap.servers": "localhost:9092",
    "client.id": "python-producer-like",
}

producer = Producer(conf)

PARTITION_MAP = {
    "POST_LIKE":      0,
    "POST_UNLIKE":    0,
    "COMMENT_LIKE":   1,
    "COMMENT_UNLIKE": 1,
    "REPLY_LIKE":     2,
    "REPLY_UNLIKE":   2,
}

VALID_ACTION_TYPES = set(PARTITION_MAP.keys())
REQUIRED_KEYS = {"action_type", "action_on_id", "action_by", "action_to", "action_at"}

# unlike must always follow a like — guard against duplicate likes
_UNLIKE_COUNTERPARTS = {
    "POST_UNLIKE":    "POST_LIKE",
    "COMMENT_UNLIKE": "COMMENT_LIKE",
    "REPLY_UNLIKE":   "REPLY_LIKE",
}


def delivery_callback(err, msg):
    if err is not None:
        print(f"[like_topic] Delivery failed: {err}")
    else:
        print(
            f"[like_topic] Delivered to partition {msg.partition()} "
            f"offset {msg.offset()}"
        )


def producer_for_like_topic(data: dict) -> None:
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
        # Self-likes are a product decision; reject at producer level to keep
        # the consumer logic clean. Remove if self-likes are intentional.
        raise ValueError("action_by and action_to cannot be the same user.")

    # --- Routing ---
    partition = PARTITION_MAP[action_type]

    # Key: (user, target entity) pair — ensures like → unlike ordering is
    # preserved within the same partition for the same (user, entity) pair.
    message_key = f"{data['action_by']}:{data['action_on_id']}"

    try:
        producer.produce(
            topic="like_topic",
            key=message_key,
            value=json.dumps(data),
            partition=partition,
            callback=delivery_callback,
        )
        producer.poll(0)
    except BufferError as e:
        print(f"[like_topic] Producer queue full, flushing: {e}")
        producer.flush()
        producer.produce(
            topic="like_topic",
            key=message_key,
            value=json.dumps(data),
            partition=partition,
            callback=delivery_callback,
        )
    except Exception as e:
        print(f"[like_topic] Failed to produce message: {e}")
        raise
