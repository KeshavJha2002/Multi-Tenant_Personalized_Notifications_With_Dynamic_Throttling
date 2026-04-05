#!/bin/bash

docker-compose exec kafka-broker-1 kafka-topics.sh --create --topic likes --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker-compose exec kafka-broker-1 kafka-topics.sh --create --topic comments --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker-compose exec kafka-broker-1 kafka-topics.sh --list --bootstrap-server localhost:9092
