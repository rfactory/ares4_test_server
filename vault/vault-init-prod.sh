#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
VAULT_CONTAINER_NAME="vault"
COMPOSE_FILE="docker-compose.v2.yml"

# --- Helper Functions ---
echo_info() {
    echo "[INFO] $1"
}

echo_success() {
    echo "[SUCCESS] $1"
}

echo_warning() {
    echo "[WARNING] $1"
}

echo_error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# --- Main Script ---

echo "-----------------------------------------------------------------"
echo "          Vault Production Initialization Helper Script          "
echo "-----------------------------------------------------------------"
echo_warning "This script is for production setup and requires manual input for sensitive operations."
echo_warning "No secrets will be saved to disk by this script."
echo ""

# Check if Vault container is running
if ! docker-compose -f "$COMPOSE_FILE" ps -q "$VAULT_CONTAINER_NAME" | grep -q .; then
    echo_info "Vault container is not running. Starting it now..."
    docker-compose -f "$COMPOSE_FILE" up -d "$VAULT_CONTAINER_NAME"
    echo_info "Waiting for Vault to start..."
    sleep 5
fi

# Check Vault status
VAULT_STATUS=$(docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault status -format=json)

IS_INITIALIZED=$(echo "$VAULT_STATUS" | jq -r .initialized)
IS_SEALED=$(echo "$VAULT_STATUS" | jq -r .sealed)

# 1. Initialization Check
if [ "$IS_INITIALIZED" = "false" ]; then
    echo_error "Vault is not initialized. Please run 'docker-compose -f "$COMPOSE_FILE" exec $VAULT_CONTAINER_NAME vault operator init' manually, secure the keys, and then re-run this script."
fi

echo_success "Vault is already initialized."

# 2. Unseal Vault (if sealed)
if [ "$IS_SEALED" = "true" ]; then
    echo_info "Vault is sealed. Please provide 3 unseal keys."
    
    for i in 1 2 3; do
        printf "Enter Unseal Key #%s: " "$i"
        read -r UNSEAL_KEY
        docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault operator unseal "$UNSEAL_KEY"
    done
    
    # Verify unseal status
    VAULT_STATUS_AFTER_UNSEAL=$(docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault status -format=json)
    if [ "$(echo "$VAULT_STATUS_AFTER_UNSEAL" | jq -r .sealed)" = "true" ]; then
        echo_error "Vault unsealing failed. Please check your keys and try again."
    fi
fi

echo_success "Vault is unsealed."

# 3. Login to Vault
printf "Please enter your Vault Root Token to proceed: "
read -r VAULT_TOKEN
docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault login "$VAULT_TOKEN"

echo_success "Login successful."

# 4. Setup PKI Backend (Idempotent checks)
echo_info "Setting up PKI backend..."

# Enable Root PKI if not already enabled
if ! docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault secrets list | grep -q 'pki/'; then
    echo_info "Enabling Root PKI engine at path 'pki'..."
    docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault secrets enable -path=pki pki
    docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault secrets tune -max-lease-ttl=87600h pki
    docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault write pki/root/generate/internal common_name="ares4.io Root CA" ttl=87600h
else
    echo_info "Root PKI engine 'pki' already enabled."
fi

# Enable Intermediate PKI if not already enabled
if ! docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault secrets list | grep -q 'pki_int/'; then
    echo_info "Enabling Intermediate PKI engine at path 'pki_int'..."
    docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault secrets enable -path=pki_int pki
    docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault secrets tune -max-lease-ttl=43800h pki_int
    
    echo_info "Generating Intermediate CSR..."
    CSR_OUTPUT=$(docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault write -format=json pki_int/intermediate/generate/internal common_name="ares4.io Intermediate CA")
    INTERMEDIATE_CSR=$(echo $CSR_OUTPUT | jq -r .data.csr)
    
    echo_info "Signing Intermediate CSR with Root CA..."
    SIGNED_CERT_OUTPUT=$(docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault write -format=json pki/root/sign-intermediate csr="$INTERMEDIATE_CSR" ttl="43800h")
    INTERMEDIATE_CERT=$(echo $SIGNED_CERT_OUTPUT | jq -r .data.certificate)
    
    echo_info "Setting Signed Intermediate Certificate..."
    docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault write pki_int/intermediate/set-signed certificate="$INTERMEDIATE_CERT"
else
    echo_info "Intermediate PKI engine 'pki_int' already enabled."
fi

echo_success "PKI backend configured with Root and Intermediate CAs."

# 5. Create Role for EMQX (Idempotent)
echo_info "Creating/Updating PKI role for EMQX..."
docker-compose -f "$COMPOSE_FILE" exec "$VAULT_CONTAINER_NAME" vault write pki_int/roles/emqx-server-role allowed_domains="emqx,emqx.ares4.io,localhost" allow_subdomains=true max_ttl="720h" require_cn=false

echo_success "Role 'emqx-server-role' created/updated."


echo "-----------------------------------------------------------------"
echo_success "Production Vault setup is complete!"
echo "You can now issue certificates using the 'pki_int/issue/emqx-server-role' endpoint."
echo "Remember to manage your secrets securely."
