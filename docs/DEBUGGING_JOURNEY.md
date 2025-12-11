# 개발 문제 해결 기록 (DEBUGGING_JOURNEY)

이 문서는 `server2` 프로젝트 개발 중 발생한 주요 문제들과 그 해결 과정을 기록합니다. 비슷한 문제가 발생했을 때 참고하거나, 프로젝트의 기술적 의사결정 과정을 이해하는 데 도움이 될 것입니다.

---

## 1. mTLS 연결 실패 (`fastapi_app2` <-> `emqx`)

### 1.1. 문제 발생 일시

2025년 11월 18일

### 1.2. 문제 요약

Docker Compose와 HashiCorp Vault를 사용하여 `server2` 개발 환경을 구축하는 과정에서, `fastapi_app2` 서비스가 `emqx` MQTT 브로커에 mTLS (Mutual TLS) 연결을 시도할 때 `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get issuer certificate` 오류가 반복적으로 발생했습니다.

### 1.3. 초기 진단 및 잘못된 가정

*   **가설 1: CA 인증서 체인 불완전 (Vault `ca_chain` 추출 오류)**
    *   Vault API의 `ca_chain` 배열을 `ca.crt` 파일에 저장하는 방식이 잘못되어 루트 CA가 누락되었을 것이라고 가정했습니다.
    *   `jq` 명령어를 수정하여 루트 CA와 중간 CA를 명시적으로 `ca.crt`에 추가하는 시도를 여러 번 했으나, 오류는 지속되었습니다.
    *   **교훈**: Python의 `ssl` 모듈은 OpenSSL 명령어보다 체인 검증에 더 엄격하며, 단순히 파일에 체인을 쓰는 것만으로는 충분하지 않을 수 있습니다.

*   **가설 2: Python `ssl` 모듈 또는 `paho-mqtt` 라이브러리 특성 문제**
    *   `openssl s_client` 명령어를 사용하여 `fastapi_app2` 컨테이너 내에서 EMQX로 직접 TLS 연결을 시도했습니다. 이 테스트에서도 **동일한 `unable to get issuer certificate` 오류가 발생**했습니다.
    *   **교훈**: 문제는 Python 코드의 버그나 `paho-mqtt`의 설정 문제가 아니라, **인증서 구성 자체의 근본적인 결함**에 있음을 확인했습니다.

*   **가설 3: `No such file or directory` 오류로의 전환**
    *   인증서 구성 로직을 여러 번 수정한 후, 오류 메시지가 `CERTIFICATE_VERIFY_FAILED`에서 `[Errno 2] No such file or directory`로 변경되었습니다.
    *   **교훈**: 이는 매우 긍정적인 신호였습니다. 인증서 검증 로직은 올바르게 수정되었으나, 이제는 컨테이너가 해당 인증서 파일을 찾지 못하는 문제로 전환되었음을 의미했습니다.

### 1.4. 근본 원인

최종적으로 확인된 문제의 근본 원인은 두 가지였습니다.

1.  **잘못된 인증서 파일 구성 전략:**
    *   EMQX 서버가 클라이언트에게 제시하는 `emqx.crt` 파일에는 **서버 인증서**와 **중간 CA 인증서**가 함께 포함되어야 했습니다.
    *   클라이언트(FastAPI)와 서버(EMQX) 양측이 상대방을 검증하기 위해 사용하는 CA 번들 파일(`full_chain_ca.crt`)에는 **루트 CA**와 **중간 CA**가 모두 포함되어야 했습니다.
    *   이전 시도에서는 이 구성이 정확히 지켜지지 않거나, 파일 내 인증서 순서/형식에 미묘한 문제가 있었습니다.

2.  **Docker 컨테이너 간 파일 공유 부재:**
    *   `vault` 컨테이너는 `vault-manual-setup.sh` 스크립트를 통해 **런타임(runtime)에** 인증서 파일들을 생성했습니다.
    *   `fastapi_app2` 컨테이너는 `Dockerfile`에 의해 **빌드 타임(build time)에** 이미지가 생성됩니다. 런타임에 생성된 파일은 빌드된 이미지에 포함될 수 없으며, 두 컨테이너는 기본적으로 격리되어 있어 서로의 파일 시스템에 직접 접근할 수 없었습니다.

### 1.5. 해결책

