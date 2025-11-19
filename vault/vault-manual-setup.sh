#!/bin/sh
# This script contains all manual steps to correctly set up Vault and generate certificates based on user analysis.

set -e

# --- Helper Functions ---
echo_header() {
    echo "\n--- $1 ---"
}


echo_header "Installing dependencies (jq)"
apk add --no-cache jq

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

# --- AppRole Setup ---
echo_header "Enabling and Configuring AppRole Auth"
vault auth enable approle

# Create a policy for applications that need to issue certificates
echo 'path "pki_int/issue/ares-server-role" { capabilities = ["create", "update"] }' | vault policy write app-policy -

# Create an AppRole named 'app-role' linked to the policy
vault write auth/approle/role/app-role \
    secret_id_ttl="10m" \
    token_num_uses=10 \
    token_ttl="20m" \
    token_max_ttl="30m" \
    policies="app-policy"

# --- Certificate Generation ---
echo_header "Generating certificates into shared volume"
CERT_DIR="/vault/file"
mkdir -p "$CERT_DIR"

# Issue a certificate to get the full chain data
CERT_DATA=$(vault write -format=json pki_int/issue/ares-server-role common_name="emqx")

# Create full_chain_ca.crt (CA Bundle for verification): Root CA + Intermediate CA
echo "Creating full_chain_ca.crt (Root + Intermediate)"
echo "$ROOT_CA_CERT" > "$CERT_DIR/full_chain_ca.crt"
echo "" >> "$CERT_DIR/full_chain_ca.crt"
echo "$INTERMEDIATE_CERT" >> "$CERT_DIR/full_chain_ca.crt"

# Issue and create EMQX server certificate (leaf only)
echo "Creating emqx.crt and emqx.key"
EMQX_CERT_DATA=$(vault write -format=json pki_int/issue/ares-server-role common_name="emqx")
echo "$EMQX_CERT_DATA" | jq -r .data.certificate > "$CERT_DIR/emqx.crt"
echo "$EMQX_CERT_DATA" | jq -r .data.private_key > "$CERT_DIR/emqx.key"

# Issue and create FastAPI client certificate (leaf only)
echo "Creating client.crt and client.key"
CLIENT_CERT_DATA=$(vault write -format=json pki_int/issue/ares-server-role common_name="client")
echo "$CLIENT_CERT_DATA" | jq -r .data.certificate > "$CERT_DIR/client.crt"
echo "$CLIENT_CERT_DATA" | jq -r .data.private_key > "$CERT_DIR/client.key"

# For compatibility, also create the old ca.crt for now, which is the full chain.
cp "$CERT_DIR/full_chain_ca.crt" "$CERT_DIR/ca.crt"

echo_header "Setting file permissions"
find "$CERT_DIR" -maxdepth 1 -type f -exec chmod 644 {} +
chown -R vault:vault /vault/file

echo "\n[SUCCESS] Manual setup complete. AppRole configured and certificates generated."
