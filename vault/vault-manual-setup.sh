#!/bin/sh
# Ares4: Vault PKI, Transit, AppRole 자동화 설정 스크립트
set -e

echo "=> Installing dependencies (jq, curl)"
apk add --no-cache jq curl

echo "=> Initializing Vault"
# 초기화 후 키 파일 저장
vault operator init -format=json > /vault/file/keys.json

UNSEAL_KEY_1=$(jq -r .unseal_keys_b64[0] < /vault/file/keys.json)
UNSEAL_KEY_2=$(jq -r .unseal_keys_b64[1] < /vault/file/keys.json)
UNSEAL_KEY_3=$(jq -r .unseal_keys_b64[2] < /vault/file/keys.json)
ROOT_TOKEN=$(jq -r .root_token < /vault/file/keys.json)

echo "=> Unsealing Vault"
vault operator unseal "$UNSEAL_KEY_1"
vault operator unseal "$UNSEAL_KEY_2"
vault operator unseal "$UNSEAL_KEY_3"

echo "=> Logging in with Root Token"
vault login "$ROOT_TOKEN"

# 1. Transit 엔진 활성화 (이미지 HMAC 검증용)
echo "=> Setting up Transit engine"
vault secrets enable transit || true

# 1-2. KV Secrets Engine 활성화 (HMAC 키 저장용)
echo "=> Setting up KV Secrets Engine for HMAC"
vault secrets enable -path=secret kv-v2 || true

# 2. PKI 설정 (Root CA -> Intermediate CA)
echo "=> Setting up Root PKI"
vault secrets enable -path=pki pki
vault secrets tune -max-lease-ttl=87600h pki
vault write -format=json pki/root/generate/internal common_name="ares4.io Root CA" ttl=87600h > /dev/null

echo "=> Setting up Intermediate PKI"
vault secrets enable -path=pki_int pki
vault secrets tune -max-lease-ttl=43800h pki_int
CSR=$(vault write -format=json pki_int/intermediate/generate/internal common_name="ares4.io Intermediate CA" | jq -r .data.csr)
CERT=$(vault write -format=json pki/root/sign-intermediate csr="$CSR" ttl="43800h" | jq -r .data.certificate)
vault write pki_int/intermediate/set-signed certificate="$CERT" > /dev/null

# 3. PKI 역할(Roles) 정의
echo "=> Creating PKI roles"
# 서버(EMQX)용 역할: 특정 도메인(ares4-mq-broker)과 IP 허용
vault write pki_int/roles/ares-server-role \
    allowed_domains="ares4-mq-broker,emqx,client,localhost" \
    allow_subdomains=true \
    allow_bare_domains=true \
    allow_ip_sans=true \
    key_type="rsa" \
    key_bits=2048 \
    max_ttl="720h" > /dev/null
# 기기(Raspberry Pi)용 역할: 어떤 이름이든 허용, IP 허용
    vault write pki_int/roles/ares-server-mqtt-client-role \
    allow_any_name=true \
    allow_ip_sans=true \
    key_type="rsa" \
    key_bits=2048 \
    max_ttl="720h" > /dev/null

# 4. AppRole 정책 설정
echo "=> Writing app-policy with HMAC permissions"
vault policy write app-policy - <<EOF
path "pki_int/issue/*" { capabilities = ["create", "update"] }
path "pki_int/certs" { capabilities = ["list"] }
path "pki_int/cert/*" { capabilities = ["read"] }
path "pki/cert/ca" { capabilities = ["read"] }
path "transit/keys/*" { capabilities = ["create", "read", "update"] }
path "transit/sign/*" { capabilities = ["update"] }
path "transit/verify/*" { capabilities = ["update"] }
path "sys/mounts" { capabilities = ["read"] }

# [핵심 추가] HMAC 키 저장을 위한 KV v2 권한
path "secret/data/ares4/hmac/*" { 
    capabilities = ["create", "update", "read", "list"] 
}
path "secret/metadata/ares4/hmac/*" { 
    capabilities = ["list", "delete"] 
}
EOF

# 5. AppRole 활성화 및 연결
echo "=> Configuring AppRole"
vault auth enable approle || true
vault write auth/approle/role/app-role \
    policies="app-policy" \
    secret_id_ttl="0" \
    token_num_uses=0

echo "\n[SUCCESS] Vault Internal Setup Complete."