위의 근본 원인들을 해결하기 위해 다음과 같은 종합적인 해결책을 적용했습니다.

1.  **Docker 공유 볼륨 도입 (핵심):**
    *   `docker-compose.v2.yml` 파일을 수정하여 `vault_file_storage`라는 이름의 **공유 볼륨(Shared Volume)**을 `vault`, `fastapi_app2`, `emqx` 세 서비스가 모두 사용하도록 설정했습니다.
    *   `vault`는 이 볼륨에 인증서를 생성하고, `fastapi_app2`와 `emqx`는 이 볼륨을 읽기 전용으로 마운트하여 인증서에 접근하도록 했습니다.
    *   `depends_on: vault` 설정을 추가하여 `vault` 컨테이너가 항상 먼저 시작되고 인증서를 생성한 후에 다른 서비스들이 시작되도록 보장했습니다.

2.  **올바른 인증서 생성 로직 적용:**
    *   `vault-manual-setup.sh` 스크립트를 수정하여 인증서 생성 로직을 다음과 같이 확립했습니다.
        *   **`full_chain_ca.crt`**: 루트 CA + 중간 CA를 포함하는 CA 번들 파일.
        *   **`emqx.crt`**: EMQX 서버 인증서만 포함.
        *   **`client.crt`**: FastAPI 클라이언트 인증서만 포함.
    *   인증서 저장 경로를 공유 볼륨의 루트(`/vault/file`)로 명확히 지정하고, `chmod 644` 명령으로 모든 생성 파일에 대한 읽기 권한을 보장했습니다.

3.  **FastAPI 코드 안정성 강화:**
    *   `server2/app/domains/mqtt/client.py` 파일에 `os.path.exists()` 검증 로직을 추가하여, MQTT 연결 시도 전에 필요한 모든 인증서 파일이 실제로 존재하는지 먼저 확인하도록 수정했습니다. 이는 디버깅 시 명확한 오류 메시지를 제공하는 데 큰 도움이 되었습니다.
    *   `tls_set` 호출에 `cert_reqs=ssl.CERT_REQUIRED`와 `tls_version=ssl.PROTOCOL_TLSv1_2`를 명시적으로 설정하여 Python `ssl` 모듈의 엄격한 검증 요구사항을 충족시켰습니다.

4.  **전체 프로세스 자동화:**
    *   모든 수동 실행 절차를 `server2/vault/vault-init-dev.sh` 스크립트 하나로 통합하여, 단일 명령어로 전체 개발 환경을 초기화하고 실행할 수 있도록 자동화했습니다.

### 1.6. 최종 결과

위의 모든 수정 사항을 적용한 후, `fastapi_app2` 서비스는 `emqx` MQTT 브로커에 `MQTT client connected successfully.` 메시지와 함께 성공적으로 mTLS 연결을 수립했습니다.

---

## 2. Vault 컨테이너 권한 오류 (`permission denied`)

### 2.1. 문제 발생 일시

2025년 11월 18일

### 2.2. 문제 요약

새로운 개발 환경 자동화 스크립트(`dev-init.sh`)를 실행한 후, `vault` 컨테이너는 정상적으로 시작되지만 약 1분 뒤 백그라운드에서 CRL(인증서 폐기 목록)을 만들거나 OIDC 키를 순환하는 등의 작업을 시도할 때 `open /vault/file/logical/...: permission denied` 오류를 로그에 반복적으로 출력했습니다.

### 2.3. 초기 진단 및 잘못된 가정

*   **가설 1: 컨테이너 사용자 불일치:** `docker exec`로 스크립트를 실행하는 `root` 사용자와 Vault 서버 프로세스를 실행하는 `vault` 사용자 간의 권한 충돌로 가정했습니다.
    *   **시도**: `docker-compose.v2.yml`에서 `vault` 서비스를 `user: root`로 강제 실행.
    *   **결과**: 실패. 동일한 오류가 발생하여, 문제가 더 복잡함을 시사했습니다.

*   **가설 2: 파일 소유권 문제:** `root`가 생성한 파일들을 `vault` 사용자가 접근하지 못한다고 가정했습니다.
    *   **시도**: `vault-manual-setup.sh` 스크립트 마지막에 `chown -R vault:vault /vault/file` 명령을 추가하여 모든 파일의 소유권을 `vault` 사용자에게 이전.
    *   **결과**: 실패. `chown` 명령은 성공적으로 실행되었지만, `permission denied` 오류는 계속되었습니다.

