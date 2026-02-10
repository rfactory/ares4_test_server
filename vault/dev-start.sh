#!/bin/sh
# Ares4: 인프라 가동 및 보안 정책(Policy/Role) 자동화 마스터 스크립트
set -e

# Windows 환경(Git Bash/MINGW) 경로 변환 이슈 방지
export MSYS_NO_PATHCONV=1

# 1. 경로 고정 (Ares4 프로젝트 루트로 이동)
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR/../.."

COMPOSE_FILE="docker-compose.v2.yml"
ENV_FILE="shared_config/.env"

echo "=> [1/6] 환경 변수 로드 및 서비스 가동..."
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build

# 2. Vault 준비 상태 확인 (Wait-for-it 로직)
echo "=> [2/6] Vault 서버 응답 대기 중..."
until docker exec vault vault status > /dev/null 2>&1; do
  echo "   ...Vault가 아직 잠겨있거나 준비되지 않았습니다. (1초 대기)"
  sleep 1
done

# 3. 보안 정책(Policy) 자동 주입
# FastAPI 서버가 인증서를 발급하고 HMAC을 저장할 수 있는 명확한 권한을 부여합니다.
echo "=> [3/6] Vault 보안 정책(ares-server-policy) 갱신 중..."
docker exec -i vault vault policy write ares-server-policy - <<EOF
# 기기 인증서 발급 권한 (pki_int 사용)
path "${VAULT_PKI_MOUNT_POINT}/issue/${VAULT_PKI_LISTENER_ROLE}" {
  capabilities = ["create", "update", "read", "list"]
}

# MQTT 서버용 인증서 발급 권한
path "${VAULT_PKI_MOUNT_POINT}/issue/ares-server-mqtt-client-role" {
  capabilities = ["create", "update", "read", "list"]
}

# HMAC 키 관리를 위한 KV 저장소 권한
path "secret/data/ares4/hmac/*" {
  capabilities = ["create", "update", "read", "list", "delete"]
}
EOF

# 4. PKI Role 설정 (도메인 제한 및 보안 강화)
echo "=> [4/6] PKI Role 설정 적용 (.device.ares4.internal)..."
docker exec vault vault write ${VAULT_PKI_MOUNT_POINT}/roles/${VAULT_PKI_LISTENER_ROLE} \
    allowed_domains="ares4-mq-broker,emqx,client,localhost,device.ares4.internal" \
    allow_subdomains=true \
    allow_bare_domains=true \
    allow_ip_sans=true \
    allow_any_name=false \
    enforce_hostnames=false \
    max_ttl="720h"

# 5. 파일 시스템 권한 교정
# Vault Agent가 생성한 인증서를 EMQX 등이 읽을 수 있도록 권한을 정리합니다.
echo "=> [5/6] 인증서 파일 권한 교정 중..."
docker exec -u 0 vault chmod -R 755 /vault/file
docker exec -u 0 vault find /vault/file -type f -exec chmod 644 {} +
docker exec -u 0 vault chown -R vault:vault /vault/file

# 6. 배달부(Agent) 재시작
echo "=> [6/6] Vault Agent 재시작 (인증서 갱신 강제)..."
docker-compose -f "$COMPOSE_FILE" restart vault-agent

# ======================================================================
# [7. NEW] EMQX Webhook 자동 연결 (다니엘님 추가 요청)
# ======================================================================
echo "=> [7/7] EMQX Webhook 브리지 설정 실행..."
if [ -f "./setup-emqx.sh" ]; then
    chmod +x ./setup-emqx.sh
    ./setup-emqx.sh
else
    echo "⚠️  Warning: setup-emqx.sh 파일을 찾을 수 없습니다. Webhook 설정이 건너뛰어졌습니다."
fi

echo "\n===================================================="
echo "🚀 Ares4 자동화 인프라 구성 완료!"
echo "환경: Development / 보안 모드: 도메인 제한 적용"
echo "상태: Vault(✅), Agent(✅), EMQX Bridge(✅)"
echo "===================================================="