#!/bin/sh
# This script fully automates the initial setup of the development environment.
# It initializes all services, including Vault for PKI, and generates certificates.
# This script should be run once for initial setup or for major migrations.

set -e
set -x # Enable debugging

COMPOSE_FILE="docker-compose.v2.yml"
ENV_FILE="./server2/.env"

# --- Helper Functions ---
echo_header() {
    echo "\n======================================================================"
    echo "=> $1"
    echo "======================================================================"
}

# 1. Clean up previous environment
echo_header "Cleaning up previous environment (containers, volumes)"
docker-compose -f "$COMPOSE_FILE" down -v

# 2. Start Vault service first
echo_header "Starting Vault container"
docker-compose -f "$COMPOSE_FILE" up -d vault

# Wait a moment for the Vault container to be ready
echo "Waiting for Vault to initialize..."
sleep 5

# 3. Run the main setup script inside the Vault container
echo_header "Configuring Vault, generating certificates, and setting up AppRole"
MSYS_NO_PATHCONV=1 docker exec -i vault sh < ./server2/vault/vault-manual-setup.sh > /dev/null

# 4. Fetch AppRole credentials and save to .env
echo_header "Fetching AppRole credentials"

# Ensure the .env file exists
touch "$ENV_FILE"

# Remove old credentials
sed -i '/^VAULT_TOKEN=/d' "$ENV_FILE"
sed -i '/^VAULT_APPROLE_ROLE_ID=/d' "$ENV_FILE"
sed -i '/^VAULT_APPROLE_SECRET_ID=/d' "$ENV_FILE"

# Get the root token from the keys.json file
ROOT_TOKEN=$(MSYS_NO_PATHCONV=1 docker exec vault jq -r .root_token /vault/file/keys.json)

# Fetch the RoleID and SecretID using the root token, ensuring jq runs inside the container
ROLE_ID=$(MSYS_NO_PATHCONV=1 docker exec -e VAULT_TOKEN="$ROOT_TOKEN" vault sh -c "vault read -format=json auth/approle/role/app-role/role-id | jq -r .data.role_id")
SECRET_ID=$(MSYS_NO_PATHCONV=1 docker exec -e VAULT_TOKEN="$ROOT_TOKEN" vault sh -c "vault write -f -format=json auth/approle/role/app-role/secret-id | jq -r .data.secret_id")

# Append new credentials to .env
echo "VAULT_APPROLE_ROLE_ID=$ROLE_ID" >> "$ENV_FILE"
echo "VAULT_APPROLE_SECRET_ID=$SECRET_ID" >> "$ENV_FILE"

echo_header "Initial Setup Complete!"
echo "Vault has been initialized, certificates generated, and AppRole credentials saved to $ENV_FILE."
echo "To start all services for development, run: ./server2/dev-start.sh"
echo "To stop all services, run: ./server2/dev-stop.sh"