*   **가설 3 (디버깅): `chmod 777`을 통한 문제 원인 고립:**
    *   **시도**: 문제의 원인이 순수하게 권한 문제인지 확인하기 위해, `chown` 이후 `chmod -R 777 /vault/file` 명령을 추가하여 모든 권한을 부여.
    *   **결과**: **성공.** 오류가 사라졌습니다. 이를 통해 문제는 파일/디렉토리 권한과 관련된 것임이 명확해졌습니다.

### 2.4. 근본 원인

`chmod 777`로 문제가 해결됨을 확인한 후, 정확한 원인을 찾기 위해 `vault-manual-setup.sh` 스크립트에 `ls -l` 디버깅 로그를 추가하여 권한 변경 과정을 추적했습니다.

*   **진짜 원인:** 범인은 `chmod 644 "$CERT_DIR"/*` 명령이었습니다.
*   `*` (glob) 패턴이 인증서 파일뿐만 아니라, Vault가 내부적으로 사용하는 데이터 디렉토리(`core`, `logical`, `sys` 등)까지 모두 일치시켰습니다.
*   디렉토리에 `644` 권한을 적용하면, 해당 디렉토리로 접근하거나 내부를 볼 수 있는 **실행(execute) 권한(`x`)이 제거**됩니다.
*   결과적으로 `vault` 프로세스는 자기 자신의 데이터 디렉토리에 접근할 수 없게 되어 `permission denied` 오류가 발생했던 것입니다.

### 2.5. 해결책

1.  **올바른 권한 설정:**
    *   문제를 일으킨 `chmod 644 "$CERT_DIR"/*` 명령을 삭제했습니다.
    *   대신, 디렉토리는 건드리지 않고 파일에만 권한을 적용하는 더 안전한 `find "$CERT_DIR" -maxdepth 1 -type f -exec chmod 644 {} +` 명령으로 교체했습니다.
    *   `chown -R vault:vault /vault/file` 명령은 그대로 유지하여 파일 소유권이 `vault` 사용자에게 올바르게 이전되도록 했습니다.

2.  **개발 워크플로우 개선 (사용자 제안):**
    *   단일 스크립트를 `dev-init.sh`(초기화), `dev-start.sh`(시작), `dev-stop.sh`(중지) 세 개의 명확한 역할로 분리하여 데이터 보존이 가능한 효율적인 개발 워크플로우를 구축했습니다.
    *   불필요한 레거시 스크립트(`vault-setup.sh`, `vault-init-dev.sh`)를 삭제하여 프로젝트 구조를 정리했습니다.

### 2.6. 최종 결과

`permission denied` 오류가 완전히 해결되었고, `chmod 777` 같은 불안전한 해결책 없이도 안정적인 개발 환경이 구축되었습니다.

---

## 3. `fastapi_app2` 및 `mqtt-listener` 구형 모듈 충돌 및 아키텍처 리팩토링 여정

### 3.1. 문제 발생 일시

2025년 11월 26일 - 27일

### 3.2. 문제 요약

`server2` 서비스 시작 시 `fastapi_app2` 및 `mqtt-listener` 컨테이너가 `PydanticSchemaGenerationError`, `ImportError`, `ModuleNotFoundError` 등 다양한 오류를 내며 반복적으로 충돌했습니다. 이는 아키텍처 리팩토링 과정에서 남겨진 `_old` 접미사가 붙은 구형 도메인 모듈(예: `device_api`, `data_old`, `accounts`, `components_old`, `hardware_old`)과 새로운 `services` 계층의 모듈이 혼재되어 발생한 문제였습니다.

### 3.3. 상세 해결 과정 및 아키텍처 결정

#### 3.3.1. `fastapi_app2` 충돌 문제 해결 (1차: 오류 회피)

