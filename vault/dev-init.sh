#!/bin/sh
set -e

# [안전 장치] 스크립트 파일의 실제 위치를 기준으로 경로를 고정합니다.
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)

# 원본 변수들을 절대 경로로 변환하여 실수를 방지합니다.
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.v2.yml"
ENV_FILE="$PROJECT_ROOT/shared_config/.env"
VAULT_SETUP_SCRIPT="$PROJECT_ROOT/server2/vault/vault-manual-setup.sh"

echo_header() {
    echo "\n======================================================================"
    echo "=> $1"
    echo "======================================================================"
}

# 1. 환경 초기화 (경로 오류 방지를 위해 --env-file 추가)
echo_header "1. Cleaning up previous environment"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down -v

# 2. Vault 컨테이너 시작
echo_header "2. Starting Vault container"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d vault

echo "Waiting 5 seconds for Vault to be ready..."
sleep 5

# 3. 내부 설정 스크립트 실행 (절대 경로 사용으로 더 안전함)
echo_header "3. Configuring Vault (Internal Script)"
MSYS_NO_PATHCONV=1 docker exec -u 0 -i vault sh < "$VAULT_SETUP_SCRIPT"

# 4. [FORCE FIX] 권한 교정 (원본 로직 유지)
echo_header "4. [FORCE FIX] Enforcing correct permissions"
MSYS_NO_PATHCONV=1 docker exec -u 0 vault find /vault/file -type d -exec chmod 755 {} +
MSYS_NO_PATHCONV=1 docker exec -u 0 vault find /vault/file -type f -exec chmod 644 {} +
MSYS_NO_PATHCONV=1 docker exec -u 0 vault chown -R vault:vault /vault/file

# 5. AppRole 정보 가져오기 (ENV_FILE 경로가 정확하므로 안전함)
echo_header "5. Fetching AppRole credentials"
touch "$ENV_FILE"
sed -i '/^VAULT_TOKEN=/d' "$ENV_FILE"
sed -i '/^VAULT_APPROLE_ROLE_ID=/d' "$ENV_FILE"
sed -i '/^VAULT_APPROLE_SECRET_ID=/d' "$ENV_FILE"

ROOT_TOKEN=$(MSYS_NO_PATHCONV=1 docker exec vault jq -r .root_token /vault/file/keys.json)
ROLE_ID=$(MSYS_NO_PATHCONV=1 docker exec -e VAULT_TOKEN="$ROOT_TOKEN" vault sh -c "vault read -format=json auth/approle/role/app-role/role-id | jq -r .data.role_id")
SECRET_ID=$(MSYS_NO_PATHCONV=1 docker exec -e VAULT_TOKEN="$ROOT_TOKEN" vault sh -c "vault write -f -format=json auth/approle/role/app-role/secret-id | jq -r .data.secret_id")

echo "VAULT_APPROLE_ROLE_ID=$ROLE_ID" >> "$ENV_FILE"
echo "VAULT_APPROLE_SECRET_ID=$SECRET_ID" >> "$ENV_FILE"

echo_header "Initial Setup Complete!"
echo "Permissions have been forced to 755/644."
echo "You can now run: ./server2/vault/dev-start.sh"