import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from consumers.base import BaseConsumer
from db_queries import insert_like, count_events_for_post
from batching import SyncBatchingLayer
from dispatcher import LoggingDispatcher

logger = logging.getLogger(__name__)

LIKES_TOPIC = "likes"
LIKES_GROUP = "likes-consumer-group"


class LikeConsumer(BaseConsumer):
    def __init__(self):
        dispatcher = LoggingDispatcher()
        batching = SyncBatchingLayer(
            get_count_func=count_events_for_post,
            dispatcher=dispatcher.dispatch,
        )
        super().__init__(topic=LIKES_TOPIC, group_id=LIKES_GROUP)
        self.batching = batching

    def process_message(self, value: dict) -> bool:
        try:
            user_id = int(value["user_id"])
            post_id = int(value["post_id"])
            event_id = str(value["event_id"])

            logger.debug(
                "Processing like: user_id=%s, post_id=%s, event_id=%s",
                user_id,
                post_id,
                event_id,
            )

            inserted = insert_like(user_id, post_id, event_id)

            if inserted:
                logger.info(
                    "Like inserted: user_id=%s, post_id=%s", user_id, post_id
                )
                self.batching.trigger(post_id=post_id, event_type="like", event_id=event_id)
            else:
                logger.info(
                    "Duplicate like ignored (idempotent): user_id=%s, post_id=%s",
                    user_id,
                    post_id,
                )

            return True

        except KeyError as e:
            logger.error("Missing required field: %s", e)
            return False
        except Exception as e:
            logger.error("Error processing like message: %s", e)
            return False


def run_like_consumer():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    consumer = LikeConsumer()
    consumer.start()


if __name__ == "__main__":
    run_like_consumer()
