# APPROACH

This document details the approach taken to design, implement, and deploy a scalable, multi-tenant notification system. The system supports personalized notifications, dynamic throttling, priority handling, and robust error handling, ensuring high performance under load.

## Tools Used

### Kafka

- Kafka is known for it's high throughput.
- Here kafka is used both as a pub-sub model and as a message queue.

### PostgreSQL

- The dummy data of the users to simulate the subscribed tenants in stored in PostgreSQL. The following schema is used to store data

``js
- user_id: string
- in_app_notifications: boolean
- mail_notifications: boolean
- mail_like_notifications: boolean
- mail_comment_notifications: boolean
- mail_mention_notifications: boolean
- mail_connection_notifications: boolean
```

## Testing