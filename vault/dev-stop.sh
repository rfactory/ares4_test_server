# C:\vscode project files\Ares4\server2\vault\dev-stop.sh

#!/bin/sh
set -e

COMPOSE_FILE="docker-compose.v2.yml"

echo "======================================================================"
echo "=> Stopping heavy services (Keeping Vault & Agent alive)"
echo "======================================================================"

# [핵심] 정지할 서비스들만 나열합니다. vault와 vault-agent는 목록에서 제외합니다.
docker-compose -f "$COMPOSE_FILE" stop \
    fastapi_app2 \
    ares4-worker \
    ares4-postgres-v2 \
    some-redis-v2 \
    mqtt-listener \
    device-health-checker \
    emqx \
    panel_react

echo "Heavy services have been stopped. Vault Agent is still running in background."