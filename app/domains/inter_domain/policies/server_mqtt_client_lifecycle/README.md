# `ServerMqttClientLifecyclePolicyProvider`

## 1. 개요 (Overview)
이 Provider는 `ServerMqttClientLifecyclePolicy`의 기능을 외부에 노출하는 인터페이스입니다. `main.py`의 `lifespan` 이벤트와 같은 애플리케이션 시작/종료 지점에서 이 Provider를 호출하여 MQTT 클라이언트 생명주기를 관리합니다.

## 2. 역할 및 책임 (Role & Responsibility)
-   `ServerMqttClientLifecyclePolicy` 인스턴스를 직접 import합니다.
-   `start_publisher_client` 및 `stop_publisher_client`와 같은 Policy의 핵심 메서드들을 외부에 노출합니다.
-   Policy의 내부 구현 세부 사항을 호출자로부터 숨기고, 안정적인 호출 인터페이스를 제공합니다.

## 3. 사용처 (Usage)
-   `main.py`의 `lifespan` 이벤트 핸들러에서 애플리케이션 시작 시 Publisher MQTT 클라이언트를 설정하고 연결하며, 종료 시 연결을 해제하기 위해 호출됩니다.
