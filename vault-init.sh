#!/bin/sh

# This script is intended to be run via `docker compose run` after the vault container is up.

# Set Vault connection details (these will be inherited from the environment)
export VAULT_ADDR="http://vault:8200"
export VAULT_TOKEN="root"

# Wait for Vault to be ready
until vault status -format=json | grep -q '"initialized": true'; do
  echo "Waiting for Vault to be initialized..."
  sleep 2
done

echo "Vault is initialized and ready."

# --- Disable default KV v1 engine and Enable KV v2 Secrets Engine ---
vault secrets disable secret || echo "No default 'secret' mount to disable, or already disabled."
vault secrets enable -path=secret kv-v2 || echo "KV v2 engine at 'secret' path already enabled."

# --- Store Secrets ---

# MQTT User Credentials
echo "Storing MQTT user credentials..."
vault kv put secret/mqtt/users/ares_user password="ares_password"

# JWT Secret Key
echo "Storing JWT secret key..."
vault kv put secret/jwt secret_key="a_very_secret_key_for_jwt_in_server2"

# Database Credentials
echo "Storing Database credentials..."
vault kv put secret/db connection_string="postgresql://ares_user:ares_password@ares4-postgres-v2:5432/ares_db_v2"

# Email Credentials
echo "Storing Email credentials..."
vault kv put secret/email username="goodsteelares4@gmail.com" password='jutm hwlf pbzl ydle' from="goodsteelares4@gmail.com" port="587" server="smtp.gmail.com"

# MQTT Client Certificates
echo "Storing MQTT client certificates..."
vault kv put secret/mqtt/certs ca_crt="$(cat /app/temp_certs/ca.crt)" client_crt="$(cat /app/temp_certs/client.crt)" client_key="$(cat /app/temp_certs/client.key)"

echo "
✅ All secrets have been stored in Vault."
