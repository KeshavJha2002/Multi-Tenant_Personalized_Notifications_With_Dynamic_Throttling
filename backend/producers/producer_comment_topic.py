"""
TOPIC => COMMENT
PARTITION => 0 for COMMENT; 1 for POST
"""

"""
data = {
      action_type: "COMMENT",
      action_on: "POST"|"COMMENT",
      action_on_id: action_on_id,
      action_by: action_by,
      action_to: action_to,
      action_at: action_at
  }
"""

from confluent_kafka import Producer
import json

conf = {
    'bootstrap.servers': 'localhost:9092',  # Kafka server address
    'client.id': 'python-producer'           # Client identifier
}

producer = Producer(conf)

def delivery_callback(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def producer_for_comment_topic(data):
    required_keys = {'action_type', 'action_on', 'action_on_id', 'action_by', 'action_to', 'action_at'}
    if not required_keys.issubset(data):
        raise ValueError(f"Missing required keys: {required_keys - data.keys()}")

    if data['action_type'] != "COMMENT":
        raise ValueError(f"Invalid action_type: {data['action_type']}")

    if data['action_on'] not in ("COMMENT", "POST"):
        raise ValueError(f"Invalid action_on: {data['action_on']}")

    partition = 0 if data['action_on'] == "COMMENT" else 1
    message_value = json.dumps(data)

    try:
        producer.produce(
            topic='comment_topic',
            key=str(data['action_on_id']),   # ensures ordering per entity
            value=message_value,
            partition=partition,
            callback=delivery_callback
        )
        producer.poll(0)   # non-blocking, triggers callbacks
    except Exception as e:
        print(f"Failed to produce message: {e}")
        raise
