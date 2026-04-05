import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from consumers.base import BaseConsumer
from db_queries import insert_comment, count_events_for_post
from batching import SyncBatchingLayer
from dispatcher import LoggingDispatcher

logger = logging.getLogger(__name__)

COMMENTS_TOPIC = "comments"
COMMENTS_GROUP = "comments-consumer-group"


class CommentConsumer(BaseConsumer):
    def __init__(self):
        dispatcher = LoggingDispatcher()
        batching = SyncBatchingLayer(
            get_count_func=count_events_for_post,
            dispatcher=dispatcher.dispatch,
        )
        super().__init__(topic=COMMENTS_TOPIC, group_id=COMMENTS_GROUP)
        self.batching = batching

    def process_message(self, value: dict) -> bool:
        try:
            user_id = int(value["user_id"])
            post_id = int(value["post_id"])
            content = str(value["content"])
            event_id = str(value["event_id"])

            logger.debug(
                "Processing comment: user_id=%s, post_id=%s, event_id=%s",
                user_id,
                post_id,
                event_id,
            )

            inserted = insert_comment(user_id, post_id, content, event_id)

            if inserted:
                logger.info(
                    "Comment inserted: user_id=%s, post_id=%s", user_id, post_id
                )
                self.batching.trigger(post_id=post_id, event_type="comment", event_id=event_id)
            else:
                logger.info(
                    "Duplicate comment skipped (idempotent): event_id=%s",
                    event_id,
                )

            return True

        except KeyError as e:
            logger.error("Missing required field: %s", e)
            return False
        except Exception as e:
            logger.error("Error processing comment message: %s", e)
            return False


def run_comment_consumer():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    consumer = CommentConsumer()
    consumer.start()


if __name__ == "__main__":
    run_comment_consumer()
