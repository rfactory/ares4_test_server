# Ares4 서버 아키텍처 설계 문서 (v6.1)

## 1. 개요

이 문서는 Ares4 프로젝트의 서버 애플리케이션 아키텍처를 정의합니다. 이 설계는 초기 프로토타입을 넘어, 실제 운영 환경에서의 안정성, 확장성,
보안성을 목표로 합니다. 특히 v6.0에서는 **동적 부품 관리 모델**을 도입하여, 하드웨어 플랫폼과 연결된 부품 구성을 분리함으로써 시스템의 유연성과
확장성을 극대화합니다. GPU를 피하기 위해 AI/ML 관련 기능(예: anomaly detection)은 규칙 기반(rule-based) 또는 간단한 통계 처리(CPU-only)로
대체하며, 미래 AI 도입 시 별도 모듈로 플러그인 가능하도록 합니다.

## 2. 핵심 아키텍처

- **언어 및 프레임워크**: Python 3, FastAPI (API 서버), SQLAlchemy (ORM)
- **데이터 검증**: Pydantic
- **통신 프로토콜**: MQTT (paho-mqtt, **TLS 필수**, **클라이언트 인증서 기반 상호 TLS**), HTTP/S
- **데이터베이스**: PostgreSQL + TimescaleDB (SQLAlchemy ORM에서 `joinedload`와 같은 기법을 사용하여 성능 최적화)
- **상태 관리**: Redis (각 기기의 최신 상태 캐시 및 **Redis Sorted Set을 활용한 효율적인 장치 헬스 체크/타임아웃 관리**)
- **설정 관리**: 환경 변수(`APP_ENV`)를 통해 개발(`local`)과 운영(`prod`) 환경을 분리하여 관리합니다. 각 환경에 맞는 설정 파일(
  `config/local.yaml`, `config/prod.yaml`)을 사용하며, `settings.py` 모듈이 이를 동적으로 로드합니다. 특히 로컬 개발 환경에서는 프로젝트 루트의 `.env` 파일에 환경 변수를 정의하고 `python-dotenv` 라이브러리를 통해 이를 로드하여 사용의 편의성을 높입니다.
- **이메일 전송**: `fastapi-mail` 라이브러리를 사용하여 비밀번호 재설정 등 비동기 이메일 전송.
- **외부 HTTP 요청**: `requests` 라이브러리를 사용하여 외부 서비스와의 연동 및 타사 API 호출.
- **보안 강화**: **HMAC 기반 메시지 무결성 검증**, **장치별 클라이언트 인증서 생성 및 관리**, **역할 기반 접근 제어 (RBAC)**

## 3. 실행 아키텍처

서버 시스템은 2개의 독립적인 프로세스로 구성됩니다.

- **프로세스 1: API 서버 (FastAPI + Uvicorn)**
  - **역할**: 사용자 인증 (**비밀번호 재설정 포함**), 기기 (**사전 등록, 클레임, 자격 증명 발급 포함**), **지원 부품 및 핀 규칙 관리**, **연결된 부품 관리**, 데이터 조회 등 클라이언트의 HTTP 요청을 처리합니다. **장치별 클라이언트 인증서 생성 및 관리** 기능을 포함합니다.

- **프로세스 2: 상태 관리 및 데이터 수집기 (범용 MQTT 리스너)**
  - **역할**: MQTT 브로커와 통신하며, **HMAC 검증을 통한 메시지 무결성 확인**, **특정 부품 종류에 의존하지 않는** 범용적인 데이터 수집 및 상태 전파를 담당합니다. 수신된 텔레메트리 페이로드 중 CPU 데이터(`cpu_average`, `cpu_peak`)를 Redis에 평탄화하여 저장하고, `led`, `pump`와 같은 특정 컴포넌트의 `status`를 직접 Redis 키로 매핑하는 등 상세 처리 로직을 포함합니다. **Redis Sorted Set을 활용하여 실시간 장치 상태 캐싱 및 효율적인 장치 헬스 체크/타임아웃 모니터링** 기능을 포함합니다. 세부 동작은 4장에서 기술합니다.
## 4. 통신 아키텍처 (v6 - 동적 부품 모델)

v6 아키텍처는 서버가 '진실의 원천(Source of Truth)'이 되는 v5의 Push 모델을 계승하면서, 라즈베리파이 기기가 자신의 부품 구성을 서버에 묻고 동적으로 동작하는 유연한 구조를 채택합니다.

### 4.1. 라즈베리파이 클라이언트 동작

1.  **부팅 및 인증**: 기기가 부팅되고, 서버에 자신을 인증합니다.
2.  **부품 목록 조회**: 서버의 신규 API(`GET /api/components/devices/{id}/components`)를 호출하여, 자신에게 연결되도록 등록된 부품의 목록을 받아옵니다.
3.  **동적 드라이버 로딩**: 조회한 부품 목록을 기반으로, 필요한 하드웨어 드라이버(센서, 액추에이터)만 동적으로 로드하고 실행합니다.
4.  **MQTT 데이터 발행**: 활성화된 부품들로부터 데이터를 읽어, 개선된 토픽 구조에 따라 MQTT 브로커로 발행합니다.
5.  **서버 측 데이터 무결성 검사**: MQTT 리스너는 수신된 텔레메트리 메시지에 대해 `hardware_variant` 일치 여부, `device_pin_configs`에 정의된 `component_type` 유효성, 그리고 `attached_components`에 해당 부품이 실제로 연결되어 있는지 등을 확인하여 데이터의 신뢰성을 확보합니다.

### 4.2. MQTT 토픽 구조 (개선안)

- **기기 -> 서버 (데이터 보고)**
  - `telemetry/{user_email}/{device_uuid}/{component_type}/status`
  - **목적**: 기기가 자신의 부품(`component_type`) 상태를 보고합니다. 이를 통해 서버 리스너는 어떤 종류의 부품인지 동적으로 파악할 수 있습니다.

- **서버 -> 클라이언트 (상태 전파)**
  - `client/state/{user_email}/{device_uuid}`
  - **목적**: 서버가 특정 기기의 최신 상태 모음을 클라이언트에게 Push하는 전용 토픽입니다.
  - **페이로드 예시**:
    {
      "device_status": "ONLINE",
      "led": "ON",
      "pump": "OFF",
      "dht22_temp": 25.5,
      "dht22_humidity": 45.1
    }

- **클라이언트 -> 서버 (상태 요청)**
  - `client/request_state/{user_email}/{device_uuid}`
  - **목적**: 앱이 서버에게 최신 상태를 요청하는 전용 토픽입니다.

### 4.3. 상태 동기화 시나리오

1.  **앱 시작/로그인**: Flutter 앱이 로그인에 성공하고 `DeviceService`가 특정 기기를 선택합니다.
2.  **MQTT 연결 및 구독**: `DeviceService`는 MQTT 브로커에 연결하고, 자신이 담당할 기기의 상태 전파 토픽(`client/state/...`)을 구독합니다.
3.  **초기 상태 요청**: 구독 성공 후, `DeviceService`는 상태 요청 토픽(`client/request_state/...`)으로 메시지를 발행합니다.
4.  **서버 응답 (Push)**: MQTT 리스너는 상태 요청을 받고, Redis에 캐시된 해당 기기의 최신 상태 전체를 상태 전파 토픽(`client/state/...`)으로 발행합니다.
5.  **앱 UI 업데이트**: `DeviceService`는 상태 전파 토픽으로 들어온 최신 상태 메시지를 수신하여, **메시지 내용에 따라 동적으로** 관련 변수(led 상태, 펌프 상태, 온도 등)를 업데이트하고, `notifyListeners()`를 호출하여 화면 전체를 한 번에 갱신합니다.
6.  **실시간 변경 (기기 -> 앱)**: 라즈베리파이에서 `telemetry/.../led/status` 토픽으로 새로운 상태를 보내면, **범용 리스너**가 이를 처리하여 캐시를 업데이트하고, 다시 상태 전파 토픽(`client/state/...`)으로 변경된 상태 전체를 Push하여 앱에 실시간으로 반영됩니다.
7.  **실시간 변경 (타임아웃)**: 서버 리스너의 백그라운드 타이머가 특정 기기의 응답 없음을 감지하면, 해당 기기의 상태 캐시를 `"device_status": "Timeout"`으로 변경하고, 이 변경 사항을 즉시 상태 전파 토픽으로 Push하여 앱에 실시간으로 반영합니다.

### 4.4. 핵심 원칙: 서버는 진실의 원천 (Single Source of Truth)

