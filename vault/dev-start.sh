#!/bin/sh
# This script starts all services for the development environment.
# It should be run after dev-init.sh has been executed at least once.

set -e

COMPOSE_FILE="docker-compose.v2.yml"

echo "Starting all services..."
docker-compose -f "$COMPOSE_FILE" up -d --build

echo "All services are starting in the background."
echo "You can monitor the logs with the following command: docker-compose -f $COMPOSE_FILE logs -f"