*   **초기 문제**: `PydanticSchemaGenerationError` 및 `ModuleNotFoundError` 발생.
*   **원인 분석**:
    1.  메인 API 라우터(`app/api/v1/api.py`)가 더 이상 사용되지 않는 `device_api` 모듈을 임포트하고 있었습니다. 이 모듈은 내부적으로 SQLAlchemy 모델을 Pydantic `response_model`로 사용하려 하여 Pydantic 오류를 유발했습니다.
    2.  또한, `api.py`는 `data_old` 모듈을 임포트하고 있었고, 이 `data_old` 모듈은 존재하지 않는 `app.domains.data`를 참조하여 `ModuleNotFoundError`를 유발했습니다.
*   **임시 해결책**: 근본적인 리팩토링 대신, `api.py`에서 `device_api`와 `data_old`를 참조하는 두 줄의 코드를 주석 처리하여 급한 불을 껐습니다. 이는 `fastapi_app2`의 실행을 가능하게 했지만, 아키텍처적으로 올바른 해결책은 아니었습니다.

#### 3.3.2. `mqtt-listener` 연쇄 충돌 문제 해결 (2차: 아키텍처 리팩토링)

`fastapi_app2` 실행 후, `mqtt-listener`가 연쇄적으로 `ImportError`와 `ModuleNotFoundError`를 일으키는 문제가 발생했습니다.

*   **원인 분석**: 핵심 로직 파일인 `app/domains/mqtt/processor.py`가 리팩토링 이전의 `_old` 디렉토리(예: `accounts`, `components_old`, `data_old`, `hardware_old`)에 있는 `crud` 객체들을 직접 임포트하고 있었습니다. 이는 `server2`의 서비스 지향 아키텍처(SOA) 원칙에 위배되며, 모듈 경로가 변경되어 오류를 발생시켰습니다.
*   **리팩토링 전략 수립 (사용자 제안)**: 단순히 임포트 경로를 수정하는 대신, `_old` 모듈의 기능을 분석하여 **단일 책임 원칙**에 따라 새로운 `services` 도메인으로 재구성하기로 결정했습니다. 또한, 서비스 간의 직접적인 `crud` 참조 대신 `inter_domain` provider를 통해 통신하는 아키텍처 패턴을 적용하기로 했습니다.

*   **`data_old` 리팩토링 -> `telemetry_ingestion_service` 생성**:
    1.  **기능 분석**: `data_old`는 장치의 측정 데이터를 수신하고 저장하는 역할을 했습니다.
    2.  **서비스 분리 제안**: 이 기능을 '데이터 수집'과 '데이터 조회'로 분리하여 각각 `telemetry_ingestion_service`와 `telemetry_query_service`로 만들자는 아이디어가 나왔습니다.
    3.  **`telemetry_ingestion_service` 구현**:
        *   `services/telemetry_ingestion/schemas/telemetry.py`에 `server2`의 정규화된 DB 모델(`metric_name`, `metric_value` 등)에 맞는 Pydantic 스키마(`TelemetryDataCreate`)를 새로 정의했습니다.
        *   `services/telemetry_ingestion/crud/telemetry_crud.py`에 오직 데이터 저장(`create`) 기능만 담당하는 `telemetry_crud` 객체를 새로 구현했습니다.
        *   `inter_domain/telemetry_ingestion/providers.py`에 `telemetry_ingestion_providers`를 만들어, `telemetry_crud.create` 함수를 감싸는 안정적인 인터페이스를 제공했습니다.

*   **`processor.py` 최종 수정**:
    *   `processor.py`의 복잡하게 꼬여있던 임포트 문들을 모두 제거했습니다.
    *   `user_crud` 대신 `user_identity_providers`를 사용하도록 수정했습니다.
    *   `telemetry_crud` 대신 새로 만든 `telemetry_ingestion_providers`를 사용하도록 수정했습니다.
    *   나머지 `crud` 객체들(`device_crud`, `component_crud`, `device_component_instance_crud` 등)도 모두 리팩토링된 `services` 계층의 올바른 경로에서 가져오도록 수정했습니다. (`hardware_blueprint_crud`는 `hardware_old`에 남아있어 임시로 해당 경로 유지)

### 3.4. 최종 결과

위 리팩토링을 통해 `processor.py`의 모든 의존성 문제가 해결되었고, `mqtt-listener` 컨테이너가 마침내 안정적으로 실행되었습니다. 이 과정을 통해 `server2`의 서비스 지향 아키텍처 원칙을 적용하고, 레거시 `_old` 모듈의 의존성을 하나씩 제거하는 중요한 첫 단계를 완료했습니다.

