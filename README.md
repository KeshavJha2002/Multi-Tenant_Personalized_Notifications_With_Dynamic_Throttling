# Multi-Tenant Notification System with Dynamic Throttling

A high-throughput notification pipeline that handles likes and comments on posts, decouples ingestion from persistence using Kafka, and delivers batched notifications using a logarithmic sliding window strategy.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Multi-Threaded Client                    │
│                  (load test / stress test)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
            POST /like        POST /comment
                     │                │
                     ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                         API Layer                           │
│                  (FastAPI + uvicorn)                        │
│                   Kafka Producers                           │
└────────────────────┬────────────────────────────────────────┘
                     │
           Kafka Topic: likes     Kafka Topic: comments
                     │                │
                     ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                      Consumers                              │
│              (idempotent DB writes)                         │
│           Like Consumer    │    Comment Consumer            │
└────────────────────┬──────┴─────────────────────────────────┘
                     │
           ┌────────▼────────┐
           │  Batching Layer │  ← max(log2(n), 2) sliding window
           └────────┬─────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Notification        │
         │  Dispatcher          │
         │  (logging only)      │
         └──────────────────────┘
```

---

## Components

| Component | Description |
|-----------|-------------|
| `backend/main.py` | FastAPI app with `POST /like` and `POST /comment` endpoints |
| `backend/producers/producer.py` | Kafka producers for likes and comments topics |
| `backend/consumers/consumer_like.py` | Kafka consumer for likes with idempotent DB writes |
| `backend/consumers/consumer_comment.py` | Kafka consumer for comments with event_id dedup |
| `backend/batching.py` | Sliding window batching layer: `wait = max(log2(n), 2)` seconds |
| `backend/dispatcher.py` | Notification dispatcher (logs batch to stdout) |
| `backend/db.py` | PostgreSQL connection using psycopg2 |
| `backend/db_queries.py` | DB queries for likes, comments, event dedup |
| `backend/init_db.py` | Database schema initialization |
| `tests/load_test_client.py` | Multi-threaded load test client |
| `docker-compose.yml` | All infrastructure services |

---

## Prerequisites

- Docker and Docker Compose
- At least 4GB RAM available

---

## Quick Start

### 1. Start Infrastructure

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5431)
- Kafka (port 9092)
- Zookeeper (port 2181)
- Redis (port 6379)
- Prometheus (port 9090)
- Grafana (port 3001)
- Loki (port 3100)
- Various exporters

### 2. Build and Start Backend

```bash
docker build -t notification-backend:latest -f Dockerfile .
docker run -d --name backend-notif-system \
  --network multi-tenant_personalized_notifications_with_dynamic_throttling_monitoring \
  -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=postgres \
  -e DB_PASSWORD=postgres -e DB_NAME=notification_system_users \
  -e KAFKA_BROKER=kafka-broker-1:9093 \
  -p 8000:8000 \
  notification-backend:latest
```

Or use the convenience script (1+2):

```bash
./start.sh
```

### 3. Verify Services

```bash
# API Health
curl http://localhost:8000/health

# List containers
docker ps
```

---

## Running the System

### API Endpoints

```bash
# Send a like
curl -X POST http://localhost:8000/like \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "post_id": 1}'

# Send a comment
curl -X POST http://localhost:8000/comment \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "post_id": 1, "content": "Hello world!"}'

# Health check
curl http://localhost:8000/health

# Metrics (Prometheus)
curl http://localhost:8000/metrics
```

### Consumers (Kafka → Database)

The backend container starts consumers automatically. To run manually:

```bash
docker exec -it backend-notif-system python backend/consumers/consumer_like.py
docker exec -it backend-notif-system python backend/consumers/consumer_comment.py
```

### Load Testing

From inside the container:

```bash
docker exec backend-notif-system python tests/load_test_client.py -t 10 -n 100
```

Or from the host:

```bash
python tests/load_test_client.py -t 10 -n 100 --api-url http://localhost:8000
```

**Load Test Options:**

| Flag | Description | Default |
|------|-------------|---------|
| `-t` | Number of threads | 10 |
| `-n` | Requests per thread | 100 |
| `-r` | Requests per second per thread | unlimited |
| `-l` | Like ratio (0-1) | 0.7 |
| `-u` | User range (min,max) | 1,10000 |
| `-p` | Post range (min,max) | 1,1000 |

**Example Run:**

```bash
docker exec backend-notif-system python tests/load_test_client.py -t 10 -n 10000
```

**Output:**

```
Starting load test: threads=10, requests_per_thread=10000, rps=0, like_ratio=0.7
User range: (1, 10000), Post range: (1, 1000)
API: http://localhost:8000
------------------------------------------------------------
------------------------------------------------------------
Load test complete
Elapsed time: 319.13s
Throughput: 313.35 req/s

