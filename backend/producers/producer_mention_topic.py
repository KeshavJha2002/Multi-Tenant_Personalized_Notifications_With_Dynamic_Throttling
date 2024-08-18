"""
TOPIC => MENTION
PARTITION => 0 for COMMENT; 1 for POST; 2 for CONVERSATION 
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


def producer_for_mention_topic(data):
    topic = 'MENTION'
    data_decoded = data.decode('utf-8')
    partition = 0
    if data_decoded.action_on == "POST":
        partition = 1
    elif data_decoded.action_on == "CONVERSATION":
        partition = 2
    produce_message(topic, partition, data)
    producer.flush()