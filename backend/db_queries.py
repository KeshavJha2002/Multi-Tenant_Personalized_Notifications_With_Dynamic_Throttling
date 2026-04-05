import logging
import psycopg2
from db import get_conn

logger = logging.getLogger(__name__)


def insert_like(user_id: int, post_id: int, event_id: str) -> bool:
    """Insert a like. Returns True on success, False on duplicate (idempotent)."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO likes (user_id, post_id, event_id, created_at)
                VALUES (%s, %s, %s, NOW())
                """,
                (user_id, post_id, event_id),
            )
        conn.commit()
        return True
    except psycopg2.IntegrityError as e:
        conn.rollback()
        logger.info(
            "Duplicate like ignored (user_id=%s, post_id=%s, event_id=%s)",
            user_id,
            post_id,
            event_id,
        )
        return False
    finally:
        conn.close()


def insert_comment(user_id: int, post_id: int, content: str, event_id: str) -> bool:
    """Insert a comment after checking event_id dedup. Returns True on success, False if already processed."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM processed_events WHERE event_id = %s",
                (event_id,),
            )
            if cur.fetchone():
                logger.info("Duplicate comment skipped (event_id=%s)", event_id)
                return False

            cur.execute(
                """
                INSERT INTO comments (user_id, post_id, content, event_id, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (user_id, post_id, content, event_id),
            )

            cur.execute(
                """
                INSERT INTO processed_events (event_id, event_type, processed_at)
                VALUES (%s, 'comment', NOW())
                """,
                (event_id,),
            )

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error("Error inserting comment: %s", e)
        return False
    finally:
        conn.close()


def count_events_for_post(post_id: int, event_type: str) -> int:
    """Return total count of events (likes or comments) for a given post."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if event_type == "like":
                cur.execute(
                    "SELECT COUNT(*) FROM likes WHERE post_id = %s", (post_id,)
                )
            else:
                cur.execute(
                    "SELECT COUNT(*) FROM comments WHERE post_id = %s", (post_id,)
                )
            result = cur.fetchone()
            return result[0] if result else 0
    finally:
        conn.close()
