"""
TOPIC => NETWORKING
PARTITION => 0 for FRIEND_REQ; 1 for FRIEND_REQ_ACK
"""

from confluent_kafka import Producer

        
# Kafka producer configuration
conf = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'my-producer'
}

# Create a Producer instance
producer = Producer(**conf)

def produce_message(topic, partition, value):
    producer.produce(topic, value=value, partition=partition)
    producer.poll(0)  # Poll to handle delivery reports


def producer_for_networking_topic(data):
    topic = 'NETWORKING'
    data_decoded = data.decode('utf-8')
    partition = 0
    if data_decoded.action_type == "FRIEND_REQ_ACK":
        partition = 1
    produce_message(topic, partition, data)
    producer.flush()