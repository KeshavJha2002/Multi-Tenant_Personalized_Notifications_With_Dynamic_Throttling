import json
import logging
from batching import Batch

logger = logging.getLogger(__name__)


class LoggingDispatcher:
    def __init__(self, record_batch_func=None):
        self.record_batch = record_batch_func

    def dispatch(self, batch: Batch):
        logger.info(
            "NOTIFICATION_BATCH: post_id=%s, event_type=%s, batch_size=%s, wait_time=%.2fs, event_ids=%s",
            batch.post_id,
            batch.event_type,
            batch.batch_size,
            batch.wait_time,
            batch.event_ids,
        )

        if self.record_batch:
            try:
                self.record_batch(
                    post_id=batch.post_id,
                    event_type=batch.event_type,
                    batch_size=batch.batch_size,
                    event_ids=batch.event_ids,
                )
            except Exception as e:
                logger.error("Failed to record batch to DB: %s", e)


def logging_dispatcher(batch: Batch):
    logger.info(
        "NOTIFICATION_BATCH: post_id=%s, event_type=%s, batch_size=%s, wait_time=%.2fs",
        batch.post_id,
        batch.event_type,
        batch.batch_size,
        batch.wait_time,
    )
