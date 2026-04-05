import os
import logging
from confluent_kafka import Producer

logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
LIKES_TOPIC = os.getenv("LIKES_TOPIC", "likes")
COMMENTS_TOPIC = os.getenv("COMMENTS_TOPIC", "comments")

_conf = {"bootstrap.servers": KAFKA_BROKER}

_likes_producer = None
_comments_producer = None


def _delivery_report(err, msg):
    if err is not None:
        logger.error("Message delivery failed: %s", err)
    else:
        logger.debug(
            "Message delivered to %s [%d]", msg.topic(), msg.partition()
        )


def get_likes_producer() -> Producer:
    global _likes_producer
    if _likes_producer is None:
        _likes_producer = Producer(_conf)
    return _likes_producer


def get_comments_producer() -> Producer:
    global _comments_producer
    if _comments_producer is None:
        _comments_producer = Producer(_conf)
    return _comments_producer


def produce_like(user_id: int, post_id: int, event_id: str):
    producer = get_likes_producer()
    key = f"{user_id}:{post_id}"
    value = (
        f'{{"user_id": {user_id}, "post_id": {post_id}, '
        f'"event_id": "{event_id}"}}'
    )
    try:
        producer.produce(
            topic=LIKES_TOPIC,
            key=key.encode("utf-8"),
            value=value.encode("utf-8"),
            callback=_delivery_report,
        )
        producer.poll(0)
    except BufferError:
        logger.warning("Local queue full, flushing...")
        producer.flush(timeout=10)
        producer.produce(
            topic=LIKES_TOPIC,
            key=key.encode("utf-8"),
            value=value.encode("utf-8"),
            callback=_delivery_report,
        )
        producer.poll(0)


def produce_comment(user_id: int, post_id: int, content: str, event_id: str):
    producer = get_comments_producer()
    key = f"{user_id}:{post_id}"
    value = (
        f'{{"user_id": {user_id}, "post_id": {post_id}, '
        f'"content": {repr(content)}, "event_id": "{event_id}"}}'
    )
    try:
        producer.produce(
            topic=COMMENTS_TOPIC,
            key=key.encode("utf-8"),
            value=value.encode("utf-8"),
            callback=_delivery_report,
        )
        producer.poll(0)
    except BufferError:
        logger.warning("Local queue full, flushing...")
        producer.flush(timeout=10)
        producer.produce(
            topic=COMMENTS_TOPIC,
            key=key.encode("utf-8"),
            value=value.encode("utf-8"),
            callback=_delivery_report,
        )
        producer.poll(0)