---

## 4. mTLS 연결 실패 (fastapi_app2 <-> emqx) 2차

### 4.1. 문제 발생 일시

2025년 12월 08일

### 4.2. 문제 요약

fastapi_app2가 emqx MQTT 브로커에 mTLS 연결을 시도할 때 `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get issuer certificate` 오류가 반복되었습니다. 이 오류는 나중에 **`[Errno 2] No such file or directory`**로 전환되었습니다.

### 4.3. 초기 진단 및 가설 (실패 사례 포함)

| 가설 | 진단 및 시도 | 결과 | 교훈 |
|---|---|---|---|
| **가설 1: CA 인증서 체인 불완전** | Vault API의 `ca_chain` 배열 저장 방식 오류로 루트 CA가 누락되었을 것이라 가정하고 `jq` 명령어를 수정함. | ❌ 오류 지속 | Python `ssl` 모듈은 OpenSSL보다 체인 검증에 엄격함. 파일 구성 자체의 문제였음. |
| **가설 2: 라이브러리(Paho/gmqtt) 문제** | `fastapi_app2` 컨테이너 내에서 `openssl s_client` 명령어로 직접 TLS 연결 테스트를 시도함. | ❌ 동일 오류 발생 | 문제는 Python 코드나 라이브러리가 아닌, 인증서 구성 자체의 근본적인 결함임을 확인. |
| **가설 3: 파일 존재 여부 오류 전환** | 인증서 구성 로직 수정 후 오류 메시지가 `CERTIFICATE_VERIFY_FAILED`에서 `No such file or directory`로 변경됨. | ✅ 긍정적 신호 | 인증서 검증 로직은 올바르게 수정되었고, 문제가 파일 접근성으로 전환되었음을 의미. |

### 4.4. 근본 원인

*   **잘못된 인증서 파일 구성 전략:** EMQX 서버의 인증서 파일(`emqx.crt`)에 중간 CA가 누락되어 검증 체인이 불완전했습니다.
*   **Docker 컨테이너 간 파일 공유 부재:** Vault가 런타임에 생성한 인증서 파일들이 격리된 컨테이너 환경에서 접근 불가능했습니다.

### 4.5. 해결책 및 인증서 관리 전략

*   **Docker 공유 볼륨 도입 (핵심):** `vault_file_storage` 공유 볼륨을 세 서비스에 마운트하여 파일 접근 문제를 해결했습니다.
*   **올바른 인증서 파일 구성 및 생성 로직 적용:** `vault-manual-setup.sh` 스크립트를 수정하여 Vault가 올바른 구성의 인증서 파일을 생성하도록 확립했습니다.
    *   `full_chain_ca.crt`: 루트 CA + 중간 CA를 포함하는 CA 번들 파일.
    *   `emqx.crt`: EMQX 서버 인증서만 포함.
*   **mTLS 인증서 관리 전략 확립 (임시 파일 vs. 메모리 동적):** 현재 `server2` 아키텍처에서 mTLS를 구성하는 네 가지 핵심 요소는 역할과 보안 요구사항에 따라 다음과 같이 관리됩니다.

    | 구성 요소 | 역할 | 관리 방식 | 위치/목적 |
    |---|---|---|---|
    | **1. 클라이언트 인증서 (client.crt)** | FastAPI 클라이언트의 신원 증명 | 메모리 동적 (RAM Disk 임시 파일) | Vault에서 주기적으로 발급/갱신되며, 민감한 키가 영구 저장소에 남지 않도록 **/dev/shm**에 임시 생성 후 사용 |
    | **2. 클라이언트 개인 키 (client.key)** | 클라이언트 인증서에 대한 암호화 키 | 메모리 동적 (RAM Disk 임시 파일) | Vault에서 가져와 **/dev/shm**에 임시 생성 후 사용. 연결이 끊어지면 즉시 삭제됨 (보안 강화). |
    | **3. 서버 인증서 (emqx.crt)** | EMQX 서버의 신원 증명 | Docker 공유 볼륨 | Vault에서 생성되어 `vault_file_storage` 볼륨을 통해 EMQX 컨테이너의 `/opt/emqx/etc/certs`에 마운트되어 사용 |
    | **4. CA 번들 (full_chain_ca.crt)** | 서버 및 클라이언트 인증서의 신뢰 체인 (Root + Intermediate) | Docker 공유 볼륨 | Vault에서 생성되어 공유 볼륨을 통해 FastAPI와 EMQX 컨테이너에 모두 마운트됨. 변경 주기가 길고 신뢰성 확보가 목적. |

    이 전략은 민감한 클라이언트 키는 일회성으로 사용하고, 신뢰 체인과 서버 인증서는 안정적인 파일 시스템을 통해 컨테이너에 제공하여 보안과 운영의 균형을 맞춥니다.

