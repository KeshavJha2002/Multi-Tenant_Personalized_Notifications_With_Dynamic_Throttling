#!/bin/bash

docker-compose exec kafka-broker-1 kafka-topics.sh --create --topic like_topic --bootstrap-server localhost:9092 --partitions 2 --replication-factor 1
docker-compose exec kafka-broker-1 kafka-topics.sh --create --topic comment_topic --bootstrap-server localhost:9092 --partitions 2 --replication-factor 1
docker-compose exec kafka-broker-1 kafka-topics.sh --create --topic networking --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker-compose exec kafka-broker-1 kafka-topics.sh --create --topic mention --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker-compose exec kafka-broker-1 kafka-topics.sh --list --bootstrap-server localhost:9092