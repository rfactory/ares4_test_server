# MQTT 및 인증서 관리 리팩토링 구현 계획

## 1. 개요 (Overview)
-   Vault를 인증서 관리의 유일한 진실 공급원(Single Source of Truth)으로 삼는다.
-   `application/mqtt`에 있던 기존 MQTT 클라이언트 로직을 각 비즈니스 도메인으로 이전하고, `Policy` 중심의 아키텍처로 리팩토링한다.
-   `Policy`는 '조율(Orchestration)'을, `Manager`는 '기술 래핑(Wrapping)'을, `Repository`는 '데이터 소스 접근'을 책임지는 역할 분담 원칙을 명확히 한다.
-   **중요:** Publisher(`fastapi_app2`)와 Listener(`mqtt-listener`)는 별개의 Docker 컨테이너에서 독립된 프로세스로 실행된다.

## 2. 완료된 작업 (Completed Tasks)
-   Publisher와 관련된 모든 리팩토링이 완료되었습니다. (인증서 관리, Publisher 리팩토링, 내부 API 구현 등)

## 3. 진행할 작업 (Next Steps) - **최종 계획**

### 3.1. `ImportError` 버그 수정
-   **목표:** 현재 시스템 실행을 막고 있는 `ImportError: cannot import name 'AuditLogDetail'` 버그 수정.
-   **단계:** `app/domains/services/audit/crud/audit_command_crud.py` 파일의 import 문을 수정.

### 3.2. Listener 및 관련 스크립트 리팩토링
-   **목표:** Listener와 관련 스크립트들을 새로운 아키텍처 및 로깅 전략에 맞게 리팩토링.
-   **단계:**
    1.  **`MqttListenerManager` 생성:** `services/mqtt_gateway/managers/`에 MQTT 연결/TLS를 담당하는 Manager 생성 (100% 인메모리 TLS).
    2.  **`MqttMessageRouter` 생성:** `services/mqtt_gateway/services/`에 토픽에 따라 메시지를 라우팅하는 Router 생성.
    3.  **`run_listener.py` 스크립트 리팩토링:** `MqttListenerManager`와 `MqttMessageRouter`를 조립하여 Listener 프로세스를 실행하도록 수정.
    4.  **`MqttMessageRouter` 수정:** LWT 메시지 수신 시, `device_log` 테이블에 'OFFLINE' 이벤트를 기록하는 로직 추가.
    5.  **`run_device_health_checker.py` 스크립트 수정:** Timeout 감지 시, `device_log` 테이블에 'TIMEOUT' 이벤트를 기록하고, `/internal/dispatch-command` API를 호출하도록 수정.

### 3.3. `TelemetryIngestionPolicy` 리팩토링
-   **목표:** 불필요한 로그 기록 제거.
-   **단계:** `TelemetryIngestionPolicy`의 `ingest` 메서드에서 `audit_command_provider.log()` 호출 부분을 **완전히 삭제**.

### 3.4. 기존 `application/mqtt` 파일 삭제
-   **목표:** 모든 기능이 새로운 위치로 이전된 후, 기존의 불필요한 파일들을 삭제.
-   **삭제 대상:** `client.py`, `listener.py`, `processor.py`
-   **시점:** 모든 리팩토링이 완료된 후, 마지막에 수행.

## 4. 다음 단계
-   **`ImportError` 버그 수정**부터 시작하겠습니다.