### 4.6. 최종 결과

`fastapi_app2`는 `emqx` MQTT 브로커에 성공적으로 mTLS 연결을 수립했습니다.

---

## 5. Vault 컨테이너 권한 오류 (`permission denied`)

### 5.1. 문제 발생 일시

2025년 12월 08일

### 5.2. 문제 요약

vault 컨테이너 시작 후, 백그라운드 작업(CRL 생성 등) 중 `open /vault/file/logical/...: permission denied` 오류가 반복적으로 출력되었습니다.

### 5.3. 초기 진단 및 가설 (실패 사례 포함)

|가설|진단 및 시도|결과|교훈|
|---|---|---|---|
|가설 1: 컨테이너 사용자 불일치|스크립트를 실행하는 root와 서버 프로세스를 실행하는 vault 사용자 간의 권한 충돌 가정. docker-compose.v2.yml에서 vault 서비스를 user: root로 강제 실행.|❌ 실패|문제는 사용자 불일치가 아닌 파일/디렉토리 권한 설정 자체에 있었음.|
|가설 2: 파일 소유권 문제|root가 생성한 파일을 vault 사용자가 접근하지 못한다고 가정하고 vault-manual-setup.sh에 chown -R vault:vault /vault/file 명령 추가.|❌ 실패|chown은 성공했으나, 디렉토리의 실행 권한이 부족했음.|
|가설 3: chmod 777을 통한 원인 고립|문제 원인 파악을 위해 chown 후 chmod -R 777 /vault/file 명령을 추가하여 모든 권한을 강제 부여.|✅ 성공|문제가 순수하게 권한 설정에 있었으며, 특히 디렉토리 접근 권한(실행 권한)과 관련됨을 확인.|

### 5.4. 근본 원인

`vault-manual-setup.sh` 스크립트 내에서 사용했던 `chmod 644 "$CERT_DIR"/*` 명령이 인증서 파일뿐만 아니라 Vault의 내부 데이터 디렉토리에도 적용되면서, 디렉토리 접근에 필수적인 **실행(execute) 권한(x)**이 제거되었습니다.

### 5.5. 해결책

*   **올바른 권한 설정:**
    *   문제를 일으킨 명령을 삭제하고, 디렉토리가 아닌 일반 파일에만 권한을 적용하는 `find "$CERT_DIR" -maxdepth 1 -type f -exec chmod 644 {} +` 명령으로 교체했습니다.
*   **파일 소유권 이전 유지:**
    *   `chown -R vault:vault /vault/file` 명령을 유지하여 파일 소유권이 Vault 사용자에게 올바르게 이전되도록 했습니다.

### 5.6. 최종 결과

`permission denied` 오류가 해결되었으며, 안정적인 개발 워크플로우를 위해 3단계 스크립트 자동화(`dev-init.sh`, `dev-start.sh`, `dev-stop.sh`)로 개발 환경을 개선했습니다.


---

## 6. gmqtt 클라이언트 재연결 루프 및 최종 안정화

### 6.1. 문제 발생 일시

2025년 12월 8일

### 6.2. 문제 요약

이전 단계들을 통해 ACL 문제가 해결된 것으로 보였으나, `fastapi_app2`가 EMQX에 성공적으로 구독(`SUBACK`)한 직후 알 수 없는 이유로 다시 연결이 끊어지고 재연결을 시도하는 루프에 빠졌습니다.

### 6.3. 상세 해결 과정 및 교훈

