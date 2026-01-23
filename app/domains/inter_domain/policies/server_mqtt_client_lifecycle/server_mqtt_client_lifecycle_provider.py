from sqlalchemy.orm import Session
# Note: We are importing the policy INSTANCE here, not the class.
from app.domains.action_authorization.policies.server_mqtt_client_lifecycle.server_mqtt_client_lifecycle_policy import server_mqtt_client_lifecycle_policy

class ServerMqttClientLifecyclePolicyProvider:
    """
    `ServerMqttClientLifecyclePolicy`의 기능을 외부 도메인(주로 `main.py`의 lifespan)에 노출하는 제공자입니다.
    싱글턴으로 관리되는 Policy 인스턴스의 메서드를 그대로 호출하여 전달하는 역할만 수행합니다.
    """
    async def start_publisher_client(self, db: Session):
        """
        Publisher용 MQTT 클라이언트의 생명주기 시작을 Policy에 위임합니다.
        """
        # Policy가 async로 변경되었으므로 await를 추가합니다.
        return await server_mqtt_client_lifecycle_policy.start_publisher_client(db)

    async def stop_publisher_client(self):
        """
        Publisher용 MQTT 클라이언트의 생명주기 중지를 Policy에 위임합니다.
        """
        # Policy가 async로 변경되었으므로 await를 추가합니다.
        return await server_mqtt_client_lifecycle_policy.stop_publisher_client()

# Singleton instance of the provider
server_mqtt_client_lifecycle_policy_provider = ServerMqttClientLifecyclePolicyProvider()