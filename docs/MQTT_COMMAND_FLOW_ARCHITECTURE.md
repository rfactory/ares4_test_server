# MQTT 명령 흐름 및 인증 아키텍처 설계

## 1. 개요 (Overview)

### 1.1. 목표
Flutter 앱과 같은 클라이언트에서 기기로 명령(예: 펌프 가동)을 전송하는 아키텍처를 설계한다.

### 1.2. 핵심 원칙
- `Policy -> Service -> Repository` 계층 분리
- `inter_domain`을 통한 의존성 관리
- 단일 책임 원칙(SRP) 준수

## 2. 주요 컴포넌트 역할 비유

-   **우체국:** `EMQX` (MQTT 브로커)
-   **고객:** `MQTT 클라이언트` (기기, 앱, 서버의 Publisher/Listener)
-   **신분증:** `클라이언트 인증서`
-   **신분증 발급소:** `certificate_management` 도메인 (내부적으로 Vault PKI 엔진 사용)
-   **우편물 발송 담당자:** `DeviceCommandDispatchPolicy` 및 하위 계층

## 3. 인증서 발급 및 사용 흐름 (mTLS)

### 3.1. 서버의 자체 인증 (서버 시작 시)
1.  서버의 MQTT 클라이언트(Publisher, Listener)가 시작될 때, '신분증 발급소'(`certificate_management` 도메인)에 자신의 '직원증'(클라이언트 인증서)을 요청한다.
2.  이때, '신분증 발급소'는 **무조건 새로 발급하는 것이 아니라, 먼저 Vault에 최근에 발급한 유효한 인증서가 있는지 '조회'**한다.
3.  유효한 인증서가 없거나 만료가 임박한 경우에만, Vault의 PKI 엔진을 통해 단기 유효(short-lived) 인증서를 **새로 '발급'**하여 전달한다.
4.  서버 클라이언트는 이렇게 받은 인증서를 사용하여 '우체국'(EMQX 브로커)에 mTLS 연결을 수립한다.

### 3.2. 클라이언트의 인증 (기기/앱 등록 시)
1.  새로운 기기나 앱이 서버에 등록을 요청하면, 서버는 이들을 위해 '신분증 발급소'(`certificate_management` 도메인)를 통해 고유한 '신분증'(클라이언트 인증서)을 발급해준다.
2.  기기/앱은 이 인증서를 안전하게 저장한다.
3.  '우체국'(EMQX 브로커)에 연결할 때, 이 인증서를 제출하여 자신의 신원을 증명한다.

### 3.3. 주기적 재인증 (보안 강화)
-   **개요:** 한 번의 연결을 계속 신뢰하는 대신, '신분증' 자체의 유효 기간을 짧게(예: 24시간) 설정하는 '단기 유효 인증서' 전략을 사용한다.
-   **자동 갱신:** 모든 클라이언트(서버, 기기, 앱)는 자신의 인증서가 만료되기 전에 '신분증 발급소'에 조용히, 내부적으로 새로운 인증서를 요청하여 갱신해야 한다. (실패 시 푸시 알림 등 2차 안전장치 활용)
-   **강제 폐기:** 관리자는 유출된 인증서를 즉시 '폐기(Revoke)'할 수 있으며, '우체국'(EMQX 브로커)은 이 폐기 목록을 확인하여 해당 인증서를 사용하는 클라이언트의 연결을 강제로 끊는다.

## 4. Vault 보안 개념: Unseal Key vs. PKI 개인 키

-   **Unseal Key (예: 5개 중 3개):**
    -   **역할:** 잠겨있는 Vault 금고의 **'문'**을 여는 물리적인 여러 개의 열쇠.
    -   **비유:** 은행 금고의 두꺼운 강철 문을 여는, 여러 명이 돌려야 하는 여러 개의 열쇠.
-   **PKI 루트 개인 키:**
    -   **역할:** 금고 안에 보관된 내용물 중 하나. 다른 인증서에 서명하는 데 사용되는 실제 **'도장'**
    -   **비유:** 금고 문을 열고 들어가, 개인 금고 안에 보관된 '위조 방지용 원본 직인'.

