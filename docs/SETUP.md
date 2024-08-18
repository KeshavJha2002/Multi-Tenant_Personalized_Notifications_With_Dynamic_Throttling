# Setup Guide

## Backend setup

```bash
  cd backend  # Assuming you are in the root directory
  python3 -m venv env
  source env/bin/activate
  pip3 install -r ./requirements.txt
```

## Docker setup

```bash
docker-compose up -d
```

## PostgreSQL setup

```sql
# Make sure that the PostgreSQL server is up and running
# Create a table following this schema
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    in_app_notifications BOOLEAN,
    mail_notifications BOOLEAN,
    mail_like_notifications BOOLEAN,
    mail_comment_notifications BOOLEAN,
    mail_mention_notifications BOOLEAN,
    mail_connection_notifications BOOLEAN
);
```

Copy the csv data into the table
```bash
\copy users from '<absolute-path-to-repo>\Multi-Tenant_Personalized_Notifications_With_Dynamic_Throttling\user_data_db_final_update.csv' DELIMITER ',' CSV HEADER;
```