이 시스템의 모든 상태 정보는 서버의 데이터베이스가 최종 권한을 갖는 '진실의 원천'입니다. 라즈베리파이나 Flutter 앱이 가진 상태 정보(예: 기기에 저장된 `user_id`, 앱에 표시되는 LED 상태)는 모두 서버 정보의 '사본' 또는 '캐시'에 해당합니다.

따라서, 기기나 앱은 자신의 로컬 상태가 서버의 상태와 일치하는지 주기적으로 확인받거나, 서버로부터 상태 변경을 통보받아야 합니다. 이 단방향 신뢰 구조는 시스템 전체의 데이터 흐름을 예측 가능하고 안정적으로 만듭니다.

### 4.5. MQTT 연결 상태 감지 강화 (Keep-Alive & LWT)

기기의 연결 상태를 보다 빠르고 정확하게 감지하기 위해 MQTT 프로토콜의 Keep-Alive 및 LWT(Last Will and Testament) 기능을 활용합니다. 이는 
기존 Redis 기반의 애플리케이션 레벨 활성 상태 체크와 상호 보완적인 역할을 합니다.

*   **Keep-Alive**:
    *   **역할**: MQTT 클라이언트와 브로커 간의 네트워크 연결 자체의 생존 여부를 확인합니다. 클라이언트가 일정 시간(Keep-Alive 간격) 동안
데이터 메시지를 보내지 않을 경우, 클라이언트는 작은 `PINGREQ` 패킷을 브로커에게 보내 연결이 살아있음을 알립니다. 브로커는 Keep-Alive 간격의 
1.5배 시간 동안 클라이언트로부터 아무 패킷도 받지 못하면 연결이 끊긴 것으로 간주합니다.
    *   **기여**: 네트워크 수준의 연결 단절을 빠르게 감지하며, LWT 메시지가 제때 발행되도록 하는 기반이 됩니다.

*   **LWT (Last Will and Testament)**:
    *   **역할**: 클라이언트가 브로커에 연결할 때 미리 "유언 메시지"를 등록합니다. 클라이언트가 `DISCONNECT` 패킷을 보내지 않고 예기치 
않게 연결이 끊어질 경우(예: 전원 차단, 네트워크 단절, 클라이언트 앱 크래시), 브로커가 이 LWT 메시지를 미리 약속된 토픽으로 자동으로 발행합니다.
    *   **기여**: 예기치 않은 네트워크 연결 끊김을 거의 즉시 서버에 알림으로써, 서버가 기기의 상태를 "OFFLINE" 등으로 빠르게 업데이트할 
수 있게 합니다.

*   **Redis 기반 타임아웃 체크 (Sorted Set 최적화)와의 시너지**:
    *   **LWT/Keep-Alive**: 주로 **네트워크 연결 수준의 단절**을 감지합니다.
    *   **Redis Sorted Set 기반 타임아웃**: 네트워크 연결은 살아있지만 기기 내부 애플리케이션이 텔레메트리 데이터를 보내지 않는 **애플리케이션 
레벨의 비활성 상태**를 감지합니다. 기존의 `KEYS` 명령을 사용한 전체 스캔 방식 대신, Redis Sorted Set(`device_last_seen_zset`)에 기기의 `device_uuid`와 마지막 활동 시간(스코어)을 저장합니다. 헬스 체크 시에는 `ZRANGEBYSCORE` 명령을 사용하여 타임아웃 임계값보다 낮은 스코어를 가진 기기들(즉, 마지막 활동 시간이 오래된 기기들)을 효율적으로 조회합니다. 이 방식은 기기 수가 많아질수록 서버의 부하를 크게 줄여줍니다.
    *   이 세 가지 메커니즘을 함께 사용함으로써, 시스템은 네트워크 문제부터 기기 애플리케이션의 오작동까지 다양한 상황에서 기기의 상태를 
빠르고 정확하게 파악하고 대응할 수 있습니다.

## 5. API 엔드포인트 명세 (v6.1)

*참고: API의 실제 구현은 유지보수성을 위해 `server/app/api/routes/` 디렉토리 아래에 `auth.py`, `devices.py`, `components.py` 등 기능별 파일로 모듈화되어 있습니다.*

- **`GET /healthz`**: 서버가 정상적으로 실행 중이며 데이터베이스에 연결할 수 있는지 확인하는 표준 헬스 체크 엔드포인트입니다. 성공 시 `{"status": "ok", "database": "ok"}`와 같은 JSON을 반환합니다.
- **`GET /`**: 서버가 실행 중임을 알리는 간단한 상태 메시지를 반환합니다.

### 5.1. 인증
- **`POST /auth/register`**: 새로운 사용자 계정을 생성합니다.
- **`POST /auth/login`**: 이메일과 비밀번호로 사용자를 인증하고, API 접근을 위한 JWT를 발급합니다.
- **`POST /auth/forgot-password`**: 사용자 이메일로 6자리 비밀번호 재설정 코드를 발송합니다. 코드는 10분 동안 유효합니다.
- **`POST /auth/reset-password`**: 유효한 임시 토큰과 새로운 비밀번호를 사용하여 비밀번호를 재설정합니다.

### 5.2. 기기 관리
- **`GET /api/devices`**: 현재 로그인된 사용자의 계정에 등록된 모든 기기(`Device`)의 목록을 조회합니다.
- **`PUT /api/devices/{device_id}/nickname`**: 특정 기기(`device_id`)에 대해 사용자가 지정한 별명을 수정합니다.
- **`DELETE /api/devices/{device_id}`**: 특정 기기(`device_id`)를 현재 사용자 계정에서 연결 해제합니다.

### 5.3. 데이터 조회 및 명령
- **`GET /api/devices/{device_id}/telemetry`**: 특정 기기(`device_id`)의 원격 측정 데이터(telemetry)를 필터링하여 조회합니다.
- **`POST /api/devices/{device_id}/command`**: 특정 기기(`device_id`)에 제어 명령(예: LED 켜기)을 전송합니다.
- **`POST /api/devices/{device_id}/change-wifi`**: 특정 기기(`device_id`)의 Wi-Fi 연결 정보를 변경하도록 명령합니다.

### 5.4. 사용자 관리
- **`DELETE /api/users/me`**: 현재 인증된 사용자(본인)의 계정을 삭제합니다.

### 5.5. 지원 부품 및 핀 규칙 관리
- **`GET /api/components`**: 시스템이 지원하는 모든 부품의 목록('카탈로그')을 조회합니다.
- **`POST /api/components`**: 시스템에 새로운 지원 부품을 추가합니다. (관리자용)
- **`PUT /api/components/{component_type}`**: 기존 지원 부품의 정보를 수정합니다. (관리자용)
- **`DELETE /api/components/{component_type}`**: 기존 지원 부품을 삭제합니다. (관리자용)
- **`GET /api/device-configs/{hardware_version}`**: 특정 하드웨어 버전에 대해 정의된 모든 핀 설정 '규칙'의 목록을 조회합니다.
- **`POST /api/device-configs`**: 새로운 핀 설정 '규칙'을 시스템에 추가합니다. (관리자용)
- **`PUT /api/device-configs/{config_id}`**: 기존의 특정 핀 설정 '규칙'(`config_id`)의 내용을 수정합니다. (관리자용)
- **`DELETE /api/device-configs/{config_id}`**: 기존의 특정 핀 설정 '규칙'(`config_id`)을 시스템에서 삭제합니다. (관리자용)

### 5.6. 연결된 부품 관리
- **`GET /api/components/devices/{device_id}/components`**: 특정 기기(`device_id`)에 현재 연결되어 있는 모든 부품의 목록을 조회합니다. (기기 부팅 시 사용)
- **`POST /api/components/devices/{device_id}/components`**: 해당 기기(`device_id`)에 새로운 부품이 연결되었음을 등록합니다.
- **`DELETE /api/components/devices/{device_id}/components/{component_id}`**: 해당 기기에서 특정 부품(`component_id`)의 연결을 해제(삭제)합니다.

### 5.7. 기기 프로비저닝
- **`POST /api/devices/preregister`**: 관리자가 기기의 `cpu_serial`을 사용하여 시스템에 기기를 사전 등록합니다. (관리자용)
- **`POST /api/devices/claim`**: 사용자가 기기의 소유권을 주장(claim)하여 자신의 계정에 등록합니다.
- **`POST /api/devices/credentials`**: 프로비저닝 과정에서 기기가 자신의 자격증명(예: `shared_secret`)을 서버에 요청하기 위해 호출하는 엔드포인트입니다.

