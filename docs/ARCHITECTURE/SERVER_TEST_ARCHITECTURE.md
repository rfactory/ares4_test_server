# Ares4 서버 테스트 아키텍처 설계 문서

## 1. 개요

이 문서는 Ares4 프로젝트의 서버 애플리케이션에 대한 테스트 아키텍처를 정의합니다. 효율적이고 신뢰할 수 있는 테스트 전략을 통해 코드 품질을 보장하고, 기능 변경 및 확장에 대한 안정성을 확보하는 것을 목표로 합니다.

## 2. 테스트 프레임워크 및 도구

*   **Python 테스트 프레임워크**: `pytest`
    *   `pytest`는 간결한 문법과 강력한 플러그인 생태계를 제공하여 Python 프로젝트의 테스트를 효율적으로 작성하고 실행할 수 있도록 합니다.
    *   `pytest-asyncio` 플러그인을 사용하여 비동기 코드(FastAPI) 테스트를 지원합니다.
    *   `httpx` 라이브러리를 사용하여 FastAPI 애플리케이션에 대한 HTTP 요청을 시뮬레이션합니다.

## 3. 테스트 유형 및 전략

### 3.1. 단위 테스트 (Unit Tests)

*   **목적**: 개별 함수, 메서드, 클래스 등 가장 작은 코드 단위를 격리하여 테스트합니다.
*   **위치**: 각 모듈의 `tests/` 디렉토리 내에 `test_*.py` 형태로 작성됩니다.
*   **예시**: `app/crud.py`의 함수들을 테스트하는 `tests/test_crud.py`

### 3.2. 통합 테스트 (Integration Tests)

*   **목적**: 여러 컴포넌트 또는 서비스(예: API 엔드포인트, 데이터베이스 상호작용)가 함께 작동하는 방식을 테스트합니다.
*   **위치**: `tests/` 디렉토리 내에 `test_*.py` 형태로 작성됩니다.
*   **예시**:
    *   `tests/test_auth_api.py`: 사용자 등록 및 로그인 API 엔드포인트 테스트.
    *   `tests/test_provisioning_api.py`: 기기 프로비저닝 흐름 테스트.

### 3.3. 엔드투엔드 테스트 (End-to-End Tests)

*   **목적**: 전체 시스템 또는 주요 사용자 흐름이 예상대로 작동하는지 검증합니다. (현재는 통합 테스트 수준에서 커버)
*   **향후 계획**: MQTT 브로커, Redis, 데이터베이스 등 모든 외부 의존성을 포함한 실제 환경에 가까운 테스트 환경에서 실행될 수 있습니다.

## 4. 테스트 실행

테스트는 `server` 디렉토리에서 Python 가상 환경이 활성화된 상태에서 `pytest` 명령어를 통해 실행됩니다.

```shell
# server 디렉토리로 이동
cd path/to/Ares4/server

# 가상 환경 활성화 (Windows)
venv\Scripts\activate

# 모든 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_auth_api.py

# 특정 마커를 가진 테스트 실행 (예: @pytest.mark.integration)
pytest -m integration
```

## 5. 테스트 데이터 관리

*   테스트 실행 시마다 깨끗한 데이터베이스 상태를 보장하기 위해 `conftest.py` 파일을 활용하여 테스트 픽스처(fixture)를 정의합니다.
*   `setup_database` 픽스처는 각 테스트 함수 실행 전후에 데이터베이스를 생성하고 삭제하여 테스트 간의 독립성을 보장합니다.

## 6. 테스트 코드 작성 가이드라인

*   **명확한 이름 지정**: 테스트 함수는 `test_`로 시작하며, 테스트하는 기능과 시나리오를 명확히 나타내야 합니다.
*   **AAA 패턴**: Arrange (준비), Act (실행), Assert (검증) 패턴을 사용하여 테스트 코드를 구조화합니다.
*   **격리**: 단위 테스트는 가능한 한 외부 의존성 없이 독립적으로 실행되어야 합니다. 필요한 경우 목(mock) 객체를 사용합니다.
*   **재현 가능성**: 모든 테스트는 어떤 환경에서든 동일한 결과를 반환해야 합니다.

