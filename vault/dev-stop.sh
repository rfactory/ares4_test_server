#!/bin/sh
# This script stops all services for the development environment without removing volumes.

set -e

COMPOSE_FILE="docker-compose.v2.yml"

echo "Stopping all services..."
docker-compose -f "$COMPOSE_FILE" down

echo "All services have been stopped."