| 단계 | 진단 및 가설 | 해결책 및 시도 | 결과 | 교훈 |
| :--- | :--- | :--- | :--- | :--- |
| **1. ACL 실패 재점검** | 구독 성공 후 끊어지는 현상이 여전히 ACL 문제일 수 있다고 가정. | `validator.py`의 토픽 매칭 로직을 정규식을 사용하여 더욱 정교하게 수정하고 상세 로그 추가. | ❌ 해결 안 됨 | 로그 분석 결과, `/acl` 웹훅은 이미 성공적으로 통과하고 있었음. 문제의 원인은 다른 곳에 있었음. |
| **2. Client ID 중복 문제** | `fastapi_app2`와 다른 서비스(e.g. `mqtt-listener`)가 동일한 Client ID (`ares-server-v2`)를 사용하여 서로의 연결을 끊는 현상 발생 가능성을 의심. | `mqtt_connection_manager.py`의 `__init__`에서 Client ID에 랜덤 UUID를 추가하여 고유 ID를 보장. (`ares-server-v2-xxxxxxxx`) | ✅ ID 충돌 해결 | 다중 클라이언트 환경에서는 MQTT Client ID의 고유성을 반드시 보장해야 함. |
| **3. ACL 규칙 매칭 실패** | 랜덤 ID가 적용되자, `ares-server-v2`에 대한 정적 규칙이 더 이상 일치하지 않아 ACL 실패. | `policy.py`의 규칙 검사 로직을 `client_id == '...'` (정확히 일치)에서 `client_id.startswith('...')` (접두사 일치)로 수정. | ✅ ACL 규칙 통과 | 동적으로 변경되는 속성을 기준으로 규칙을 적용할 때는 유연한 매칭 전략이 필요함. |
| **4. ACL 응답 형식 오류** | EMQX 로그에 `unsupported content-type: text/plain` 오류 발생. | `endpoints.py`의 `/acl` 응답을 `Response(content="1")`에서 최종적으로 `JSONResponse(content={"result": "allow"})`로 수정. | ✅ `SUBACK(0)` 성공 | EMQX 버전(5.x 이상)에 맞는 웹훅 응답 형식(JSON)을 따라야 함을 확인. |
| **5. 최종 불안정 연결** | 모든 문제가 해결된 듯 보였으나, 구독 성공 직후 다시 연결이 끊어지는 현상 발생. <br>**가설**: `gmqtt` 라이브러리의 자동 재연결 기능과 직접 구현한 재연결 로직이 충돌. | 1. `connect()` 메소드에 진입 로그 추가 -> 우리 로직은 재호출되지 않음을 증명.<br>2. **최종 해결**: 우리 재연결 로직(`connect_in_background` 반복문)을 **삭제**하고, 라이브러리의 자동 재연결 기능에 모든 것을 위임. | ✅ **연결 안정화** | 라이브러리가 제공하는 내장 기능(특히 네트워크 처리)을 최대한 신뢰하고 활용하는 것이 아키텍처를 단순하고 안정적으로 만듦. |

### 6.4. 근본 원인

최종 문제의 근본 원인은 **직접 구현한 애플리케이션 레벨의 재연결 로직**과 **`gmqtt` 라이브러리 내부의 자동 재연결 로직**이 서로 충돌하며 경쟁 상태(Race Condition)를 일으킨 것이었습니다. 우리 로직이 연결에 성공하고 `break`로 종료된 직후, 라이브러리의 재연결 로직이 불필요하게 다시 동작하여 기존 연결을 끊는 현상이 반복되었습니다.

### 6.5. 최종 해결책

1.  **재연결 로직 단일화 (라이브러리 위임):**
    *   `MqttConnectionManager`에서 직접 구현했던 `connect_in_background` 메소드를 완전히 삭제했습니다.
    *   `MqttLifecycleOrchestrator`가 시작 시 `connect()` 메소드를 단 한 번만 호출하도록 수정했습니다.
    *   이후 발생하는 모든 네트워크 단절 및 재연결은 `gmqtt` 라이브러리가 내부적으로 처리하도록 위임하여 충돌을 해결했습니다.

### 6.6. 최종 결과

모든 문제를 해결한 후, `fastapi_app2`는 시작 시 EMQX 브로커에 안정적으로 mTLS 연결을 수립하고, 구독(`SUBACK`)까지 성공적으로 마친 후 더 이상 끊김 없이 안정적인 상태를 유지하게 되었습니다. 이로써 `server2`의 MQTT 통신 파이프라인이 완벽하게 안정화되었습니다.