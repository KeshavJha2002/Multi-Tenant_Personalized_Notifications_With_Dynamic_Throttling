#!/bin/bash
set -e

echo "Starting infrastructure services..."
docker-compose up -d zookeeper kafka-broker-1 postgres redis prometheus grafana loki node-exporter redis-exporter postgres-exporter

echo "Waiting for PostgreSQL..."
sleep 10

echo "Starting backend..."
docker rm -f backend-notif-system 2>/dev/null || true
docker run -d --name backend-notif-system \
    --network multi-tenant_personalized_notifications_with_dynamic_throttling_monitoring \
    -e DB_HOST=postgres \
    -e DB_PORT=5432 \
    -e DB_USER=postgres \
    -e DB_PASSWORD=postgres \
    -e DB_NAME=notification_system_users \
    -e KAFKA_BROKER=kafka-broker-1:9093 \
    -e LIKES_TOPIC=likes \
    -e COMMENTS_TOPIC=comments \
    -p 8000:8000 \
    multi-tenant_personalized_notifications_with_dynamic_throttling_backend:test

echo "All services started!"
docker ps --format "table {{.Names}}\t{{.Status}}"