## 7. 목업 장치 설정 및 인증서 (Mock Device Setup and Certificates)

*   **`app/scripts/temp_certs` 디렉토리**: `mock_device_publisher.py`와 같은 목업 장치 시뮬레이션 스크립트가 실행될 때, 임시 클라이언트 인증서 및 키 파일을 생성하고 저장하는 데 사용됩니다. 이 디렉토리는 목업 장치가 MQTT 브로커와 TLS 연결을 설정하는 데 필요한 인증서를 관리하며, 개발 및 테스트 환경에서만 사용되는 임시 아티팩트입니다.

## 8. 테스트 보조 스크립트 실행 (Running Test Helper Scripts)

`server/app/scripts` 폴더에는 개발, 테스트, 디버깅을 돕는 여러 유용한 스크립트가 포함되어 있습니다. 아래의 모든 명령어는 `server` 디렉토리에서 가상 환경이 활성화된 상태(`venv\Scripts\activate`)에서 실행해야 합니다.

### 8.1. 개발 보조 스크립트 (Development Helper Scripts)

*   **목업 장치 시뮬레이터 실행 (`mock_device_publisher.py`)**:
    이 스크립트는 `.env` 파일에 정의된 `MOCK_USER_EMAIL`과 `MOCK_USER_PASSWORD`를 사용하여 실행됩니다.

    ```shell
    # .env 파일을 사용하거나, 환경 변수가 이미 설정된 경우
    python -m app.scripts.mock_device_publisher
    ```

    또는, `MINGW64` (Git Bash)와 같은 Bash 셸에서는 다음과 같이 한 줄로 환경 변수를 설정하며 실행할 수 있습니다.

    ```shell
    # MINGW64 (Git Bash) 환경에서 한 줄로 실행
    MOCK_USER_EMAIL="test@example.com" MOCK_USER_PASSWORD="testpassword" python -m app.scripts.mock_device_publisher
    ```

*   **테스트용 사용자 및 장치 등록 (`register_mock_user.py`, `register_mock_device.py`)**:
    ```shell
    # 테스트 사용자 생성
    python -m app.scripts.register_mock_user

    # 테스트 장치 사전 등록
    python -m app.scripts.register_mock_device
    ```

*   **초기 데이터 시딩 (`seed_test_data.py`)**:
    이 스크립트는 `app/database.py`의 `init_db()` 함수를 호출하여 데이터베이스를 초기화합니다.
    ```shell
    python -m app.scripts.seed_test_data
    ```

*   **범용 MQTT 구독기 (디버깅용) (`test_subscriber.py`)**:
    ```shell
    python -m app.scripts.test_subscriber
    ```

### 8.2. 기타 개발 스크립트 (Other Development Scripts)

*   **MQTT ACL 파일 동적 생성 (`generate_mqtt_acl.py`)**:
    ```shell
    python -m app.scripts.generate_mqtt_acl
    ```

*   **다양한 테스트 메시지 발행 (`publish_alert_message.py`, `publish_offline_message.py`, `publish_test_message.py`)**:
    ```shell
    # '경고' 상태 메시지 발행
    python -m app.scripts.publish_alert_message

    # '오프라인' 상태 메시지 발행
    python -m app.scripts.publish_offline_message

    # 일반적인 테스트 메시지 발행
    python -m app.scripts.publish_test_message
    ```

*   **테스트 기기 UUID 강제 변경 (`update_device_uuid.py`)**:
    ```shell
    python -m app.scripts.update_device_uuid
    ```

*   **간단한 MQTT 발행 테스트 (`simple_publisher_test.py`)**:
    ```shell
    python -m simple_publisher_test
    ```

*   **간단한 MQTT 구독 테스트 (`simple_subscriber_test.py`)**:
    ```shell
    python -m simple_subscriber_test
    ```