### 5.8. OTA 업데이트 (신규)
- **`POST /api/updates`**: (관리자용) 새로운 펌웨어 업데이트 버전과 패키지 파일을 등록합니다.
- **`GET /api/updates/latest`**: 기기가 사용 가능한 최신 업데이트 정보를 조회합니다.
- **`POST /api/devices/{device_id}/ota-trigger`**: 특정 기기에 대해 OTA 업데이트 프로세스를 시작하도록 명령합니다.

## 6. 데이터베이스 스키마

-
- **ORM**: SQLAlchemy
- **마이그레이션**: Alembic
  - 또한, `sqlalchemy_utils` 라이브러리를 사용하여 마이그레이션 실행 전에 데이터베이스의 존재 여부를 확인하고 필요 시 자동으로 생성합니다.

#### 6.1. `users` 테이블
| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | `integer` | PK, NOT NULL | 사용자 고유 ID |
| `username` | `character varying` | NOT NULL | 사용자 이름 |
| `email` | `character varying` | NOT NULL | 이메일 주소 |
| `password_hash` | `character varying` | NOT NULL | 해시된 비밀번호 |
| `created_at` | `timestamp with time zone` | | 계정 생성일 |
| `reset_token` | `character varying` | NULLABLE | 비밀번호 재설정 토큰 |
| `reset_token_expires_at` | `timestamp with time zone` | NULLABLE | 토큰 만료 시간 |
| `shared_secret` | `character varying` | NULLABLE | 기기와의 HMAC 통신을 위한 공유 비밀키 |
| `last_login` | `timestamp with time zone` | NULLABLE | 마지막 로그인 시간 |
| `is_active` | `boolean` | NOT NULL | 계정 활성 상태 |
| `email_verification_token` | `character varying` | NULLABLE | 이메일 인증 토큰 |
| `email_verification_token_expires_at` | `timestamp with time zone` | NULLABLE | 이메일 인증 토큰 만료 시간 |
| `is_staff` | `boolean` | NOT NULL | 관리자 패널 접근 가능 여부 |
| `is_superuser` | `boolean` | NOT NULL | 최고 관리자 권한 여부 |

#### 6.2. `devices` 테이블
| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | `integer` | PK, NOT NULL | 기기 고유 ID |
| `cpu_serial` | `character varying` | NOT NULL | 기기 물리적 식별자 |
| `current_uuid` | `uuid` | NOT NULL | 마지막으로 보고된 논리적 식별자 |
| `created_at` | `timestamp with time zone` | NULLABLE | 처음 등록된 시간 |
| `last_seen_at` | `timestamp with time zone` | NULLABLE | 마지막 활동 시간 (레코드 업데이트 시 자동 갱신) |
| `hardware_version` | `character varying` | NOT NULL | **라즈베리파이 보드 모델** (예: '4B', '5') |
| `device_certificate` | `text` | NULLABLE | 기기 전용 클라이언트 인증서 |
| `device_private_key` | `text` | NULLABLE | 기기 전용 개인 키 |
| `ca_certificate` | `text` | NULLABLE | 기기 인증서를 서명한 CA 인증서 |
| `hardware_variant_id` | `integer` | FK, NOT NULL | 하드웨어 변형 ID (hardware_variants.id 참조) |
| `hardware_variant` | `character varying` | NOT NULL | **하드웨어 변형** (예: 'Pro', 'Standard') |

#### 6.3. `attached_components` 테이블
| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | `integer` | PK, NOT NULL | 부품 연결 고유 ID |
| `device_id` | `integer` | NOT NULL | 어떤 기기에 연결되었는지 |
| `component_type` | `character varying` | NOT NULL | 부품 종류 |
| `name` | `character varying` | NULLABLE | 사용자가 붙인 부품 별명 (예: "메인 펌프") |
| `pin_number` | `integer` | NULLABLE | 실제 GPIO 핀 번호 |
| `pin_mode` | `character varying` | NULLABLE | 핀 모드 (예: 'OUT', 'IN', 'PWM') |
| `default_state` | `character varying` | NULLABLE | 기본 상태 (예: 'HIGH', 'LOW', 'ON', 'OFF') |

#### 6.4. `device_pin_configs` 테이블
| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | `integer` | PK, NOT NULL | 설정 고유 ID |
| `hardware_version` | `character varying` | NOT NULL | 어떤 하드웨어 버전에 대한 설정인지 |
| `component_type` | `character varying` | NOT NULL | 컴포넌트 종류 |
| `pin_number` | `integer` | NOT NULL | 실제 GPIO 핀 번호 |
| `pin_mode` | `character varying` | NULLABLE | 핀 모드 (예: 'OUT', 'IN', 'PWM') |
| `default_state` | `character varying` | NULLABLE | 기본 상태 (예: 'HIGH', 'LOW', 'ON', 'OFF') |
| `description` | `text` | NULLABLE | 핀 설정에 대한 설명 |
| `hardware_variant` | `character varying` | NOT NULL | 하드웨어 변형 (예: 'Pro', 'Standard') |

#### 6.5. `firmware_updates` 테이블
| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | `integer` | PK, NOT NULL | 펌웨어 업데이트 고유 ID |
| `version` | `character varying` | NOT NULL | 펌웨어 버전 문자열 (예: '1.2.3') |
| `package_url` | `text` | NOT NULL | 업데이트 패키지 파일의 다운로드 URL |
| `package_hash` | `character varying` | NOT NULL | 파일 무결성 검증을 위한 해시값 (SHA256) |
| `release_date` | `timestamp with time zone` | NULLABLE | 펌웨어 출시일 |
| `description` | `text` | NULLABLE | 해당 업데이트에 대한 설명 |

#### 6.6. `roles` 테이블
| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | `integer` | PK, NOT NULL | 역할 고유 ID |
| `name` | `character varying` | NOT NULL | 역할 이름 (예: 'prime_admin', 'general_admin', 'owner', 'viewer', 'developer') |
| `description` | `text` | NULLABLE | 역할에 대한 설명 |

#### 6.7. `supported_components` 테이블
| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | `integer` | PK, NOT NULL | 부품 고유 ID |
| `component_type` | `character varying` | NOT NULL | 부품의 고유 타입 식별자 (예: 'dht22', 'pump', 'cpu_temp') |
| `display_name` | `character varying` | NOT NULL | 사용자에게 보여줄 이름 (예: "온습도 센서", "워터 펌프") |
| `category` | `character varying` | NOT NULL | 부품 분류 (예: 'sensor', 'actuator', 'internal_module') |
| `description` | `text` | NULLABLE | 부품에 대한 상세 설명 |
| `component_metadata` | `json` | NULLABLE | 추가 정보 (예: 아이콘 이름, 데이터 단위(°C, %), 기본 설정값 등) |
| `telemetry_category` | `character varying` | NULLABLE | 텔레메트리 데이터 분류 (예: 'temperature', 'humidity', 'status') |

#### 6.8. `telemetry_data` 테이블
| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | `bigint` | PK, NOT NULL | 텔레메트리 데이터 고유 ID |
| `timestamp` | `timestamp with time zone` | NOT NULL | 데이터 생성 시간 |
| `received_at` | `timestamp with time zone` | NULLABLE | 서버 수신 시간 |
| `device_id` | `integer` | NULLABLE | 기기 ID |
| `topic` | `character varying` | NULLABLE | MQTT 토픽 |
| `payload` | `json` | NULLABLE | 데이터 페이로드 |

#### 6.9. `user_devices` 테이블
| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `user_id` | `integer` | NOT NULL | 사용자 ID |
| `device_id` | `integer` | NOT NULL | 기기 ID |
| `role` | `character varying` | NOT NULL | 사용자의 기기에 대한 역할 |
| `nickname` | `character varying` | NULLABLE | 기기 별명 |
| `id` | `integer` | PK, NOT NULL | 연결 고유 ID |

#### 6.10. `user_roles` 테이블
| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | `integer` | PK, NOT NULL | 사용자-역할 연결 고유 ID |
| `user_id` | `integer` | NOT NULL | 사용자 ID |
| `role_id` | `integer` | NOT NULL | 역할 ID |

#### 6.11. `alembic_version` 테이블
| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `version_num` | `character varying` | NOT NULL | Alembic 마이그레이션 버전 |

#### 6.12. Django 및 인증 테이블
*참고: 아래 테이블들은 `server` 애플리케이션의 핵심 로직에는 사용되지 않으나, `admin_panel`을 실행하는 과정에서 Django가 자체적인 기능(세션, 관리자 로그, 권한 관리 등)을 위해 자동으로 생성하고 사용하는 테이블들입니다.*