## 5. `certificate_management` 도메인 역할 분담

`certificate_management` 도메인 내의 서비스들은 Vault와 상호작용할 때, CQRS(Command Query Responsibility Segregation) 원칙에 따라 명확한 역할을 가진다.

### 5.1. `CertificateCommandService` (명령/쓰기 서비스)
-   **역할:** Vault의 상태를 변경하는 **쓰기(Write) 작업**을 담당한다.
-   **주요 기능:**
    -   `issue_device_certificate()`: 기기를 위한 새 인증서 **발급**.
    -   `issue_server_mqtt_cert()`: 서버 자신을 위한 새 인증서 **발급**. (내부적으로 유효한 기존 인증서가 있는지 **조회 후 발급**하는 최적화 로직 포함)
    -   `revoke_certificate()`: 기존 인증서 **폐기**.

### 5.2. `CertificateQueryService` (조회/읽기 서비스)
-   **역할:** Vault의 상태를 변경하지 않는 **읽기(Read-Only) 작업**을 담당한다.
-   **주요 기능:**
    -   `is_certificate_valid()`: 특정 인증서의 유효성(폐기/만료 여부) **조회**.
    -   `get_crl()`: 인증서 폐기 목록(CRL) **조회**.
    -   `get_issued_certificate_details()`: 특정 인증서의 상세 정보 **조회**.
-   **사용 예:** 관리자 대시보드, 보안 감시, 선제적 갱신 알림 등.

## 6. `DeviceCommandDispatchPolicy` 전체 실행 계획

1.  **1단계: `certificate_management` 도메인 강화**
    -   `VaultCertificateRepository`에 Vault PKI 엔진과 상호작용하는 메서드들(`issue_cert_...`, `get_latest_cert_...` 등)을 구현한다.
    -   `CertificateCommandService`에 **'조회 후 발급'** 로직을 포함하는 `issue_server_mqtt_cert()` 메서드를 추가한다.
    -   `CertificateCommandProvider`와 `CertificateQueryProvider`를 통해 이 기능들을 외부에 노출시킨다.

2.  **2단계: `command_dispatch` 도메인 신설**
    -   `MqttPublisherRepository`를 생성한다. 이 Repository는 생성 시 1단계에서 만든 Provider를 통해 인증서 내용을 동적으로 받아와 `paho-mqtt` 클라이언트를 초기화하고 연결한다.
    -   `MqttCommandPublisherService` 및 `MqttCommandPublisherProvider`를 생성하여 계층 구조를 완성한다.

3.  **3단계: `DeviceCommandDispatchPolicy` 생성**
    -   API 요청을 받아, `UserPermissionValidator` 등으로 권한을 검증한다.
    -   `BlueprintCommandCompatibilityValidator` 등으로 명령 유효성을 검증한다.
    -   2단계에서 만든 `MqttCommandPublisherProvider`를 호출하여 MQTT 메시지 발행을 요청한다.
    -   `audit_command_provider`를 호출하여 사용자 행위를 감사 로그로 기록한다.

4.  **4단계: `application` 계층 연결**
    -   FastAPI 엔드포인트(예: `POST /devices/{device_id}/command`)를 생성하여 3단계의 `Policy`를 호출한다.
    -   FastAPI lifespan 이벤트를 사용하여 2단계의 `MqttPublisherRepository` 연결/해제 로직을 관리한다.

## 7. 기기 상태 관리 및 Redis 확장성 (Device State Management & Redis Scalability)

### 7.1. 서버의 기기 상태 관리 역할
-   **단일 진실 공급원(Single Source of Truth):** 서버는 라즈베리파이로부터 오는 모든 상태 보고(예: `led: off`, `펌프: on`, 센서 데이터)를 받아 Redis에 항상 최신 상태를 저장하고 기억한다.
-   **Flutter 앱 동기화:** Flutter 앱은 시작될 때 서버의 Redis에 저장된 최신 기기 상태를 요청하여 UI를 업데이트하며, 이후 MQTT를 통해 실시간으로 상태 변화를 구독한다. 앱을 껐다 켜도 최신 상태가 반영된다.