Results:
  Total requests:  100000
  Success:         100000
  Failures:        0
  Success rate:    100.0%
  Avg latency:     29.74ms
  P50 latency:     27.42ms
  P95 latency:     45.08ms
```

**Performance Notes:**
- 313 req/s throughput with single Kafka broker
- 100% success rate under load
- P95 latency under 50ms

---

## Configuration

Environment variables for the backend:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | postgres | PostgreSQL host |
| `DB_PORT` | 5432 | PostgreSQL port |
| `DB_USER` | postgres | PostgreSQL user |
| `DB_PASSWORD` | postgres | PostgreSQL password |
| `DB_NAME` | notification_system_users | Database name |
| `KAFKA_BROKER` | kafka-broker-1:9093 | Kafka broker address |
| `LIKES_TOPIC` | likes | Kafka topic for likes |
| `COMMENTS_TOPIC` | comments | Kafka topic for comments |

---

## Database Schema

Created automatically on startup:

| Table | Description |
|-------|-------------|
| `likes` | Stores likes with `UNIQUE(user_id, post_id)` for idempotency |
| `comments` | Stores comments with unique event_id |
| `processed_events` | Tracks processed event_ids for comment dedup |
| `notification_batches` | Audit log for dispatched batches |

---

## Monitoring

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API Health | http://localhost:8000/health |
| API Metrics | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 (admin/admin) |
| Loki (logs) | http://localhost:3100 |

### Grafana Setup

1. Go to `http://localhost:3001` (login: admin/admin)
2. **Configuration** → **Data Sources** → **Add data source**
3. Select **Prometheus**
4. URL: `http://prometheus-notif-system:9090`
5. Save

Now create dashboards using PromQL queries like:
- `api_requests_total` - total requests
- `api_request_latency_seconds_bucket` - latency histogram

---

## Key Design Decisions

### Idempotency

- **Likes**: Handled by `UNIQUE(user_id, post_id)` constraint in PostgreSQL
- **Comments**: Handled by checking `processed_events` table before insert

### Batching Algorithm

Sliding window: `wait_time = max(log2(total_count), 2)` seconds

- On each new event, compute total count for that post
- Calculate wait time using log2
- Reset timer on new events (debouncing)
- Dispatch batch when timer fires

### At-Least-Once Delivery

- Kafka consumers manually commit offsets only after successful DB write
- On failure, message is not committed and will be redelivered

---

## Stopping the System

```bash
# Stop backend
docker stop backend-notif-system

# Stop all services
docker-compose down

# Remove volumes (data will be lost)
docker-compose down -v
```

---

## Troubleshooting

### Backend won't start

Check logs:
```bash
docker logs backend-notif-system
```

### Kafka not connecting

Ensure Kafka is healthy:
```bash
docker exec kafka-broker-1 kafka-topics.sh --list --bootstrap-server localhost:9092
```

### Database connection issues

Test connection:
```bash
docker exec backend-notif-system bash -c "PGPASSWORD=postgres psql -h postgres -U postgres -d notification_system_users -c 'SELECT 1'"
```

### Rebuild after changes

```bash
docker build --no-cache -t notification-backend:latest -f Dockerfile .
docker rm -f backend-notif-system
docker run -d --name backend-notif-system \
  --network multi-tenant_personalized_notifications_with_dynamic_throttling_monitoring \
  -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=postgres \
  -e DB_PASSWORD=postgres -e DB_NAME=notification_system_users \
  -e KAFKA_BROKER=kafka-broker-1:9093 \
  -p 8000:8000 \
  notification-backend:latest
```

---

## File Structure

```
.
├── Dockerfile                    # Backend container
├── docker-compose.yml            # All services
├── HLD.md                        # High-level design
├── ROADMAP.md                    # Implementation roadmap
├── README.md                     # This file
├── start.sh                      # Convenience startup script
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── models.py                # Pydantic models
│   ├── db.py                    # DB connection
│   ├── db_queries.py            # DB operations
│   ├── init_db.py               # Schema init
│   ├── batching.py               # Sliding window batching
│   ├── dispatcher.py             # Notification dispatcher
│   ├── start.sh                 # Container entrypoint
│   ├── requirements.txt         # Python dependencies
│   ├── producers/
│   │   ├── __init__.py
│   │   └── producer.py          # Kafka producers
│   └── consumers/
│       ├── __init__.py
│       ├── base.py              # Base consumer class
│       ├── consumer_like.py     # Likes consumer
│       └── consumer_comment.py  # Comments consumer
├── tests/
│   └── load_test_client.py      # Load testing tool
├── prometheus/
│   └── config.yml               # Prometheus config
└── loki/
    └── loki-config.yml          # Loki config
```
