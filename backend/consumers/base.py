import os
import json
import logging
import signal
import threading
from abc import ABC, abstractmethod
from typing import Callable, Optional

from confluent_kafka import Consumer, KafkaError, KafkaException

logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
GROUP_ID = os.getenv("CONSUMER_GROUP", "notification-consumer-group")


class BaseConsumer(ABC):
    def __init__(
        self,
        topic: str,
        group_id: Optional[str] = None,
        message_handler: Optional[Callable[[dict], bool]] = None,
    ):
        self.topic = topic
        self.group_id = group_id or GROUP_ID
        self.message_handler = message_handler
        self._running = False
        self._consumer: Optional[Consumer] = None
        self._shutdown_event = threading.Event()

    def _create_consumer(self) -> Consumer:
        conf = {
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": self.group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "session.timeout.ms": 30000,
            "heartbeat.interval.ms": 10000,
        }
        return Consumer(conf)

    def _signal_handler(self, signum, frame):
        logger.info("Shutdown signal received")
        self._running = False
        self._shutdown_event.set()

    def start(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self._consumer = self._create_consumer()
        self._consumer.subscribe([self.topic])
        self._running = True

        logger.info(
            "Consumer started: topic=%s, group_id=%s", self.topic, self.group_id
        )

        try:
            while self._running:
                msg = self._consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(
                            "Reached end of partition %s [%d]",
                            msg.topic(),
                            msg.partition(),
                        )
                    else:
                        logger.error("Kafka error: %s", msg.error())
                        raise KafkaException(msg.error())
                    continue

                try:
                    value = json.loads(msg.value().decode("utf-8"))
                    logger.debug(
                        "Received message: topic=%s, partition=%s, offset=%s",
                        msg.topic(),
                        msg.partition(),
                        msg.offset(),
                    )

                    success = self.process_message(value)

                    if success:
                        self._consumer.commit(message=msg)
                        logger.debug(
                            "Committed offset %s for partition %s",
                            msg.offset(),
                            msg.partition(),
                        )
                    else:
                        logger.warning(
                            "Message processing failed, not committing: partition=%s, offset=%s",
                            msg.partition(),
                            msg.offset(),
                        )

                except json.JSONDecodeError as e:
                    logger.error("Failed to decode message: %s", e)
                    self._consumer.commit(message=msg)
                except Exception as e:
                    logger.error("Error processing message: %s", e)
                    self._consumer.commit(message=msg)

        except KafkaException as e:
            logger.error("Kafka exception: %s", e)
        finally:
            self._cleanup()

    @abstractmethod
    def process_message(self, value: dict) -> bool:
        pass

    def _cleanup(self):
        if self._consumer:
            logger.info("Closing consumer for topic %s", self.topic)
            self._consumer.close()
            self._consumer = None

    def stop(self):
        self._running = False
        self._shutdown_event.set()