### 7.2. Redis 확장성
-   **데이터 크기 분석:** 기기당 상태 데이터는 수백 바이트에서 몇 킬로바이트(KB) 수준이다.
    -   예: 1만 대의 기기 상태를 저장해도 수십 ~ 수백 메가바이트(MB) 수준으로, 일반적인 서버의 RAM 용량(GB 단위)으로 충분히 감당 가능하다.
-   **확장 전략:** 기기 수가 수십만, 수백만 대로 늘어날 경우를 대비한 표준 전략이 존재한다.
    1.  **스케일 업 (Scale-Up):** Redis가 실행되는 서버의 RAM 용량을 늘린다.
    2.  **Redis 클러스터링 (Clustering):** 여러 서버에 Redis를 분산 설치하여 데이터를 자동으로 분산 저장(sharding)한다. 거의 무한대에 가깝게 수평적 확장이 가능하다.
    3.  **데이터 정책 (Data Eviction Policies):** 오랫동안 접속하지 않거나 비활성화된 기기의 상태 정보는 Redis에서 자동으로 삭제하고, 필요 시 더 느린 영구 저장소(PostgreSQL)에서 읽어오도록 정책을 설정할 수 있다.

## 8. 재해 복구: PKI 인증서 유출 시 대응 방안 (Disaster Recovery)

### 8.1. 기기/사용자 인증서 유출 시 (Device/User Certificate Compromise)
-   **상황:** 특정 기기나 사용자의 개인 키가 유출된 경우.
-   **대응:** 관리자가 Vault를 통해 해당 인증서를 즉시 **'폐기(Revoke)'**합니다.
-   **결과:** MQTT 브로커(EMQX)가 폐기 목록(CRL)을 주기적으로 확인하고, 해당 인증서를 사용하는 클라이언트의 연결을 강제로 끊습니다. 공격자는 더 이상 해당 인증서로 접속할 수 없습니다.

### 8.2. 중간 CA 인증서 유출 시 (Intermediate CA Compromise)
-   **상황:** 인증서 발급에 일상적으로 사용하는 중간 CA의 개인 키가 유출된 경우.
-   **대응:**
    1.  즉시 해당 중간 CA를 '폐기'합니다.
    2.  이 중간 CA가 발급했던 모든 기기/사용자/서버 인증서도 함께 폐기됩니다.
    3.  안전하게 보관된 루트 CA를 사용하여 **새로운 중간 CA를 발급**합니다.
    4.  새로운 중간 CA를 사용하여 모든 클라이언트(기기, 사용자, 서버)의 인증서를 재발급합니다.
-   **결과:** 피해 범위가 해당 중간 CA를 사용하던 시스템으로 한정됩니다. 루트 CA는 안전합니다.

### 8.3. 루트 CA 인증서 유출 시 (Root CA Compromise)
-   **상황:** 최상위 루트 CA의 개인 키가 유출된 최악의 시나리오.
-   **대응:**
    1.  기존 PKI 시스템 전체를 즉시 폐기합니다.
    2.  **완전히 새로운 루트 CA를 생성**합니다.
    3.  새로운 루트 CA로 새로운 중간 CA를 생성합니다.
    4.  새로운 중간 CA로 시스템의 **모든 인증서를 처음부터 다시 발급**합니다.
-   **결과:** 시스템 전체의 신뢰가 무너졌으므로, 신뢰 체계를 처음부터 다시 구축해야 합니다. 이것이 루트 CA를 오프라인으로 안전하게 보관하는 이유입니다.

### 8.4. 재배포/복구 구현을 위한 데이터 모델
인증서 폐기 후 안전한 재배포(복구) 절차를 지원하기 위해서는, 기기의 상태와 일회용 토큰을 관리할 수 있는 데이터베이스 필드가 필요하다.

