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
