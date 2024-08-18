"""
TOPIC  => networking_topic
PARTITIONS:
    0  => FOLLOW / UNFOLLOW
    1  => CONNECTION_REQUEST / CONNECTION_ACCEPT / CONNECTION_REJECT
    2  => PROFILE_VIEW / BLOCK / UNBLOCK
"""

"""
data = {
    action_type : "FOLLOW" | "UNFOLLOW"
                | "CONNECTION_REQUEST" | "CONNECTION_ACCEPT" | "CONNECTION_REJECT"
                | "PROFILE_VIEW"
                | "BLOCK" | "UNBLOCK",
    action_by   : <user_id>,
    action_to   : <user_id>,
    action_at   : <iso_timestamp>,
    metadata    : {}   # optional, e.g. {"source": "search", "mutual_connections": 3}
}
"""

from confluent_kafka import Producer
import json

conf = {
    "bootstrap.servers": "localhost:9092",
    "client.id": "python-producer-networking",
}

producer = Producer(conf)

PARTITION_MAP = {
    "FOLLOW":               0,
    "UNFOLLOW":             0,
    "CONNECTION_REQUEST":   1,
    "CONNECTION_ACCEPT":    1,
    "CONNECTION_REJECT":    1,
    "PROFILE_VIEW":         2,
    "BLOCK":                2,
    "UNBLOCK":              2,
}

VALID_ACTION_TYPES = set(PARTITION_MAP.keys())

REQUIRED_KEYS = {"action_type", "action_by", "action_to", "action_at"}


def delivery_callback(err, msg):
    if err is not None:
        print(f"[networking_topic] Delivery failed: {err}")
    else:
        print(
            f"[networking_topic] Delivered to partition {msg.partition()} "
            f"offset {msg.offset()}"
        )


def producer_for_networking_topic(data: dict) -> None:
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
        raise ValueError("action_by and action_to cannot be the same user.")

    # --- Routing ---
    partition = PARTITION_MAP[action_type]

    # Key on (action_by, action_to) pair — ensures ordering of events
    # between the same two users lands on the same partition offset sequence.
    message_key = f"{data['action_by']}:{data['action_to']}"

    try:
        producer.produce(
            topic="networking_topic",
            key=message_key,
            value=json.dumps(data),
            partition=partition,
            callback=delivery_callback,
        )
        producer.poll(0)  # non-blocking flush of delivery callbacks
    except BufferError as e:
        # Local producer queue is full — back-pressure signal
        print(f"[networking_topic] Producer queue full, flushing: {e}")
        producer.flush()
        producer.produce(
            topic="networking_topic",
            key=message_key,
            value=json.dumps(data),
            partition=partition,
            callback=delivery_callback,
        )
    except Exception as e:
        print(f"[networking_topic] Failed to produce message: {e}")
        raise