- **`auth_group`**: 권한들의 묶음인 그룹 정보.
- **`auth_group_permissions`**: 그룹과 권한의 연결 정보.
- **`auth_permission`**: 모델별 기본 권한('add', 'change', 'view', 'delete') 목록.
- **`django_admin_log`**: 어드민 패널에서의 모든 관리자 활동 기록.
- **`django_content_type`**: 시스템에 등록된 모든 모델의 정보를 관리.
- **`django_migrations`**: Django 마이그레이션 적용 상태 기록.
- **`django_session`**: 어드민 패널 로그인 세션 정보 저장.

#### 6.13. `hardware_variants` 테이블
| 컬럼명 | 데이터 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| `id` | `integer` | PK, NOT NULL | 하드웨어 변형 고유 ID |
| `name` | `character varying` | NOT NULL | 변형 이름 (예: 'Standard', 'Pro') |
| `description` | `text` | NULLABLE | 변형에 대한 설명 |


## 7. 보안 강화 전략

- **MQTT 통신 TLS 암호화**: MQTT 브로커와의 모든 통신은 TLS를 통해 암호화되어야 합니다. 서버는 브로커의 인증서를 검증하고, 상호 TLS(Mutual TLS)를 위해 자체 클라이언트 인증서를 브로커에 제시하여 서버의 신원을 인증합니다. `settings.py`에 정의된 TLS 관련 설정(`mqtt.tls_enabled`, `mqtt.ca_certs`, `mqtt.client_cert`, `mqtt.client_key`)을 활용합니다.
- **API 인증**: JWT 기반 인증. 모든 보호된 API는 Access Token을 검증합니다.
- **비밀번호 해싱**: `bcrypt` 라이브러리를 사용하여 안전하게 해시하여 저장합니다.
- **역할 기반 접근 제어 (RBAC)**: `RoleChecker` 의존성을 통해 API 엔드포인트에 대한 접근을 제어합니다. 사용자에게 할당된 역할('prime_admin', 'general_admin', 'developer', 'owner' 등)을 기반으로 특정 API의 사용 권한을 검사하여, 인가되지 않은 요청을 차단합니다.
  - **MQTT 접근 제어 (ACL)**: 개인 MQTT 브로커 운영 시, ACL(Access Control List)을 적용하여 각 사용자/기기가 허가된 토픽에만 접근할 수 있도록 제어합니다. **이는 브로커 수준에서 설정되어야 하는 중요한 보안 요소입니다.** `mosquitto.conf` 파일에서 `acl_file` 지시어를 통해 `acl.conf` 파일을 참조합니다. **클라이언트 인증은 비밀번호 대신 클라이언트 인증서 기반 상호 TLS(Mutual TLS)를 사용하며, `mosquitto_passwd` 파일은 클라이언트 인증 목적으로 사용되지 않습니다.**- **데이터 유효성 검사**: Pydantic을 사용하여 모든 API 요청/응답 데이터의 형식을 엄격하게 검증합니다.
- **메시지 무결성 검증 (HMAC)**: 기기에서 발행되는 모든 MQTT 텔레메트리 메시지에는 HMAC 서명이 포함됩니다. 서버의 MQTT 리스너는 메시지 수신 시 다음 절차에 따라 서명을 검증하여 메시지가 신뢰할 수 있는 기기로부터 왔으며, 전송 중에 위변조되지 않았음을 보장합니다.
  1.  **토픽 분석**: 수신된 메시지의 토픽(`telemetry/{user_email}/{device_uuid}/...`)에서 `user_email`을 추출합니다.
  2.  **공유 비밀키 조회**: `user_email`을 기반으로 `users` 테이블에서 해당 사용자의 `shared_secret`을 조회합니다.
  3.  **서명 재현**: 수신한 페이로드(HMAC 필드 제외)와 타임스탬프를 사용하여 클라이언트와 동일한 방식으로 Canonical String을 생성하고, 조회한 공유 비밀키로 HMAC 서명을 직접 계산합니다.
  4.  **서명 비교**: 직접 계산한 서명과 메시지에 포함된 서명이 일치하는지 비교합니다.
  5.  **처리 결정**: 서명이 일치하면 메시지를 처리하고, 일치하지 않으면 해당 메시지를 폐기하고 보안 경고 로그를 기록합니다. 이 메커니즘은 재전송 공격(Replay Attack)과 메시지 위변조를 효과적으로 방지합니다.

### 7.1. 프로덕션 론칭을 위한 추가 보안 고려 사항

현재 시스템은 클라이언트 인증서 기반 상호 TLS(Mutual TLS) 인증을 사용하여 강력한 보안 기반을 제공하지만, 실제 프로덕션 론칭을 위해서는 다음 사항들을 반드시 해결해야 합니다.

*   **Flutter 앱을 위한 고유 클라이언트 인증서**: 현재 모든 Flutter 앱 인스턴스가 동일한 클라이언트 인증서를 사용하는 것은 심각한 보안 취약점입니다. 각 사용자 또는 앱 인스턴스에 고유한 클라이언트 인증서를 발급하고 안전하게 프로비저닝하는 시스템을 구축해야 합니다.
*   **TLS 호스트네임 검증 활성화**: 개발 편의를 위해 `MQTT_TLS_INSECURE=True`와 같이 TLS 호스트네임 검증을 우회하는 설정은 중간자 공격(MITM)에 취약합니다. 프로덕션 환경에서는 이 설정을 반드시 `False`로 변경하고, Flutter 앱에서도 호스트네임 검증을 활성화해야 합니다.
*   **Python 클라이언트의 안전한 자격 증명 관리**: FastAPI 서버, MQTT 리스너 등 Python 클라이언트가 사용하는 공유된 자격 증명(예: `.env` 파일의 `MQTT_USER`, `MQTT_PASSWORD`)은 유출 시 위험합니다. 각 구성 요소에 고유하고 강력한 자격 증명을 사용하고, 이를 환경 변수, Docker Secrets, Kubernetes Secrets 또는 클라우드 기반 비밀 관리 서비스(예: AWS Secrets Manager)를 통해 안전하게 관리해야 합니다.

## 8. 프로덕션 배포를 위한 보안 고려 사항 (Security Considerations for Production Deployment)

이 섹션에서는 Ares4 시스템을 프로덕션 환경에 배포하기 전에 반드시 고려해야 할 보안 관련 사항들을 다룹니다. 현재 개발 환경 설정은 기능 검증에 중점을 두었으므로, 실제 서비스 운영을 위해서는 추가적인 보안 강화 조치가 필수적입니다.

### 8.1. MQTT 클라이언트 인증서 관리

-   **현재 문제점**: Flutter 앱은 현재 모든 인스턴스가 동일한 클라이언트 인증서(`flutter_client.crt`, `flutter_client.key`)를 사용하도록 설정되어 있습니다. 이는 개발 및 테스트에는 편리하지만, 프로덕션 환경에서는 심각한 보안 취약점입니다.
-   **보안 위협**: 만약 단 하나의 Flutter 앱 인스턴스라도 클라이언트 인증서와 개인 키가 유출되면, 공격자는 이 정보를 사용하여 시스템에 연결된 **모든 Flutter 앱 사용자를 가장할 수 있습니다.** 이는 클라이언트 인증서 기반 인증의 목적을 완전히 무력화시킵니다.
-   **프로덕션 해결책**:
    1.  **고유 인증서 발급**: 각 사용자 또는 기기(Flutter 앱 인스턴스)는 회원가입 또는 기기 등록 시 서버로부터 **고유한 클라이언트 인증서와 개인 키**를 발급받아야 합니다. 서버는 이 인증서의 Common Name(CN)을 해당 사용자 또는 기기의 고유 식별자(예: `user_email` 또는 `device_uuid`)로 설정하여 MQTT 브로커에서 사용자/기기별 ACL 적용에 활용합니다.
    2.  **안전한 프로비저닝**: 발급된 인증서와 개인 키는 앱 설치 시 또는 첫 로그인 시점에 기기에 안전하게 전달(프로비저닝)되어야 합니다. 개인 키는 절대로 기기 외부로 유출되어서는 안 되며, 기기 내 안전한 저장소(예: 키체인, Secure Storage)에 보관되어야 합니다.
    3.  **인증서 폐기 및 갱신**: 계정 탈퇴 또는 기기 등록 해제 시, 서버는 해당 클라이언트 인증서를 무효화(폐기)하고, 앱은 기기에 저장된 인증서를 삭제해야 합니다. 또한, 인증서 만료 전에 갱신하는 시스템을 구축해야 합니다.

