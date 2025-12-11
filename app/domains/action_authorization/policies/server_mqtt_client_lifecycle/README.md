# `ServerMqttClientLifecyclePolicy`
## 개요 (Overview)
이 Policy는 `fastapi_app2` 애플리케이션의 생명주기(`lifespan`) 동안, 서버의 MQTT Publisher 클라이언트의 전체 생명주기를 조율(orchestrate)하는 최상위 Policy입니다.

## 역할 및 책임 (Role & Responsibility)
- **시작 시 (`startup`):**
  1. `ServerCertificateAcquisitionPolicy`를 호출하여 Publisher가 사용할 유효한 mTLS 인증서를 획득합니다.
  2. `MqttConnectionManager`를 생성하고, 획득한 인증서를 주입합니다.
  3. `CommandDispatchRepository`를 생성하고, 전역 `AppRegistry`에 등록하여 다른 곳에서 발행 기능을 사용할 수 있도록 합니다.
  4. `MqttConnectionManager`의 연결을 시작합니다.
- **종료 시 (`shutdown`):**
  1. `MqttConnectionManager`의 연결을 안전하게 해제합니다.

## 사용처 (Usage)
- `main.py`의 `lifespan` 이벤트 핸들러에서 직접 호출되어, 애플리케이션의 시작과 종료에 맞춰 MQTT Publisher 클라이언트를 관리합니다.
