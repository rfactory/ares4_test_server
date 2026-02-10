#!/bin/sh
# Ares4: 재부팅 후 금고 자동 잠금 해제 스크립트
set -e
# 윈도우 경로 변환 방지 전역 설정
export MSYS_NO_PATHCONV=1

COMPOSE_FILE="docker-compose.v2.yml"

echo "======================================================================"
echo "=> [RECOVERY] System Reboot Detected. Unsealing Vault..."
echo "======================================================================"

# 1. Vault 컨테이너만 먼저 가동
docker-compose -f "$COMPOSE_FILE" up -d vault
echo "Waiting 5 seconds for Vault process to initialize..."
sleep 5

# 2. 저장된 열쇠(keys.json)에서 키를 추출 (도커 내부 jq 사용으로 로컬 종속성 제거)
echo "Extracting unseal keys..."
K1=$(docker exec vault jq -r .unseal_keys_b64[0] /vault/file/keys.json)
K2=$(docker exec vault jq -r .unseal_keys_b64[1] /vault/file/keys.json)
K3=$(docker exec vault jq -r .unseal_keys_b64[2] /vault/file/keys.json)

# 3. 인자로 키를 전달하여 잠금 해제 (터미널 입력 대기 에러 방지)
docker exec vault vault operator unseal "$K1" > /dev/null
docker exec vault vault operator unseal "$K2" > /dev/null
docker exec vault vault operator unseal "$K3" > /dev/null

echo "=> Vault is UNSEALED."

# 4. 도커 헬스체크가 'healthy'가 될 때까지 대기
echo "Waiting for Docker Healthcheck to pass..."
while [ "$(docker inspect --format='{{.State.Health.Status}}' vault)" != "healthy" ]; do
    echo "Status: $(docker inspect --format='{{.State.Health.Status}}' vault)... waiting 2s"
    sleep 2
done

echo "=> Vault is HEALTHY. Waking up all services..."

# Agent가 발급한 토큰은 agent-config.hcl 설정에 따라 /vault/file/token.txt에 저장됩니다.
echo "=> Syncing fresh token for Server2..."
NEW_TOKEN=$(docker exec vault cat /vault/file/token.txt)
sed -i "/VAULT_TOKEN/d" ./shared_config/.env
echo "VAULT_TOKEN=$NEW_TOKEN" >> ./shared_config/.env

# 5. 모든 서비스 정상 가동 (dev-start.sh 호출)
./server2/vault/dev-start.sh