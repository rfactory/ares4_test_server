#!/bin/sh
# This script starts all services for the development environment.
# It ensures permissions are enforced every time services are started.

set -e

COMPOSE_FILE="docker-compose.v2.yml"

echo "Starting all services..."
# --build 옵션 때문에 컨테이너가 재생성되면서 권한이 리셋될 수 있습니다.
docker-compose --env-file ./shared_config/.env -f "$COMPOSE_FILE" up -d --build

# ------------------------------------------------------------------
# [추가된 부분] 컨테이너가 켜지자마자 "스마트 권한 설정"을 다시 적용합니다.
# ------------------------------------------------------------------
echo "Ensuring Smart Permissions (Dirs: 755, Files: 644)..."

# 컨테이너가 뜰 때까지 잠깐 대기
sleep 2

# 1. 일단 다 755로 열어서 탐색 가능하게 만듦 (필수!)
MSYS_NO_PATHCONV=1 docker exec -u 0 vault chmod -R 755 //vault/file

# 2. 파일만 골라서 644로 다시 잠금 (보안 강화)
MSYS_NO_PATHCONV=1 docker exec -u 0 vault find //vault/file -type f -exec chmod 644 {} +

# 3. 소유권 도장 찍기
MSYS_NO_PATHCONV=1 docker exec -u 0 vault chown -R vault:vault //vault/file

echo "Permissions verified."
# ------------------------------------------------------------------

echo "All services are starting in the background."
echo "You can monitor the logs with the following command: docker-compose -f $COMPOSE_FILE logs -f"