### 8.2. TLS 호스트네임 검증 (`MQTT_TLS_INSECURE` 비활성화)

-   **현재 문제점**: 개발 환경에서는 편의를 위해 Python 클라이언트(`MQTT_TLS_INSECURE=True`)와 Flutter 클라이언트(`onBadCertificate = (dynamic a) => true`) 모두 TLS 호스트네임 검증을 우회하도록 설정되어 있습니다.
-   **보안 위협**: 이 설정은 중간자 공격(Man-in-the-Middle, MITM)에 앱을 취약하게 만듭니다. 공격자가 가짜 MQTT 브로커를 운영하며 유효해 보이는 인증서를 제시할 경우, 클라이언트는 이를 신뢰하고 연결하여 통신 내용을 도청하거나 변조할 수 있습니다.
-   **프로덕션 해결책**: 프로덕션 환경에서는 `MQTT_TLS_INSECURE` 설정을 **반드시 `False`로 변경**하고, Flutter 앱에서도 `onBadCertificate` 콜백을 제거해야 합니다. 이를 위해서는 Mosquitto 브로커의 서버 인증서(`mosquitto_server.crt`)가 클라이언트가 연결하는 **브로커의 실제 호스트네임 또는 IP 주소와 일치하는 Common Name(CN) 또는 Subject Alternative Name(SAN)**을 포함해야 합니다.

### 8.3. 자격 증명 및 비밀 정보 관리

-   **현재 문제점**: Python 클라이언트(FastAPI 서버, MQTT 리스너, Mock 센서 발생기)는 `.env` 파일에 정의된 `MQTT_USER`, `MQTT_PASSWORD`와 같은 공유된 자격 증명을 사용합니다.
-   **보안 위협**: 이러한 공유된 비밀 정보가 유출될 경우, 시스템의 여러 구성 요소가 동시에 위험에 노출될 수 있습니다.
-   **프로덕션 해결책**: 각 구성 요소에 대해 고유하고 강력한 자격 증명을 사용하고, 이를 환경 변수, Docker Secrets, Kubernetes Secrets 또는 클라우드 기반 비밀 관리 서비스(예: AWS Secrets Manager, Google Secret Manager)를 통해 안전하게 관리해야 합니다.

### 8.4. 기타 프로덕션 고려 사항

-   **보안 감사 및 침투 테스트**: 정기적인 보안 감사 및 침투 테스트를 통해 시스템의 취약점을 식별하고 개선해야 합니다.
-   **로깅 및 모니터링**: 모든 보안 관련 이벤트(인증 실패, 비정상적인 접근 시도 등)를 기록하고, 실시간 모니터링 및 알림 시스템을 구축하여 신속하게 대응할 수 있도록 해야 합니다.
-   **확장성 및 고가용성**: 단일 장애 지점(Single Point of Failure)을 제거하고, 로드 밸런싱, 클러스터링, 데이터베이스 복제 등을 통해 시스템의 확장성과 고가용성을 확보해야 합니다.
-   **코드 보안**: 정적/동적 코드 분석 도구를 사용하여 코드의 보안 취약점을 지속적으로 검사하고 수정해야 합니다.

이러한 고려 사항들을 바탕으로 프로덕션 환경에 맞는 보안 아키텍처를 설계하고 구현하는 것이 중요합니다.

## 9. 기기 프로비저닝 아키텍처 (하이브리드 모델)

기기의 초기 설정을 위해, 관리자의 편의성과 사용자의 경험을 모두 만족시키는 하이브리드 프로비저닝 모델을 채택합니다.

### 9.1. 주요 흐름

1.  **[관리자] 기기 사전 등록**: 관리자는 서버의 API 또는 관리자 도구를 사용하여 새 기기의 물리적 식별자(예: `cpu_serial`)를 `devices` 테이블에 미리 등록합니다. 이 시점의 기기는 "등록됨(Registered)" 상태이지만, 아직 특정 사용자에게 "할당되지 않음(Unassigned)" 상태입니다.

2.  **[사용자] 기기 수령 및 전원 연결**: 사용자는 관리자로부터 기기를 받아 전원을 연결합니다. 기기는 부팅 후, 자신이 아직 특정 사용자에게 할당되지 않았음을 인지하고 블루투스(BLE) 페어링 대기 모드로 진입합니다.

3.  **[앱] 블루투스를 통한 기기 탐색 및 연결**: 사용자가 Flutter 앱의 "새 기기 추가" 기능을 실행하면, 앱은 블루투스 스캔을 통해 주변에 있는 프로비저닝 대기 상태의 기기를 찾습니다. 사용자가 목록에서 자신의 기기를 선택하면 앱과 기기는 블루투스로 연결됩니다.

4.  **[앱/기기] 기기 소유권 주장(Claim) 준비**: 블루투스로 연결이 완료되면, 기기는 자신의 물리적 식별자(`cpu_serial`)를 앱에게 안전하게 전송합니다.

5.  **[앱/서버] 소유권 주장 요청**: 앱은 현재 로그인된 사용자의 인증 정보(JWT)와 기기로부터 받은 `cpu_serial`을 함께 서버의 `POST /api/devices/claim` 엔드포인트로 전송합니다.
    *   **[서버] Wi-Fi 변경 명령 중계**: 사용자가 Flutter 앱을 통해 Wi-Fi 변경을 요청할 경우, 앱은 새로운 Wi-Fi 정보를 서버의 특정 API로 전송합니다. 서버는 이 정보를 포함하는 MQTT 명령을 해당 기기로 전송하여 라즈베리파이가 새로운 Wi-Fi에 연결하도록 합니다.

6.  **[서버] 소유권 할당 및 자격증명 생성**:
    a. 서버는 `devices` 테이블에서 `cpu_serial`을 조회하여 기기가 사전 등록된 유효한 기기인지 확인합니다.
    b. 서버는 `user_devices` 테이블에 레코드를 추가하여 해당 기기를 요청한 사용자에게 할당(소유권 연결)합니다.
    c. 서버는 이 사용자-기기 조합을 위한 고유한 `shared_secret`(HMAC용)을 생성하여 데이터베이스에 안전하게 저장합니다.
    d. **장치별 고유 클라이언트 인증서 생성 및 할당**: 각 라즈베리파이 장치를 위한 **고유한 클라이언트 인증서(`device_uuid.crt`)와 개인 키(`device_uuid.key`) 쌍을 자동 생성**합니다. 이 과정은 `app/core/certificate_manager.py` 모듈이 전담하여 처리합니다. 이 모듈은 시스템에 자체 서명된 로컬 인증 기관(CA)이 없는 경우(`certs/ca.key`, `certs/ca.crt`) 자동으로 생성하며, 이 CA를 사용해 각 장치의 고유 인증서에 서명합니다. 생성된 인증서의 Common Name(CN)은 해당 장치의 `device_uuid`로 설정되며, 이는 Mosquitto 브로커에서 `use_identity_as_username true` 옵션과 함께 장치별 ACL(Access Control List)을 적용하는 데 사용됩니다. 이 인증서는 MQTT TLS 연결 시 장치 자체를 인증하는 핵심적인 역할을 합니다.

7.  **[서버/기기] 자격증명 발급**: 잠시 후, 기기는 인터넷을 통해 서버의 `POST /api/devices/credentials` 엔드포인트로 자신의 `cpu_serial`을 보내 자격증명을 요청합니다. 서버는 해당 기기가 특정 사용자에게 할당된 것을 확인하고, 저장되어 있던 `user_id`(또는 `user_email`)와 `shared_secret`을 기기에게 발급해 줍니다.

8.  **[기기] 프로비저닝 완료**: 기기는 발급받은 자격증명을 자신의 안전한 저장소에 기록하고, 이후 모든 MQTT 통신에 이 정보를 사용합니다.

9.  **[기기] 보안 강화**: 프로비저닝이 성공적으로 완료되면, 기기는 보안을 위해 더 이상 불필요한 블루투스 페어링 모드를 즉시 비활성화합니다.

## 10. 장치 식별 및 무결성 전략

이 문서는 라즈베리파이 장치 식별에 UUID(Universally Unique Identifier)와 CPU 시리얼 넘버를 함께 사용하는 전략의 배경, 발생 가능한 문제점 및 해결 방안을 요약합니다.

### 10.1. UUID와 CPU 시리얼 넘버를 함께 사용하는 목적

