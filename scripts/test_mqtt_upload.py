# 실행 명령어
# docker compose --env-file shared_config/.env -f docker-compose.v2.yml exec mqtt-listener python scripts/test_mqtt_upload.py
import asyncio
import json
import random
from gmqtt import Client as MQTTClient

# --- 설정 ---
MQTT_BROKER = "emqx"
MQTT_PORT = 1883
DEVICE_UUID = "test-device-001"
TOPIC = f"ares4/{DEVICE_UUID}/telemetry"

async def main():
    client = MQTTClient("test-publisher-script")
    
    client.set_auth_credentials("ares_user", "ares_password")
    
    # EMQX에 접속
    await client.connect(MQTT_BROKER, MQTT_PORT)
    print("✅ [Test] Broker Connected!")

    # 가짜 센서 데이터 생성
    payload = {
        "temperature": round(20 + random.random() * 10, 2), # 20~30도
        "humidity": round(40 + random.random() * 20, 2),    # 40~60%
        "status": "RUNNING"
    }

    # 데이터 전송
    print(f"📡 Sending Telemetry to [{TOPIC}]")
    print(f"📦 Data: {json.dumps(payload, indent=2)}")
    
    client.publish(TOPIC, json.dumps(payload))

    # 전송 후 잠시 대기 (비동기 처리 시간 고려)
    await asyncio.sleep(1)
    
    await client.disconnect()
    print("👋 Disconnected.")

if __name__ == "__main__":
    asyncio.run(main())