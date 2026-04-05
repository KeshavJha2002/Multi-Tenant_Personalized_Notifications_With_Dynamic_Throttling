# Notification System — High Level Design (HLD)

---

## 1. Overview

A simulated real-world notification pipeline that handles high-throughput user events (likes and comments on posts), decouples ingestion from persistence and notification dispatch, and delivers batched notifications to users. Actual notification delivery (push/email/SMS) is out of scope — the pipeline is built end-to-end up to the dispatch boundary.

---

## 2. Goals

- Simulate millions of concurrent users via a multi-threaded client
- Decouple API ingestion from DB writes using Kafka
- Ensure consumer idempotency under at-least-once delivery semantics
- Batch notifications intelligently using a logarithmic sliding window strategy
- Lay the groundwork for a pluggable notification dispatcher

---

## 3. Non-Goals

- Actual notification delivery (push, email, SMS)
- Authentication / Authorization
- Horizontal scaling of Kafka brokers beyond 1 replica

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Multi-Threaded Client              │
│         (simulates millions of concurrent users)    │
└────────────────┬────────────────┬───────────────────┘
                 │                │
         POST /like         POST /comment
                 │                │
                 ▼                ▼
┌────────────────────────────────────────────────────┐
│                    API Layer                       │
│         (produces events to Kafka topics)          │
└────────────┬───────────────────────┬───────────────┘
             │                       │
             ▼                       ▼
    ┌─────────────────┐    ┌──────────────────┐
    │  Kafka Topic:   │    │  Kafka Topic:    │
    │     likes       │    │    comments      │
    │ (1 replica,     │    │ (1 replica,      │
    │  master+backup) │    │  master+backup)  │
    └────────┬────────┘    └────────┬─────────┘
             │                      │
             └──────────┬───────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │      Kafka Consumers    │
          └────────────┬────────────┘
                       │
           ┌───────────┴────────────┐
           │                        │
           ▼                        ▼
    ┌──────────────┐      ┌──────────────────────┐
    │  DB Writer   │      │    Batching Layer     │
    │              │      │  wait = max(log2(n),  │
    │  Idempotent  │      │  2) seconds           │
    │  writes only │      │  Sliding window,      │
    └──────────────┘      │  reset on new event   │
                          │  n = COUNT from DB    │
                          └──────────┬────────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │  Notification         │
                          │  Dispatcher           │
                          │  (pipeline boundary — │
                          │  no actual dispatch)  │
                          └──────────────────────┘
```

---

## 5. Component Breakdown

### 5.1 Multi-Threaded Client

- Spawns N threads to simulate concurrent users
- Each thread fires POST `/like` or POST `/comment` requests at a configurable rate
- Designed to stress-test the pipeline at scale

### 5.2 API Layer

- Exposes two endpoints:
  - `POST /like` — user likes a post
  - `POST /comment` — user comments on a post
- Each request:
  - Generates a unique `event_id` (UUID)
  - Produces a message to the corresponding Kafka topic
  - Returns immediately (fire-and-forget to DB)
- Does **not** write directly to the database

### 5.3 Kafka

| Property        | Value                          |
|-----------------|--------------------------------|
| Topics          | `likes`, `comments`            |
| Replication     | 1 replica (master + backup)    |
| Delivery        | At-least-once                  |
| Consumer Groups | One per topic                  |

### 5.4 Kafka Consumers

- Consume messages from `likes` and `comments` topics
- Responsibilities:
  1. Idempotent DB write
  2. Trigger batching layer

### 5.5 DB Writer (Idempotency)

Two strategies, one per event type:

| Event Type | Idempotency Strategy |
|------------|----------------------|
| Like       | `UNIQUE(user_id, post_id)` constraint at DB level. Duplicate insert → DB rejects → consumer treats as no-op. |
| Comment    | `event_id` (UUID) checked against `processed_events` table before write. Already exists → skip. |

### 5.6 Batching Layer

Triggered after every DB write. Governs how notifications are grouped before dispatch.

**Algorithm:**

```
On (n+1)th event for a given post:
  → read total_count from DB          # single COUNT query
  → wait = max(log2(total_count), 2)  # minimum 2 seconds
  → start timer: wait seconds

  → if new event arrives before timer fires:
      → read total_count from DB again
      → reset timer: max(log2(total_count), 2) seconds

  → if timer fires:
      → dispatch batch of all events accumulated in this window
      → clear window
```

**Timer Behaviour:** Sliding window — any new event within the wait period resets the timer with a freshly computed `log2(n)`.

**Wait time examples:**

| Total Likes (n) | Wait (seconds) |
|-----------------|----------------|
| < 2             | 2.0 (floor)    |
| 4               | 2.0            |
| 8               | 3.0            |
| 16              | 4.0            |
| 32              | 5.0            |
| 1024            | 10.0           |

> Same batching strategy applies to both `likes` and `comments`.

### 5.7 Notification Dispatcher

- Receives a batch from the batching layer
- Logs / records the batch (simulated dispatch)
- Does **not** deliver actual notifications
- Acts as the terminal stage of the pipeline

---

## 6. Data Flow Summary

```
Client Thread
  → POST /like {user_id, post_id, event_id}
  → Kafka: likes topic
  → Consumer: idempotent DB write (UNIQUE constraint)
  → Batching Layer: sliding window timer (max(log2(n), 2)s)
  → Timer fires → Notification Dispatcher (batch logged)

Client Thread
  → POST /comment {user_id, post_id, content, event_id}
  → Kafka: comments topic
  → Consumer: check processed_events → DB write
  → Batching Layer: sliding window timer (max(log2(n), 2)s)
  → Timer fires → Notification Dispatcher (batch logged)
```

---

## 7. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API → DB coupling | Decoupled via Kafka | DB cannot keep up with API hit rate at scale |
| Kafka delivery | At-least-once | Default Kafka behaviour; idempotency handled downstream |
| Like idempotency | DB UNIQUE constraint | Likes are naturally idempotent (one like per user per post) |
| Comment idempotency | event_id deduplication | Comments are not naturally unique; UUID check prevents duplicates |
| Batch wait time | max(log2(n), 2) seconds | Logarithmic backoff — high-traffic posts batch more aggressively |
| Window strategy | Sliding (reset on new event) | Ensures no notification fires mid-burst |
| n source | DB COUNT query | Globally accurate; not session-scoped |
| Kafka replication | 1 replica (master + backup) | Fault tolerance without operational overhead for simulation |

---

## 8. Out of Scope

- Actual push / email / SMS delivery
- User preference management (opt-in/opt-out)
- Read receipts
- Multi-datacenter replication
- Authentication

---