*   **UUID**: 소프트웨어 인스턴스 또는 논리적 장치(Logical Device)를 식별하는 데 사용됩니다. SD 카드에 저장되므로, SD 카드를 옮겨도 동일한 논리적 장치로 인식됩니다.
*   **CPU 시리얼 넘버**: 물리적 하드웨어 장치(Physical Device)를 식별하는 데 사용됩니다. 라즈베리파이 본체에 고유하게 부여됩니다.
*   **이점**: 이 두 가지를 함께 사용함으로써, 백엔드 시스템은 소프트웨어 인스턴스(UUID)와 물리적 하드웨어(CPU 시리얼)를 모두 추적할 수 있어 장치 관리의 유연성과 견고성을 크게 높일 수 있습니다.

### 10.2. 발생 가능한 문제 시나리오 및 해결 방안

#### 시나리오 1: SD 카드 복제 (Cloning)

*   **문제점**: 사용자가 SD 카드(UUID A 포함)를 여러 개 복제하여 각각 다른 라즈베리파이(CPU 시리얼 B, C 등)에 삽입하여 구동하는 경우.
    *   모든 복제본은 동일한 UUID A를 가지지만, 서로 다른 CPU 시리얼 넘버를 보고합니다.
*   **탐지 방법**:
    *   백엔드 시스템은 동일한 `DEVICE_ID`(UUID A)로부터 **서로 다른 `hardware_id`(CPU 시리얼 B, C 등)가 보고되는 것**을 감지합니다. 이는 명백한 복제본 사용의 증거입니다.
*   **해결 방안 (백엔드 정책)**:
    *   **알림**: 즉시 관리자에게 복제본 탐지 알림을 보냅니다.
    *   **데이터 격리/폐기**: 복제본으로 의심되는 장치에서 오는 데이터는 신뢰할 수 없으므로 격리하거나 폐기합니다.
    *   **접속 차단**:
        *   해당 UUID를 가진 모든 장치의 MQTT 접속을 차단할 수 있습니다 (원본 장치도 차단될 수 있음).
        *   또는, 초기 프로비저닝 시 등록된 `(UUID, CPU 시리얼)` 페어와 일치하는 장치만 허용하고, 불일치하는 장치(클론)의 접속만 차단할 수 있습니다.
    *   **원격 명령**: MQTT를 통해 해당 UUID로 "자체 비활성화" 또는 "설정 초기화" 명령을 전송하여 클론 장치의 작동을 중단시킬 수 있습니다.

#### 시나리오 2: SD 카드 또는 라즈베리파이 본체 교체 (Swapping)

*   **문제점**:
    *   **SD 카드 교체**: 기존 SD 카드(UUID A) 고장으로 새 SD 카드(UUID B)를 동일 라즈베리파이(CPU 시리얼 A)에 삽입.
        *   백엔드는 `(UUID A, CPU 시리얼 A)`를 예상하나, `(UUID B, CPU 시리얼 A)`를 수신.
    *   **라즈베리파이 본체 교체**: 기존 라즈베리파이(CPU 시리얼 A) 고장으로 동일 SD 카드(UUID A)를 새 라즈베리파이(CPU 시리얼 B)에 삽입.
        *   백엔드는 `(UUID A, CPU 시리얼 A)`를 예상하나, `(UUID A, CPU 시리얼 B)`를 수신.
*   **탐지 방법**:
    *   백엔드는 수신된 `(UUID, CPU 시리얼)` 페어가 **기존에 등록된 매핑과 일치하지 않음**을 감지합니다.
*   **해결 방안 (백엔드 정책)**:
    *   **알림**: 관리자에게 하드웨어 변경(SD 카드 또는 라즈베리파이 본체 교체) 알림을 보냅니다.
    *   **자동 매핑 업데이트**:
        *   만약 이러한 교체가 정상적인 유지보수 활동으로 간주된다면, 백엔드는 새로운 `(UUID, CPU 시리얼)` 페어로 매핑 정보를 자동으로 업데이트할 수 있습니다.
        *   예: `UUID A`가 `CPU 시리얼 B`에서 보고되면, 백엔드는 `UUID A`의 연결된 `CPU 시리얼`을 `A`에서 `B`로 업데이트합니다.
    *   **재프로비저닝 요구**: 시스템이 엄격한 매핑을 요구한다면, 장치에 재프로비저닝을 요구하는 명령을 보내거나, 관리자가 수동으로 재프로비저닝을 진행하도록 할 수 있습니다.

#### 시나리오 3: UUID 충돌 (Collision - 발생 확률은 극히 낮음)

*   **문제점**: 두 장치가 우연히 동일한 UUID를 생성하는 경우. (확률은 극히 낮아 실제 발생 가능성은 무시할 수준)
*   **탐지 방법**:
    *   백엔드 시스템은 동일한 `DEVICE_ID`(UUID)로부터 **서로 다른 `hardware_id`(CPU 시리얼)가 보고되는 것**을 감지합니다. (시나리오 1과 유사하게 탐지)
*   **해결 방안 (수동 개입)**:
    *   **알림**: 즉시 관리자에게 치명적인 UUID 충돌 알림을 보냅니다.
    *   **수동 조사**: 관리자는 관련된 물리적 장치들을 식별하고, 어떤 장치가 "정상"인지 판단합니다.
    *   **UUID 강제 재설정**: 충돌하는 장치 중 하나 또는 모두에 대해 수동으로 장치 내의 UUID 저장 파일을 삭제하고 재시작하여 새로운 UUID를 생성하도록 합니다. 이후 백엔드에 재프로비저닝합니다.

### 10.3. 백엔드의 일반적인 역할

*   **진실의 원천 (Source of Truth)**: 백엔드는 장치의 `(UUID, CPU 시리얼)` 매핑 및 기대되는 상태에 대한 권위 있는 정보를 유지해야 합니다.
*   **정책 기반 (Policy-Driven)**: "자동 처리"는 백엔드 애플리케이션에 정의된 정책에 따라 달라집니다. 어떤 변경이 허용되고 어떤 변경이 차단되어야 하는지 명확한 정책이 필요합니다.
*   **경고 시스템**: 모든 중요한 장치 상태 변경이나 불일치에 대해 관리자에게 즉시 알림을 보내는 시스템이 필수적입니다.
*   **장치 측 보고**: 장치(라즈베리파이)는 자신의 UUID(SD 카드에서)와 CPU 시리얼 넘버(하드웨어에서)를 일관되게 백엔드에 보고하는 역할을 합니다. 모든 지능적인 판단과 해결은 백엔드에서 이루어집니다。

### 10.4. 사전 등록 시 식별자 중복 처리 정책

관리자가 기기를 사전 등록할 때, `cpu_serial` 또는 `uuid`가 데이터베이스에 이미 존재할 수 있습니다. 각 시나리오에 대한 처리 정책은 다음과 같습니다.

*   **`cpu_serial` 중복의 경우 (실질적 시나리오):**
    *   **신뢰 가정 및 해석:** 이 시스템은 `cpu_serial`이 하드웨어의 고유 식별자라는 신뢰 가정 하에 구축되었습니다. 따라서 중복이 감지되면, 이는 '다른 기기와의 우연한 충돌'이 아니라 **'이미 등록된 기기의 재등록 시도'**로 간주합니다.
    *   **처리 방안:** 서버 API(`POST /api/devices/preregister`)는 **HTTP 409 Conflict**를 응답합니다. API를 호출하는 클라이언트(예: 자동 등록 도구)는 이 응답을 받고, "이미 등록된 기기입니다."라는 메시지를 관리자에게 명확히 보여줍니다.

*   **`uuid` 중복의 경우 (이론적 시나리오):**
    *   **신뢰 가정 및 해석:** UUID v4 표준을 사용하므로, 수학적으로 중복될 확률은 무시할 수 있을 정도로 매우 낮습니다. 하지만 만약의 경우를 대비합니다.
    *   **처리 방안:** `uuid` 컬럼에도 `UNIQUE` 제약 조건이 있으므로 서버 API는 동일하게 **HTTP 409 Conflict**를 응답합니다. 이 응답을 받은 클라이언트(예: 자동 등록 도구)는 **내부적으로 새 UUID를 다시 한번 생성하여 API 호출을 자동으로 재시도**합니다. 이 과정은 사용자에게 보이지 않게 처리됩니다.


## 11. 기기 연결 해제 및 초기화 (De-provisioning)

사용자 계정 탈퇴 또는 기기 분실 등, 기기와 사용자의 연결을 해제하고 기기를 초기 상태로 되돌려야 할 때를 위한 시나리오입니다.

