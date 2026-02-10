#!/bin/sh
set -e
export MSYS_NO_PATHCONV=1

# 1. 경로 설정 (스크립트 위치 기준 절대 경로)
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)

cd "$PROJECT_ROOT"

COMPOSE_FILE="./docker-compose.v2.yml"
ENV_FILE="./shared_config/.env"

echo "======================================================================"
echo "=> 1. Cleaning up previous environment"
echo "======================================================================"
if [ ! -f "$ENV_FILE" ]; then
    echo "[ERROR] .env file not found at $ENV_FILE"
    exit 1
fi
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down -v

echo "======================================================================"
echo "=> 2. Starting Vault and Internal Setup"
echo "======================================================================"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d vault
sleep 5

# 내부 설정 스크립트 실행 (1번 파일 호출)
docker exec -i vault sh < "$PROJECT_ROOT/server2/vault/vault-manual-setup.sh"

echo "======================================================================"
echo "=> 3. Generating and Injecting AppRole Credentials"
echo "======================================================================"
# Root Token 추출
ROOT_TOKEN=$(docker exec vault sh -c "jq -r .root_token /vault/file/keys.json")

# 사원증(Role ID / Secret ID) 발급
ROLE_ID=$(docker exec -e VAULT_TOKEN="$ROOT_TOKEN" vault sh -c "vault read -format=json auth/approle/role/app-role/role-id | jq -r .data.role_id")
SECRET_ID=$(docker exec -e VAULT_TOKEN="$ROOT_TOKEN" vault sh -c "vault write -f -format=json auth/approle/role/app-role/secret-id | jq -r .data.secret_id")

# .env 파일 업데이트 (기존 값 삭제 후 삽입)
sed -i '/VAULT_APPROLE/d' "$ENV_FILE"
echo "VAULT_APPROLE_ROLE_ID=$ROLE_ID" >> "$ENV_FILE"
echo "VAULT_APPROLE_SECRET_ID=$SECRET_ID" >> "$ENV_FILE"

# 배달부(Agent)가 읽을 수 있도록 볼륨 안에 파일로 주입
docker exec vault sh -c "echo $ROLE_ID > /vault/file/role_id"
docker exec vault sh -c "echo $SECRET_ID > /vault/file/secret_id"

# 권한 교정 (배달부가 읽을 수 있게)
docker exec -u 0 vault chown -R vault:vault /vault/file

echo "\n[SUCCESS] Setup Complete! All credentials injected."
echo "Now run: ./server2/vault/dev-start.sh"