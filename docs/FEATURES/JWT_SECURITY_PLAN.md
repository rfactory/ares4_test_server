# JWT 보안 강화 계획: Refresh Token Rotation & DPoP

## 1. 개요

본 문서는 현재의 JWT 인증 방식의 보안을 강화하기 위한 단계별 구현 계획을 정의합니다. 핵심 목표는 토큰 탈취 공격에 대한 방어력을 높이고, 안전한 세션 관리 메커니즘을 도입하는 것입니다.

## 2. 핵심 전략: 하이브리드 토큰 모델

전통적인 서버 세션 방식과 순수 JWT 방식의 장점을 결합한 하이브리드 모델을 채택합니다.

- **전송 계층 보안 (TLS/HTTPS):** 모든 통신은 HTTPS를 통해 암호화되어야 합니다. 이는 중간자 공격(Man-in-the-Middle)을 통해 전송 중인 토큰이 탈취되는 것을 방지하는 가장 기본적인 전제 조건입니다.
- **Stateless API Calls:** 대부분의 일반적인 API 요청은 수명이 짧은(short-lived) Access Token을 사용하여 서버 상태 조회 없이 빠르고 확장성 있게 처리합니다.
- **Stateful Session Control:** 로그아웃, 토큰 탈취 감지 등 중요한 세션 제어는 DB에 상태를 저장하는 Refresh Token을 통해 관리합니다. 이를 통해 필요 시 특정 사용자의 모든 세션을 즉시 무효화하는 등 중앙 제어가 가능해집니다.
- **블랙리스트 불필요:** 이 모델에서는 Access Token의 유효 기간이 매우 짧고, Refresh Token 자체를 DB에서 폐기하는 방식으로 세션을 제어하므로, 별도의 Access Token 블랙리스트를 운영할 필요가 없습니다.

## 3. 구현 계획

### 1단계: Refresh Token Rotation 구현

이 단계는 Refresh Token을 도입하고, 1회용으로 사용하도록 만들어 탈취된 토큰의 재사용을 방지 및 탐지하는 데 중점을 둡니다.

#### 1.1. Refresh Token 저장소: DB vs. Redis

- **논의:** Redis는 속도가 빠르지만, 서버 재시작 시 데이터가 유실되어 모든 사용자가 강제 로그아웃될 수 있는 치명적인 위험이 있습니다. 반면, DB(PostgreSQL)는 약간의 속도 저하가 있을 수 있으나, 데이터의 완전한 영속성을 보장하고, 특정 사용자의 모든 토큰을 조회/관리하는 등 복잡한 세션 관리에 훨씬 용이합니다.
- **결정:** 사용자의 로그인 세션은 매우 중요한 데이터이므로, 안전성과 영속성을 우선하여 **DB에 저장**하는 방식을 채택합니다.

#### 1.2. 구체적인 구현 단계

1.  **`RefreshToken` 모델 생성:**
    -   `server2/app/models/objects/refresh_token.py` 파일 및 관련 `__init__.py` 파일들을 생성 및 수정하여 모델을 정의하고 노출시켰습니다.
2.  **데이터베이스 마이그레이션:**
    -   Alembic을 사용하여 `refresh_tokens` 테이블을 생성하는 마이그레이션을 실행하고 적용했습니다.
3.  **`token_management` 도메인 생성:**
    -   기존의 불완전한 `token` 도메인을 삭제하고, CQRS 원칙에 따라 `crud`, `services` 하위 디렉토리를 포함하는 `server2/app/domains/services/token_management` 도메인을 새로 생성했습니다.
    -   `token_management_command_crud.py`, `token_management_query_crud.py`, `token_management_command_service.py`, `token_management_query_service.py` 파일들을 생성하여 토큰 발급, 조회, 순환, 폐기 로직을 구현했습니다.
4.  **토큰 생성 로직 수정:**
    -   `security.py`: `create_refresh_token` 함수를 추가했습니다.
    -   `config.py`: `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`를 `5`분으로, `JWT_REFRESH_TOKEN_EXPIRE_DAYS`를 `14`일로 설정했습니다.
5.  **로그인 흐름 수정:**
    -   `login_policy.py`가 새로운 `token_management_command_provider`를 통해 토큰 쌍을 발급받도록 수정했습니다.
6.  **토큰 갱신 엔드포인트 구현:**
    -   `server2/app/api/v1/endpoints/auth.py` 파일을 새로 생성하고, `/login/access-token` 및 `/register/*` 엔드포인트를 `common.py`에서 이곳으로 옮겼습니다.
    -   `POST /api/v1/auth/login/refresh` 엔드포인트를 `auth.py`에 구현했습니다.
    -   `refresh_token_policy.py`와 관련 Provider들을 '순수 오케스트레이션' 원칙에 맞게 생성하여 엔드포인트에 연결했습니다.
7.  **아키텍처 리팩토링:**
    -   구현 과정에서 `user_existence_validator`, `password_strength_validator` 등 여러 Validator들이 순수하지 않음을 발견하고, 이를 순수 Validator 원칙에 맞게 리팩토링했습니다.
    -   영향을 받는 `initiate_registration_policy.py` 파일도 수정하여 전체적인 아키텍처 일관성을 확보했습니다.

### 2단계: DPoP 구현 (향후 작업)

Refresh Token Rotation이 안정화된 후, 추가적인 보안 강화를 위해 DPoP(Demonstrating Proof-of-Possession) 구현을 고려합니다. DPoP는 토큰을 특정 클라이언트에 암호학적으로 귀속시켜, 토큰이 탈취되더라도 공격자가 다른 기기에서 사용할 수 없도록 만듭니다. 이는 클라이언트와 서버 양쪽에 상당한 수정이 필요하므로 별도 단계로 분리합니다.

## 4. JWT 시크릿 키 순환(Rotation) 전략

프로덕션 환경에서 서비스 중단 없이 시크릿 키를 안전하게 교체하기 위한 절차입니다. **(참고: 이 전략에 대한 코드는 아직 구현되지 않았습니다.)**

- **핵심:** 키 교체는 관리자가 직접 통제 하에 진행하는 **수동 운영 작업**이지만, 교체 과정에서 서버가 중단 없이 옛날 토큰과 새 토큰을 모두 처리하는 로직은 **코드로 자동화**됩니다.

- **1. 키 처리 로직 (내부, Python 코드):**
  - `security.py` 코드는 환경 변수에 여러 키(`JWT_SECRET_KEYS=키1,키2`)가 주어지면, 항상 첫 번째 키로 새 토큰을 서명하고, 검증 시에는 목록의 모든 키로 시도하도록 구현되어야 합니다.

- **2. 키 생성 (외부, 관리자):**
  - 관리자는 `openssl` 등의 도구를 사용하여 새로운 시크릿 키를 안전하게 생성합니다.

- **3. 키 관리 (외부, 관리자):**
  - **A 단계:** 관리자가 운영 서버에 접속하여 `.env` 파일의 `JWT_SECRET_KEYS` 환경 변수 맨 앞에 새로운 키를 추가합니다. (예: `JWT_SECRET_KEYS=새로운키,이전키`)
  - **B 단계:** 서버 애플리케이션을 재시작합니다.
  - **C 단계:** Refresh Token의 최대 유효 기간(예: 14일) 이상 기다립니다.
  - **D 단계:** 환경 변수에서 이제는 아무도 사용하지 않는 '이전키'를 제거하고 서버를 다시 재시작합니다.