1.  **[서버] 연결 관계 삭제**: 사용자가 앱을 통해 계정을 탈퇴하거나 특정 기기와의 연결을 해제하면, 서버는 데이터베이스에서 해당 `users` 및 `user_devices` 레코드를 삭제합니다. 이와 동시에 기기에 발급되었던 `shared_secret` 및 **장치별 클라이언트 인증서**도 즉시 무효화(삭제)됩니다. 이제 기기는 논리적으로 '주인 없는' 상태가 됩니다。

2.  **[기기/서버] 인증 실패**: 기기는 이 사실을 모른 채 평소처럼 서버로 데이터를 전송합니다. 서버는 HMAC 서명을 검증하려 하지만, 유효한 `shared_secret`이 없으므로 '인증 실패'로 판단합니다. 동시에 MQTT 브로커는 더 이상 유효하지 않은 클라이언트 인증서로 연결을 시도하는 장치에 대해 연결을 거부합니다。

3.  **[서버] 원격 초기화 명령**: 인증에 실패한 기기에게, 서버는 `system/{device_id}/reset`과 같은 특정 시스템 토픽을 통해 '인증 정보가 만료되었으니 초기화하라'는 명령을 전송합니다。

4.  **[기기] 공장 초기화 상태 복귀**: '초기화' 명령을 수신한 기기는 자신의 저장소에 기록된 모든 자격증명(`user_id`, `shared_secret`, **고유 클라이언트 인증서 및 개인 키**)을 삭제합니다. 그 후, 다시 블루투스 페어링 모드를 활성화하여 새로운 주인을 기다리는 '프로비저닝 대기' 상태로 돌아갑니다. 이로써 기기는 다른 사용자가 안전하게 재사용할 수 있게 됩니다。

## 12. OTA 업데이트 아키텍처 (신규)

안정적이고 효율적인 OTA(Over-the-Air) 업데이트를 위해 MQTT와 HTTP를 함께 사용하는 하이브리드 모델을 채택합니다.

1.  **[관리자] 업데이트 등록**: 관리자가 서버의 `POST /api/updates` API를 통해 새로운 펌웨어 버전과 업데이트 패키지(바이너리 파일)를 업로드합니다. **업로드된 패키지 파일은 클라우드 저장소에 저장됩니다.**
2.  **[사용자/앱] 업데이트 명령**: 사용자가 Flutter 앱에서 특정 기기의 업데이트를 시작하면, 앱은 `POST /api/devices/{id}/ota-trigger` API를 호출합니다.
3.  **[서버] 업데이트 알림 (MQTT)**: API 요청을 받은 서버는 해당 기기에게 `commands/{device_uuid}/ota/notify` 토픽으로 업데이트가 필요함을 알리는 MQTT 메시지를 발행합니다. 메시지에는 `{ "version": "2.1.0" }`와 같이 새 버전 정보가 포함됩니다.
4.  **[기기] 업데이트 정보 조회 (HTTP)**: MQTT 알림을 수신한 라즈베리파이는 `GET /api/updates/latest` 또는 특정 버전 조회 API를 호출하여, 업데이트 파일의 다운로드 URL(예: S3 pre-signed URL), 파일 해시(무결성 검증용) 등의 상세 정보를 얻습니다.
5.  **[기기] 업데이트 다운로드 (HTTP)**: 기기는 받은 URL을 통해 대용량 업데이트 파일을 다운로드합니다.
6.  **[기기] 상태 보고 (MQTT)**: 기기는 다운로드 시작, 진행률, 설치, 성공, 실패 등 업데이트의 전 과정을 `telemetry/{device_uuid}/ota/status` 토픽을 통해 서버로 보고합니다.
7.  **[서버/앱] 실시간 모니터링**: 서버의 MQTT 리스너는 이 상태 메시지를 수신하여 Redis 캐시를 업데이트하고, `client/state/...` 토픽으로 앱에 전달하여 사용자가 실시간으로 업데이트 진행 상황을 모니터링할 수 있게 합니다.

## 13. 관리자/개발자 웹 패널 (Web Panel for Admin/Developer)

시스템 관리자 및 개발자를 위한 웹 기반 패널을 구축하여 시스템 운영 및 디버깅 편의성을 제공합니다. 빠른 개발과 안정성을 위해 Django 프레임워크의 내장 Admin 기능을 사용하여 구현합니다. 이 패널은 역할 기반 접근 제어(RBAC)를 통해 관리자 및 개발자 권한을 명확히 구분합니다.

### 13.1. 주요 기능

*   **기기 사전 등록**: `cpu_serial`을 사용하여 새로운 기기를 시스템에 사전 등록합니다.
*   **사용자 관리**: 사용자 계정 생성, 수정, 삭제 및 권한 관리.
*   **기기 관리**: 등록된 기기 목록 조회, 기기 정보 수정, 기기-사용자 연결 관리.
*   **텔레메트리 데이터 조회**: 특정 기기의 과거 텔레메트리 데이터를 조회하고 시각화합니다.
*   **시스템 모니터링**: 서버 및 MQTT 브로커의 상태 모니터링, 로그 조회.
*   **디버깅 도구**: 특정 기기로의 명령 전송, 기기 상태 강제 변경 등 개발 및 디버깅을 위한 기능.

### 13.2. 역할 기반 접근 제어 (RBAC)

*   **관리자 (Admin)**: 모든 시스템 기능에 대한 접근 권한을 가집m니다. 사용자 및 기기 관리, 시스템 설정 변경 등.
*   **개발자 (Developer)**: 시스템 모니터링, 로그 조회, 디버깅 도구 사용 등 개발 및 테스트에 필요한 기능에 접근할 수 있습니다. 민감한 운영 설정 변경 권한은 제한됩니다.

### 13.3. 기술적 고려사항 (Technical Considerations)

*   **데이터베이스 모델 관리 및 자동 동기화**: 관리자 패널은 FastAPI 서버와 동일한 데이터베이스를 사용하지만, 자체적인 Django 모델(`admin_panel/ares_admin/models.py`)을 가집니다. 이 모델들은 `managed = False` 옵션을 통해 Django의 마이그레이션 기능으로 관리되지 않습니다. 데이터베이스 스키마의 '진실의 원천(Source of Truth)'은 `server` 애플리케이션의 SQLAlchemy 모델과 Alembic 마이그레이션입니다. 따라서 `server`의 모델이 변경될 경우, `admin_panel`의 모델도 동기화해야 합니다. 이 프로세스를 자동화하기 위해, `alembic/env.py` 스크립트에는 **Alembic 마이그레이션이 성공적으로 완료될 때마다 `admin_panel/regenerate_django_models.py` 스크립트를 자동으로 호출하는 후크(hook)가 구현**되어 있습니다. 이 스크립트는 `inspectdb` 명령을 실행하여 데이터베이스로부터 최신 모델 코드가 포함된 임시 파일을 생성하므로, 개발자는 이를 참고하여 `models.py` 파일을 더 쉽고 정확하게 업데이트할 수 있습니다. **또한, Django 관리자 패널은 `server`의 `users` 테이블을 직접 사용하여 사용자 및 역할을 관리하기 위해 사용자 지정 Django 사용자 모델과 인증 백엔드를 구현할 것입니다.**

*   **중앙 집중식 설정 관리**: Django 관리자 패널은 독립적인 설정 파일을 가지는 대신, `admin_panel/ares_admin/settings.py` 파일 내에서 **`server` 프로젝트의 `config/local.yaml` 또는 `config/prod.yaml` 파일을 직접 읽어 데이터베이스 연결 정보 등을 가져옵니다.** 이 방식은 두 애플리케이션의 설정이 분리되어 발생하는 문제를 원천적으로 방지하고, 모든 주요 설정을 `server`의 `config` 디렉토리에서 중앙 집중적으로 관리할 수 있도록 합니다.

*   **데이터 타입 처리**: `admin_panel/ares_admin/models.py`에는 `CustomJSONField`가 구현되어 있습니다. 이는 `psycopg2` 라이브러리가 PostgreSQL의 `JSONB` 타입을 Python 딕셔너리로 자동 변환한 상태에서 Django 모델이 이를 다시 JSON 문자열로 변환하려는 문제를 해결하고, 데이터베이스 값을 그대로 사용하기 위해 추가된 커스텀 필드입니다.

*   **사용자 인증**: Django 관리자 패널은 `server`의 `users` 테이블을 직접 사용하며, `email`을 통한 로그인을 지원하기 위해 `CustomAuthBackend`를 구현했습니다. 이 백엔드는 FastAPI 서버와 동일한 `bcrypt` 해시 비밀번호를 검증하고, 사용자의 역할(`roles` 테이블)에 따라 `is_staff` 및 `is_superuser` 플래그를 동적으로 설정하여 패널 접근 권한을 제어합니다.

