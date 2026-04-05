#!/bin/bash
set -e

cd /app/backend

export PYTHONPATH=/app/backend:$PYTHONPATH

echo "Waiting for PostgreSQL..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - initializing schema..."
python init_db.py

echo "Starting uvicorn API server in background..."
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 &

sleep 3

echo "Starting Kafka consumers in background..."
nohup python consumers/consumer_like.py > /tmp/like.log 2>&1 &
nohup python consumers/consumer_comment.py > /tmp/comment.log 2>&1 &

sleep 2

echo "All services started!"
echo "API: http://localhost:8000"

tail -f /dev/null
