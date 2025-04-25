#!/bin/bash
set -e

echo "Waiting for services to be ready..."
sleep 10  

echo "Initializing database..."
python scripts/init_db.py

echo "Creating Kafka topics..."
python scripts/create_kafka_topics.py

echo "Initialization complete!"

if [ "$1" = "keep-alive" ]; then
  echo "Keeping container alive..."
  tail -f /dev/null
fi