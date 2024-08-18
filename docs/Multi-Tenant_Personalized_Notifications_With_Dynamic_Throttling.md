# Notification System Design

## Requirements

Simulating the notification system of a social media platform.

### Notification Types

- **Like/Comment** on a Post/Comment (Reply is a type of comment)
  - Ensure no duplicates
- **Sending a Friend Request**: Notify the receiver of the request
- **Accepting a Friend Request**: Notify the sender
- **@mention** in Post/Comment
- **Wants to be Notified**: For a particular user's posts

### Features

#### In-App Notifications
- **Switch**: ON/OFF
- **Bundling**: All notifications of the same type within 5 minutes will be bundled
- **Notification Preferences**: 
  - Switch to enable or disable each type of notification

#### Mail Notifications
- **Switch**: ON/OFF
- **Bundling**: All notifications of the same type within 60 minutes will be bundled
- **Notification Preferences**:
  - Switch to enable or disable each type of notification

## Components

### Producers

**Features:**
- Modify data received according to the format
- Separation of concern for each producer
- Push objects into Kafka

### Kafka

**Features:**
- **Format**: JSON
- **Schema**: Defined as per requirements

### Consumers

**Features:**
- Perform database queries to check notification preferences
- Bundle notifications if necessary
- Discard notifications if necessary
- Retries if necessary
- Format notifications if necessary
- Push to the queue
- Set priority according to preferences

## Exposed Producers

### `like_on_post_or_comment()`

**Parameter Sample:**

```json
{
  "action_type": "LIKE",
  "action_on": "POST||COMMENT",
  "action_on_id": "POST_ID||COMMENT_ID",
  "action_by": "USER_ID",
  "action_to": "USER_ID",
  "action_at": "timestamp"
}
```

### `comment_on_post_or_comment()`

**Parameter Sample:**

```json
{
  "type": "COMMENT",
  "action_data": "",
  "action_on": "POST||COMMENT",
  "action_on_id": "POST_ID||COMMENT_ID",
  "action_by": "USER_ID",
  "action_to": "USER_ID",
  "action_at": "timestamp"
}
```

### `received_friend_request()`

**Parameter Sample:**

```json
{
  "type": "FRIEND_REQ",
  "action_by": "USER_ID",
  "action_on": "USER_ID",
  "action_at": "timestamp"
}
```

### `friend_request_accepted()`

**Parameter Sample:**

```json
{
  "action_type": "FRIEND_REQ_ACK",
  "action_by": "USER_ID",
  "action_on": "USER_ID",
  "action_at": "timestamp"
}
```

### `mentioned()`

**Parameter Sample:**

```json
{
  "action_type": "MENTION",
  "action_on": "POST||COMMENT||CONVERSATION",
  "action_on_id": "POST_ID||COMMENT_ID||CONVERSATION_ID",
  "action_by": "USER_ID",
  "action_to": "USER_ID",
  "action_at": "timestamp"
}
```

## Kafka Topics

Geographic partitioning will be used, but not for this simulation

> Manual Partition Assignment
- LIKE 2 partitions: Based on `action_on` (POST/COMMENT)
- COMMENT 2 partitions: Based on `action_on` (POST/COMMENT)
- MENTION 3 partitions: Based on `action_on` (POST/COMMENT/CONVERSATIONS)
- NETWORKING 2 partitions: Based on `action_type`

## Kafka Consumers

- Consumer_Group_SUB_LIKE: 2 consumers
- Consumer_Group_SUB_COMMENTS: 2 consumers
- Consumer_Group_SUB_MENTION: 3 consumers
- Consumer_Group_SUB_NETWORKING: 2 consumers

## Middleware Utilities

- database calls to ensure whether the notification will be sent or not
- @mention and @connection will not be bundled
[dynamic] :: after 1st action, wait(15m/40s) -> 2nd action(12m/30s) -> 3rd action(8m/25s) and so on
	[same target user_id]
- sms: like/comments will be bundled: 15mins wait time
- in-app: like/comments will be bundled: 40s wait time
- Bundle format:
  ```json
  {
	count: number, 
	action_by_user_id: string|string[],
	comment_id: string|string[]|null,
	post_id: string|string[]|null,
}```

In case of multiple hits, say (comment_id => [] &&  action_by_user_id=> []) then pick the one with the max size.

## Priority Message Queues

- LIKE: 1 retry
- COMMENT: 1 retry
- MENTION: high_priority : 2 retries
- NETWORKING: 1 retry
- DLQ: #####################

## User Schema

- user_id: string
- in_app_notifications: boolean
- mail_notifications: boolean
- mail_like_notifications: boolean
- mail_comment_notifications: boolean
- mail_mention_notifications: boolean
- mail_connection_notifications: boolean

## Schema Registry


## Monitoring and Logging Targets

- end-to-end latency
- Kafka processing latency
- Database query latency
- Notifications processed per sec
- Rate of processing, retires, and dead letter queues
- Cpu usage
- Consumer lag
- Bundling rate