## 14. 향후 개선 과제

- **부품 단위 헬스 체크 (Component Health Check)**: 현재 기기 전체의 타임아웃만 관리하는 로직을 확장하여, `attached_components`에 등록된 부품이 실제로 MQTT 메시지를 보내고 있는지 주기적으로 확인합니다. 특정 부품에서만 데이터가 들어오지 않는 경우, 해당 부품의 상태를 '오류' 또는 '연결 끊김'으로 표시하여 사용자가 문제를 더 정확히 인지할 수 있도록 합니다.
- **사용자 프로필 및 설정 관리 API 구현**: 사용자가 자신의 프로필(이름 등)을 수정하거나, 알림 설정을 관리하는 기능을 위해 `PUT /api/users/me`와 같은 API를 구현합니다.

## 15. 로컬 개발 환경 실행 (Local Development Startup)

이 섹션은 로컬 환경에서 개발을 위해 서버의 모든 구성 요소를 실행하는 절차를 설명합니다.

### 15.1. 사전 요구사항

- Docker가 설치되고 실행 중이어야 합니다.
- Python 가상 환경(`venv`)이 설정되어 있어야 합니다.
- `requirements.txt`에 명시된 모든 라이브러리가 가상 환경에 설치되어 있어야 합니다.

### 15.2. 실행 순서

올바른 통신을 위해 각 구성 요소는 **반드시 별개의 터미널 창**에서 실행되어야 합니다.

1.  **의존 서비스 시작 (Docker Compose)**
    -   프로젝트에 필요한 데이터베이스(PostgreSQL), 캐시(Redis), MQTT 브로커(Mosquitto)는 `docker-compose.yml` 파일을 통해 관리됩니다.
    -   프로젝트 루트 디렉토리(`Ares4/`)에서 다음 명령어를 실행하여 모든 서비스를 시작합니다.
    ```shell
    # 프로젝트 루트 디렉토리로 이동
    cd path/to/Ares4/

    # Docker Compose 서비스 시작
    docker-compose up -d
    ```
    -   **컨테이너 충돌 시:** 만약 `Conflict` 오류가 발생하면, 기존에 남아있는 컨테이너를 중지하고 제거한 후 다시 시도해야 합니다.
    ```shell
    docker stop mosquitto ares4-postgres some-redis
    docker rm mosquitto ares4-postgres some-redis
    docker-compose up -d
    ```
    -   **중요**: 이전에 문제가 되었던 Windows 서비스 형태의 Mosquitto가 실행되지 않도록 `net stop mosquitto` 명령어로 확인하는 것이 좋습니다.

2.  **API 서버 실행**
    -   새로운 터미널을 열고, `server` 디렉토리에서 아래 명령어를 실행합니다.
    ```shell
    # server 디렉토리로 이동
    cd path/to/Ares4/server

    # 가상 환경 활성화 (Windows)
    venv\Scripts\activate

    # Uvicorn으로 API 서버 실행
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

3.  **MQTT 리스너 실행**
    -   또 다른 새 터미널을 열고, `server` 디렉토리에서 아래 명령어를 실행합니다。
    ```shell
    # server 디렉토리로 이동
    cd path/to/Ares4/server

    # 가상 환경 활성화 (Windows)
    venv\Scripts\activate

    # 리스너 스크립트 실행 (TLS 활성화 시 환경 변수 설정 필요)
    # 예시: set MQTT_TLS_ENABLED=True (Windows) 또는 export MQTT_TLS_ENABLED=True (Linux/macOS)
    python -m app.scripts.run_listener
    ```

이제 모든 백엔드 서비스가 준비되었으며, Flutter 앱이나 다른 클라이언트의 연결을 처리할 수 있습니다.

### 15.3. 개발 보조 스크립트 (Development Helper Scripts)

`server/app/scripts` 폴더에는 개발, 테스트, 디버깅을 돕는 여러 유용한 스크립트가 포함되어 있습니다. 이러한 스크립트의 상세한 사용법은 [서버 테스트 아키텍처 설계 문서](SERVER_TEST_ARCHITECTURE.md)를 참조하십시오.

*   **목업 장치 시뮬레이터 실행 (`mock_device_publisher.py`)**: 실제 라즈베리파이 없이 가상의 장치가 MQTT 메시지를 보내는 것처럼 시뮬레이션합니다.
*   **테스트용 사용자 및 장치 등록 (`register_mock_user.py`, `register_mock_device.py`)**: 테스트에 필요한 사용자 계정과 장치를 미리 등록합니다.
*   **테스트용 장치 사전 등록 (`preregister_mock_device.py`)**: 관리자가 기기의 `cpu_serial`을 사용하여 시스템에 기기를 사전 등록하는 과정을 시뮬레이션합니다.
*   **초기 데이터 시딩 (`seed_test_data.py`)**: `supported_components` 테이블과 같이 시스템 운영에 필요한 초기 데이터를 데이터베이스에 미리 채워 넣습니다.
*   **범용 MQTT 구독기 (디버깅용) (`test_subscriber.py`)**: 특정 토픽을 구독하여 브로커로 오고 가는 메시지를 실시간으로 모니터링할 때 사용합니다.

### 15.4. 기타 개발 스크립트 (Other Development Scripts)

위 스크립트 외에도, 특정 개발 및 디버깅 시나리오를 위한 추가 스크립트들이 `server/app/scripts/` 폴더에 존재합니다. 이러한 스크립트의 상세한 사용법은 [서버 테스트 아키텍처 설계 문서](SERVER_TEST_ARCHITECTURE.md)를 참조하십시오.

*   **하드웨어 변형 확인 (`check_hardware_variant.py`)**: 특정 하드웨어 변형의 유효성을 확인하거나 관련 정보를 조회합니다.
*   **목업 장치 인증서 삭제 (`clear_mock_device_certs.py`)**: 테스트를 위해 생성된 임시 목업 장치 인증서 및 키 파일을 삭제합니다.
*   **하드웨어 변형 스크립트 생성 (`create_hardware_variant_script.py`)**: 새로운 하드웨어 변형을 위한 스크립트 또는 설정 파일을 생성합니다.
*   **하드웨어 변형 생성 (`create_hardware_variant.py`)**: 시스템에 새로운 하드웨어 변형을 등록합니다.
*   **인증서 생성 (`generate_certs.py`)**: 개발 및 테스트 목적으로 필요한 TLS/SSL 인증서 및 키 파일을 생성합니다.
*   **권한 초기화 (`initialize_permissions.py`)**: 시스템의 기본 권한 데이터를 초기화하거나 재설정합니다.
*   **역할 및 권한 초기화 (`initialize_roles_and_permissions.py`)**: 시스템의 기본 역할 및 권한 데이터를 초기화하거나 재설정합니다.
*   **MQTT ACL 파일 동적 생성 (`generate_mqtt_acl.py`)**: 데이터베이스의 최신 사용자 및 기기 정보를 바탕으로 Mosquitto 브로커가 사용할 `acl.conf` 파일을 동적으로 생성합니다. 새로운 사용자나 기기가 추가되었을 때 브로커의 접근 제어 규칙을 쉽게 업데이트할 수 있습니다.
*   **다양한 테스트 메시지 발행 (`publish_alert_message.py`, `publish_offline_message.py`, `publish_test_message.py`)**: 특정 시나리오를 테스트하기 위해 다양한 종류의 MQTT 메시지를 발행합니다.
*   **테스트 기기 UUID 강제 변경 (`update_device_uuid.py`)**: 개발 및 테스트 과정에서 특정 기기의 UUID를 알려진 값으로 강제 변경할 필요가 있을 때 사용합니다.

### 15.5. 테스트 아키텍처 (Testing Architecture)

서버 애플리케이션의 테스트 전략, 프레임워크(`pytest`), 테스트 유형 및 실행 방법에 대한 자세한 내용은 별도의 [서버 테스트 아키텍처 설계 문서](SERVER_TEST_ARCHITECTURE.md)를 참조하십시오.

### 15.6. 개발 보조 도구 (Development Helper Tools)

`admin_panel` 개발 환경에서는 `django_extensions` 라이브러리를 사용하여 개발 생산성을 향상시킵니다. 이 라이브러리는 다음과 같은 유용한 기능을 제공합니다:

*   **`shell_plus`**: Django 모델이 자동으로 로드된 확장된 Django 셸.
*   **`runserver_plus`**: HTTPS 지원 및 디버거가 내장된 개발 서버.
*   **`graph_models`**: 설치된 앱의 모델 관계를 시각화하는 그래프 생성.