#!/bin/sh
# 이 스크립트는 개발 환경의 모든 서비스를 시작합니다.
set -e

# 1. [경로 고정] 스크립트 위치를 기준으로 프로젝트 루트(Ares4)로 이동합니다.
# 이렇게 하면 윈도우/리눅스 경로 변환 문제를 완벽하게 피할 수 있습니다.
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR/../.."

# 2. [파일 경로] 이제 모든 경로는 현재 폴더(루트) 기준입니다.
COMPOSE_FILE="docker-compose.v2.yml"
ENV_FILE="shared_config/.env"

echo "Current Working Directory: $(pwd)"
echo "Loading variables from: $ENV_FILE"

# 3. [환경 변수 로드] .env 파일을 읽어서 현재 쉘에 주입합니다.
if [ -f "$ENV_FILE" ]; then
    # export를 통해 docker-compose가 변수들을 즉시 인식하게 합니다.
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "ERROR: .env file not found at $ENV_FILE"
    exit 1
fi

# 4. [윈도우 경로 변환 방지] Git Bash 환경 필수 설정
export MSYS_NO_PATHCONV=1

echo "\n======================================================================"
echo "=> Starting all services"
echo "======================================================================"

# 5. [실행] 이제 상대 경로를 사용하여 에러를 방지합니다.
docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build

# ------------------------------------------------------------------
# [권한 복구 로직] 원본 그대로 유지
# ------------------------------------------------------------------
echo "\nEnsuring Smart Permissions (Dirs: 755, Files: 644)..."
sleep 2

docker exec -u 0 vault chmod -R 755 //vault/file
docker exec -u 0 vault find //vault/file -type f -exec chmod 644 {} +
docker exec -u 0 vault chown -R vault:vault //vault/file

echo "Permissions verified."
echo "Monitor logs: docker-compose --env-file $ENV_FILE -f $COMPOSE_FILE logs -f"