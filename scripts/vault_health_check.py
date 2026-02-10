import hvac
import logging
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VaultHealthCheck")

def check_vault_infrastructure():
    logger.info(f"🔍 Vault 서버 연결 시도: {settings.VAULT_ADDR}")
    client = hvac.Client(url=settings.VAULT_ADDR)

    try:
        # 1. AppRole 로그인 테스트 (가장 중요)
        logger.info("🔑 AppRole 인증 시도 중...")
        login_response = client.auth.approle.login(
            role_id=settings.VAULT_APPROLE_ROLE_ID,
            secret_id=settings.VAULT_APPROLE_SECRET_ID
        )
        client.token = login_response['auth']['client_token']
        logger.info("✅ AppRole 인증 성공!")

        # 2. PKI 엔진 및 Role 확인
        pki_mount = settings.VAULT_PKI_MOUNT_POINT.strip('/')
        logger.info(f"🛡️ PKI 엔진 확인 중 (경로: {pki_mount})...")
        
        roles = client.list(f"{pki_mount}/roles")
        if roles and 'data' in roles and 'keys' in roles['data']:
            found_roles = roles['data']['keys']
            logger.info(f"✅ 발견된 PKI Roles: {found_roles}")
            
            # 코드에서 사용하는 Role이 있는지 확인
            required_roles = ["ares-server-role", "ares-server-mqtt-client-role"]
            for r in required_roles:
                if r in found_roles:
                    logger.info(f"   - {r}: 존재 확인")
                else:
                    logger.error(f"   - {r}: ❌ 존재하지 않음! (Vault 설정 필요)")
        else:
            logger.error(f"❌ PKI 엔진에 설정된 Role이 없습니다.")

        # 3. Transit 엔진 확인 (HMAC용)
        logger.info("💎 Transit 엔진 활성화 여부 확인 중...")
        mounts = client.sys.list_mounted_secrets_engines()
        if 'transit/' in mounts['data']:
            logger.info("✅ Transit 엔진 활성화 확인")
        else:
            logger.error("❌ Transit 엔진이 활성화되어 있지 않습니다! (vault secrets enable transit)")

    except Exception as e:
        logger.error(f"🚨 진단 중 오류 발생: {e}")
        logger.info("💡 팁: Vault가 실행 중인지, 네트워크(Docker)가 연결되었는지 확인하세요.")

if __name__ == "__main__":
    check_vault_infrastructure()