#!/bin/sh
set -e
# set -x # 디버깅 필요 시 주석 해제

COMPOSE_FILE="docker-compose.v2.yml"
ENV_FILE="./shared_config/.env"

echo_header() {
    echo "\n======================================================================"
    echo "=> $1"
    echo "======================================================================"
}

# 1. 환경 초기화
echo_header "1. Cleaning up previous environment"
# 볼륨까지 확실하게 날립니다.
docker-compose -f "$COMPOSE_FILE" down -v

# 2. Vault 컨테이너 시작
echo_header "2. Starting Vault container"
docker-compose -f "$COMPOSE_FILE" up -d vault

echo "Waiting 5 seconds for Vault to be ready..."
sleep 5

# 3. 내부 설정 스크립트 실행 (오류 확인을 위해 /dev/null 제거함)
echo_header "3. Configuring Vault (Internal Script)"
# 여기서 오류가 나더라도 스크립트가 멈추지 않도록 '|| true'를 붙이거나,
# set -e가 있으므로 오류 발생 시 바로 확인 가능하게 합니다.
MSYS_NO_PATHCONV=1 docker exec -u 0 -i vault sh < ./server2/vault/vault-manual-setup.sh

# ------------------------------------------------------------------
# [핵심] 여기서부터가 "강제 교정(Safety Net)" 로직입니다.
# 내부 스크립트가 권한을 망쳐놨더라도, 여기서 다시 복구합니다.
# ------------------------------------------------------------------
echo_header "4. [FORCE FIX] Enforcing correct permissions"

echo "Fixing directory permissions to 755 (rwxr-xr-x)..."
MSYS_NO_PATHCONV=1 docker exec -u 0 vault find /vault/file -type d -exec chmod 755 {} +

echo "Fixing file permissions to 644 (rw-r--r--)..."
MSYS_NO_PATHCONV=1 docker exec -u 0 vault find /vault/file -type f -exec chmod 644 {} +

echo "Fixing ownership to vault:vault..."
MSYS_NO_PATHCONV=1 docker exec -u 0 vault chown -R vault:vault /vault/file
# ------------------------------------------------------------------

# 5. AppRole 정보 가져오기
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
echo "You can now run: ./server2/dev-start.sh"