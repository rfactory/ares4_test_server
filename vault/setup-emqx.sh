#!/bin/sh
# Ares4: EMQX Webhook 자동 연결 스크립트
set -e

# 1. 환경 변수 파일 위치 설정
ENV_FILE="./shared_config/.env"

echo "======================================================================"
echo "=> [EMQX] Configuring Webhook Bridge automatically..."
echo "======================================================================"

# 2. .env 파일 존재 확인 및 시크릿 키 추출
if [ -f "$ENV_FILE" ]; then
    # .env에서 EMQX_WEBHOOK_SECRET 값만 grep으로 뽑아냅니다.
    SECRET_KEY=$(grep "^EMQX_WEBHOOK_SECRET=" "$ENV_FILE" | cut -d '=' -f2 | tr -d '\r' | tr -d '"' | tr -d "'")
else
    echo "❌ Error: $ENV_FILE not found!"
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo "❌ Error: EMQX_WEBHOOK_SECRET is missing in .env file."
    exit 1
fi

# 3. EMQX 가동 대기
echo "   Waiting for EMQX API..."
until curl -s -u "admin:public" "http://localhost:18083/api/v5/status" > /dev/null; do
    echo "   ...loading (sleep 2s)"
    sleep 2
done

# 4. 커넥터 생성
echo "   Creating Connector..."
curl -s -X POST -u "admin:public" "http://localhost:18083/api/v5/connectors" \
    -H "Content-Type: application/json" \
    -d '{
        "type": "http",
        "name": "ares4-webhook",
        "url": "http://fastapi_app2:8000/api/v1/mqtt/publish",
        "headers": { "content-type": "application/json", "X-Ares-Secret": "'"${SECRET_KEY}"'" },
        "parameters": {
            "body": "{\"topic\": \"${topic}\", \"payload\": ${payload}, \"clientid\": \"${clientid}\"}"
        },
        "method": "post"
    }' > /dev/null || true

# 5. 규칙 생성
echo "   Creating Rule..."
curl -s -X POST -u "admin:public" "http://localhost:18083/api/v5/rules" \
    -H "Content-Type: application/json" \
    -d '{
        "id": "rule:forward_telemetry",
        "sql": "SELECT * FROM \"ares4/+/telemetry\"",
        "actions": ["http:ares4-webhook"]
    }' > /dev/null || true

echo "✅ [EMQX] Webhook Configured successfully!"