#!/usr/bin/env python3
"""
Database initialization script.
Creates all tables required by the notification system.

Usage:
    python init_db.py

Environment variables:
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
"""

import os
import psycopg2

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "notification_system_users")


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS likes (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    post_id     INTEGER NOT NULL,
    event_id    VARCHAR(36) NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_likes_user_post
    ON likes (user_id, post_id);

CREATE INDEX IF NOT EXISTS idx_likes_post_id
    ON likes (post_id);

CREATE TABLE IF NOT EXISTS comments (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    post_id     INTEGER NOT NULL,
    content     TEXT NOT NULL,
    event_id    VARCHAR(36) NOT NULL UNIQUE,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comments_post_id
    ON comments (post_id);

CREATE TABLE IF NOT EXISTS processed_events (
    event_id      VARCHAR(36) PRIMARY KEY,
    event_type    VARCHAR(20) NOT NULL,
    processed_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notification_batches (
    id            SERIAL PRIMARY KEY,
    post_id       INTEGER NOT NULL,
    event_type    VARCHAR(20) NOT NULL,
    batch_size    INTEGER NOT NULL,
    event_ids     TEXT[] NOT NULL,
    dispatched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notification_batches_post_id
    ON notification_batches (post_id);
"""


def init_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()
        print("Database schema initialized successfully.")
        print("Tables created: likes, comments, processed_events, notification_batches")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