-   **`Device` 모델 변경 사항:**
    1.  **`DeviceStatusEnum` 수정:** '복구 필요'를 의미하는 `RECOVERY_NEEDED` 상태를 `Enum`에 추가한다. 관리자가 인증서를 폐기하면, 서버는 해당 기기의 `status`를 이 값으로 변경한다.
    2.  **필드 추가:** `Device` 테이블에 다음 두 필드를 추가한다.
        -   `recovery_token: Optional[str]`: 사용자가 블루투스를 통한 복구 절차를 시작할 때 생성되는, 암호학적으로 안전한 일회용 토큰을 저장한다.
        -   `recovery_token_expires_at: Optional[datetime]`: 토큰의 유효 시간(예: 10분)을 저장하여, 시간 초과 공격을 방지한다.

-   **구현 절차:** 이 모델 변경을 적용하기 위해 새로운 Alembic 마이그레이션을 생성하고 실행해야 한다.

### 8.5. 유출 탐지 전략 (Compromise Detection Strategy)
-   **개요:** 유출 탐지는 단일 기능이 아닌, 여러 계층에서 이상 징후를 감시하는 '심층 방어(Defense in Depth)' 전략이 필요하다.
-   **1. 비정상 행위 탐지 (Anomalous Behavior Detection):** 애플리케이션 레벨에서 기기의 평소 행동 패턴에서 벗어나는 이상 징후를 탐지한다.
    -   **불가능한 이동 (Impossible Travel):** 단시간 내에 물리적으로 불가능한 두 지역에서 동일한 기기의 접속이 시도되는 경우.
    -   **비정상적 명령/데이터 (Unusual Commands/Data):** 평소와 다른 종류의 명령을 보내거나, 평소보다 과도한 양의 데이터를 전송하는 경우.
    -   **인증/검증 실패 급증:** 특정 기기에서만 HMAC 서명 검증 실패나 기타 인증 오류가 갑자기 많이 발생하는 경우.
-   **2. 인프라 및 접근 로그 감시 (Infrastructure & Access Log Monitoring):**
    -   **로그 중앙 관리:** 모든 시스템(Vault, EMQX, 서버, 방화벽)의 로그를 중앙에서 수집하고 분석하여 비정상적인 접근 시도를 탐지한다 (예: SIEM 시스템 사용).
    -   **Vault 감사 로그:** '누가 Vault의 민감한 경로에 접근했는가'를 기록하는 Vault의 감사 로그를 실시간으로 감시하는 것이 매우 중요하다.
-   **3. 외부 요인 (External Factors):**
    -   사용자가 '내 기기가 이상하게 동작한다'고 신고하는 경우.
    -   보안 전문가가 외부에 취약점을 제보하는 경우.

### 7.5. 유출 탐지 전략 (Compromise Detection Strategy)
-   **개요:** 유출 탐지는 단일 기능이 아닌, 여러 계층에서 이상 징후를 감시하는 '심층 방어(Defense in Depth)' 전략이 필요하다.
-   **1. 비정상 행위 탐지 (Anomalous Behavior Detection):** 애플리케이션 레벨에서 기기의 평소 행동 패턴에서 벗어나는 이상 징후를 탐지한다.
    -   **불가능한 이동 (Impossible Travel):** 단시간 내에 물리적으로 불가능한 두 지역에서 동일한 기기의 접속이 시도되는 경우.
    -   **비정상적 명령/데이터 (Unusual Commands/Data):** 평소와 다른 종류의 명령을 보내거나, 평소보다 과도한 양의 데이터를 전송하는 경우.
    -   **인증/검증 실패 급증:** 특정 기기에서만 HMAC 서명 검증 실패나 기타 인증 오류가 갑자기 많이 발생하는 경우.
-   **2. 인프라 및 접근 로그 감시 (Infrastructure & Access Log Monitoring):**
    -   **로그 중앙 관리:** 모든 시스템(Vault, EMQX, 서버, 방화벽)의 로그를 중앙에서 수집하고 분석하여 비정상적인 접근 시도를 탐지한다 (예: SIEM 시스템 사용).
    -   **Vault 감사 로그:** '누가 Vault의 민감한 경로에 접근했는가'를 기록하는 Vault의 감사 로그를 실시간으로 감시하는 것이 매우 중요하다.
-   **3. 외부 요인 (External Factors):**
    -   사용자가 '내 기기가 이상하게 동작한다'고 신고하는 경우.
    -   보안 전문가가 외부에 취약점을 제보하는 경우.
