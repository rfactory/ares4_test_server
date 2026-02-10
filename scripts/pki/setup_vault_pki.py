# server2/scripts/pki/setup_vault_pki.py
# Vault 은행장 만들
import sys
import hvac
import logging
from pathlib import Path

# server2 경로 추가 (app 모듈을 불러오기 위함)
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.core.config import settings
# 방금 만든 오프라인 스크립트의 서명 함수 import
from scripts.pki.generate_genesis_pki import sign_vault_csr, main as generate_keys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VaultSetup")

def setup_vault():
    # 0. 키가 없으면 먼저 생성
    generate_keys()

    # 1. Vault 연결
    logger.info(f"Connecting to Vault at {settings.VAULT_ADDR}...")
    client = hvac.Client(url=settings.VAULT_ADDR)
    # 로컬 개발용 Root Token (실제 환경에선 환경변수로 주입)
    if not client.is_authenticated():
        client.token = os.getenv("VAULT_TOKEN", "root") # 예시: dev 모드면 root
    
    if not client.is_authenticated():
        logger.error("❌ Vault Authentication Failed. Please set VAULT_TOKEN.")
        return

    mount_point = settings.VAULT_PKI_MOUNT_POINT # "pki_int"

    # 2. PKI 엔진 활성화 (이미 있으면 패스)
    try:
        client.sys.enable_secrets_engine(backend_type='pki', path=mount_point)
        logger.info(f"✅ Enabled PKI engine at '{mount_point}'")
    except hvac.exceptions.InvalidRequest:
        logger.info(f"ℹ️ PKI engine at '{mount_point}' already enabled.")

    # 3. Tuning (TTL 설정)
    client.sys.tune_mount_configuration(
        path=mount_point,
        default_lease_ttl=settings.VAULT_SERVER_CERT_TTL, # "720h"
        max_lease_ttl="8760h", # 1년
    )

    # 4. [핵심] Vault: "CSR 만들어줘"
    logger.info("Generating CSR from Vault...")
    csr_response = client.secrets.pki.generate_intermediate(
        mount_point=mount_point,
        type="internal",
        common_name="Ares4 Intermediate CA",
    )
    csr_pem = csr_response['data']['csr']

    # 5. [핵심] Offline Script: "서명해줄게" (Air-Gap Simulation)
    logger.info("✍️ Signing CSR with Offline Root CA...")
    signed_cert_pem = sign_vault_csr(csr_pem)

    # 6. [핵심] Vault: "서명된 거 받아라" (Import)
    client.secrets.pki.set_signed_intermediate(
        mount_point=mount_point,
        certificate=signed_cert_pem
    )
    logger.info("✅ Signed Intermediate CA imported to Vault!")

    # 7. Role 설정 (기존 Repository 코드와 매칭)
    # 7-1. ares-server-role (장치용)
    client.secrets.pki.create_or_update_role(
        mount_point=mount_point,
        name=settings.VAULT_PKI_LISTENER_ROLE, # "ares-server-role"
        extra_params={
            "allow_any_name": True, # UUID 등을 CN으로 쓰기 위함
            "max_ttl": "8760h",
        }
    )
    logger.info(f"✅ Role configured: {settings.VAULT_PKI_LISTENER_ROLE}")

    # 7-2. ares-server-mqtt-client-role (서버 자신용)
    client.secrets.pki.create_or_update_role(
        mount_point=mount_point,
        name="ares-server-mqtt-client-role",
        extra_params={
            "allow_any_name": True,
            "max_ttl": "8760h",
        }
    )
    logger.info("✅ Role configured: ares-server-mqtt-client-role")
    
    print("\n🎉 Vault PKI Setup Complete! Your 'VaultCertificateCommandRepository' is ready.")

if __name__ == "__main__":
    import os
    setup_vault()