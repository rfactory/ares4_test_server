#!/bin/sh

# 1. 인증서 경로 지정 (명확하게 하드코딩)
CERT_PATH="/opt/emqx/etc/certs"

echo "----------------------------------------------------------------"
echo "Starting Custom Entrypoint Script..."
echo "Checking for certificates at: $CERT_PATH"
echo "----------------------------------------------------------------"

# 2. 파일이 실제로 존재하는지 3초마다 확인 (무한 대기 안전장치)
# 하나라도 없으면 루프를 돌며 기다립니다.
while [ ! -f "$CERT_PATH/emqx.crt" ] || [ ! -f "$CERT_PATH/emqx.key" ] || [ ! -f "$CERT_PATH/full_chain_ca.crt" ]; do
    echo "[$(date)] Waiting for certificates..."
    echo "  - emqx.crt exists? $([ -f $CERT_PATH/emqx.crt ] && echo 'Yes' || echo 'No')"
    echo "  - emqx.key exists? $([ -f $CERT_PATH/emqx.key ] && echo 'Yes' || echo 'No')"
    # [중요] 여기 파일명이 ca.crt가 아니라 full_chain_ca.crt 여야 합니다.
    echo "  - full_chain_ca.crt exists? $([ -f $CERT_PATH/full_chain_ca.crt ] && echo 'Yes' || echo 'No')"
    sleep 3
done

echo "----------------------------------------------------------------"
echo "All certificates found! Starting EMQX..."
echo "----------------------------------------------------------------"

# 3. 권한 안전장치 (혹시 모르니 한번 더 풉니다)
chmod 644 $CERT_PATH/*

# 4. EMQX 진짜 실행 (PID 1번을 넘겨주며 교체)
exec /usr/bin/docker-entrypoint.sh /opt/emqx/bin/emqx foreground
