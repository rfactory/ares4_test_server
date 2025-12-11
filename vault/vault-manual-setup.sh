#!/bin/sh
# This script contains all manual steps to correctly set up Vault and generate certificates.
# It creates a Full CA Bundle to solve [SSL: CERTIFICATE_VERIFY_FAILED] errors.

set -e

# --- Helper Functions ---
echo_header() {
    echo "\n--- $1 ---"
}

# [수정됨] curl 추가 (Root CA 다운로드용)
echo_header "Installing dependencies (jq, curl)"
apk add --no-cache jq curl

echo_header "Initializing Vault"
vault operator init -format=json > /vault/file/keys.json

UNSEAL_KEY_1=$(jq -r .unseal_keys_b64[0] < /vault/file/keys.json)
UNSEAL_KEY_2=$(jq -r .unseal_keys_b64[1] < /vault/file/keys.json)
UNSEAL_KEY_3=$(jq -r .unseal_keys_b64[2] < /vault/file/keys.json)
ROOT_TOKEN=$(jq -r .root_token < /vault/file/keys.json)

echo_header "Unsealing Vault"
vault operator unseal "$UNSEAL_KEY_1"
vault operator unseal "$UNSEAL_KEY_2"
vault operator unseal "$UNSEAL_KEY_3"

echo_header "Logging into Vault with Root Token"
vault login "$ROOT_TOKEN"

echo_header "Setting up Root PKI"
vault secrets enable -path=pki pki
vault secrets tune -max-lease-ttl=87600h pki
# Root CA 생성
ROOT_CA_CERT=$(vault write -format=json pki/root/generate/internal common_name="ares4.io Root CA" ttl=87600h | jq -r .data.certificate)

echo_header "Setting up Intermediate PKI"
vault secrets enable -path=pki_int pki
vault secrets tune -max-lease-ttl=43800h pki_int
CSR_OUTPUT=$(vault write -format=json pki_int/intermediate/generate/internal common_name="ares4.io Intermediate CA")
INTERMEDIATE_CSR=$(echo "$CSR_OUTPUT" | jq -r .data.csr)
SIGNED_CERT_OUTPUT=$(vault write -format=json pki/root/sign-intermediate csr="$INTERMEDIATE_CSR" ttl="43800h")
INTERMEDIATE_CERT=$(echo "$SIGNED_CERT_OUTPUT" | jq -r .data.certificate)
vault write pki_int/intermediate/set-signed certificate="$INTERMEDIATE_CERT" > /dev/null

echo_header "Creating PKI role for server certificates"
vault write pki_int/roles/ares-server-role \
    allowed_domains="emqx,client,localhost,ares4-mqtt-listener" \
    allow_subdomains=true \
    allow_bare_domains=true \
    max_ttl="720h" > /dev/null

# Create the role required by the fastapi_app2 service
echo_header "Creating PKI role for server MQTT client"
vault write pki_int/roles/ares-server-mqtt-client-role \
    allow_any_name=true \
    max_ttl="720h" > /dev/null

# --- AppRole Setup ---
echo_header "Enabling and Configuring AppRole Auth"
vault auth enable approle

# Create a policy for applications that need to issue certificates
echo '
path "pki_int/issue/ares-server-role" { capabilities = ["create", "update"] }
path "pki_int/issue/ares-server-mqtt-client-role" { capabilities = ["create", "update"] }
' | vault policy write app-policy -

# Create an AppRole named 'app-role' linked to the policy
vault write auth/approle/role/app-role \
    secret_id_ttl="10m" \
    token_num_uses=10 \
    token_ttl="20m" \
    token_max_ttl="30m" \
    policies="app-policy"

# --- Certificate Generation for EMQX ---
echo_header "Generating EMQX certificates into shared volume"
CERT_DIR="/vault/file"
mkdir -p "$CERT_DIR"

# Issue a certificate for EMQX
echo "Issuing certificate for EMQX..."
CERT_DATA=$(vault write -format=json pki_int/issue/ares-server-role common_name="emqx" ttl="24h")

if [ -z "$CERT_DATA" ]; then
    echo "ERROR: Failed to issue certificate for EMQX."
    exit 1
fi

# Save the certificate, private key
echo "Saving EMQX certificate to $CERT_DIR/emqx.crt"
echo "$CERT_DATA" | jq -r '.data.certificate' > "$CERT_DIR/emqx.crt"

echo "Saving EMQX private key to $CERT_DIR/emqx.key"
echo "$CERT_DATA" | jq -r '.data.private_key' > "$CERT_DIR/emqx.key"

# ------------------------------------------------------------------
# [핵심 수정] Full CA Bundle 생성 (Intermediate + Root)
# ------------------------------------------------------------------
echo "Creating Full CA Bundle (Root + Intermediate)..."

# 1. Root CA 가져오기 (Vault API 사용)
ROOT_CA=$(curl -s http://127.0.0.1:8200/v1/pki/ca/pem)

# 2. Intermediate CA 가져오기 (방금 발급된 인증서 데이터에서 추출)
INTERMEDIATE_CA=$(echo "$CERT_DATA" | jq -r '.data.issuing_ca')

# 3. 하나로 합치기 (순서 중요: Intermediate -> Root)
# 이렇게 해야 클라이언트가 Chain을 따라가며 신뢰를 확인할 수 있습니다.
echo "Saving Full Chain CA to $CERT_DIR/full_chain_ca.crt"
echo "$INTERMEDIATE_CA" > "$CERT_DIR/full_chain_ca.crt"
echo "" >> "$CERT_DIR/full_chain_ca.crt" # 줄바꿈 추가
echo "$ROOT_CA" >> "$CERT_DIR/full_chain_ca.crt"
# ------------------------------------------------------------------


echo_header "Setting file permissions with verbose logging"

# "대문"을 먼저 열어 find가 하위 폴더를 탐색할 수 있도록 보장합니다.
echo "Ensuring top-level directory (/vault/file) is accessible..."
chmod 755 /vault/file

# 디렉토리 권한 설정
echo "\n--> Setting DIRECTORY permissions to 755 (rwxr-xr-x)..."
for d in $(find /vault/file -type d); do
    echo "  - Changing permissions for directory: $d"
    ls -ld "$d" # 변경 전 권한 출력
    chmod 755 "$d"
    ls -ld "$d" # 변경 후 권한 출력
done

# 파일 권한 설정
echo "\n--> Setting FILE permissions to 644 (rw-r--r--)..."
for f in $(find /vault/file -type f); do
    echo "  - Changing permissions for file: $f"
    ls -l "$f" # 변경 전 권한 출력
    chmod 644 "$f"
    ls -l "$f" # 변경 후 권한 출력
done

# 소유권 설정
echo "\n--> Setting OWNERSHIP to vault:vault recursively..."
chown -R vault:vault /vault/file
echo "Ownership change completed."

# 최종 권한 상태 확인
echo "\n--> Final permission status for /vault/file:"
ls -l /vault/file

echo "\n[SUCCESS] Manual setup complete. AppRole configured and Full CA Bundle generated."