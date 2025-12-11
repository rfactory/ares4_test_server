# `user_identity` 도메인 설계 문서

## 1. 도메인의 목적 및 책임

`user_identity` 도메인은 **'사용자 신원(Identity)'**의 생명주기와 관련된 핵심 CRUD(생성, 조회, 수정, 삭제) 작업을 전담하는 '전문가 서비스'입니다.

-   **주요 책임:**
    -   새로운 사용자 계정 생성 (`create_user_and_log`)
    -   사용자 계정 활성화 (`activate_user`)
    -   사용자명, 이메일, ID 등 다양한 조건으로 사용자 정보 조회 (`get_user_by...`)
    -   (향후) 사용자 정보의 개별 속성 업데이트
    -   (향후) 사용자 계정 삭제

-   **포함하지 않는 책임:**
    -   사용자 인증(로그인) 로직 (이는 `authentication` 도메인의 책임)
    -   사용자의 개별 설정 변경 (이는 `user_settings` 도메인의 책임)
    -   사용자에게 역할을 부여하는 로직 (이는 `user_authorization` 도메인의 책임)
    -   여러 도메인을 조율하는 복잡한 비즈니스 워크플로우 (이는 `user_management` 오케스트레이터의 책임)

---

## 2. 핵심 설계 원칙

### 2.1. 단일 책임 원칙 (Single Responsibility Principle)

-   `UserIdentityService`는 오직 '사용자'라는 데이터 모델의 생명주기를 관리하는 책임만 가집니다. 다른 모든 부가적인 기능(인증, 설정, 권한 부여 등)은 별도의 전문 도메인에 위임합니다.

### 2.2. 외부 의존성 최소화

-   이 도메인은 다른 비즈니스 도메인에 거의 의존하지 않습니다. 단, 생성/수정 이벤트가 발생했을 때 이를 기록하기 위해 `inter_domain` 프로바이더를 통해 `audit` 도메인을 호출합니다.

---

## 3. 권한 모델 (Permission Model)

-   **서비스 메소드:** `UserIdentityService`의 메소드들(`create_user_and_log`, `activate_user`, `get_user_by...` 등)은 자체적으로 권한 검사를 수행하지 않습니다. 이들을 호출하는 상위 계층의 API 엔드포인트나 다른 서비스(예: `access_request_service`)가 해당 작업을 수행할 수 있는 권한을 가졌는지 사전에 확인해야 할 책임이 있습니다.
-   **API 엔드포인트:**
    -   `POST /users/`: **`system:user:create`** 권한이 필요합니다. (`System_Admin` 역할만 호출 가능)
    -   `GET /users/{username}`: **`user:read`** 권한이 필요합니다.

---

## 4. 주요 기능 및 작동 방식

### 4.1. `UserIdentityService.create_user_and_log(...)`

-   **역할:** 새로운 사용자 계정을 데이터베이스에 생성하고, 이 사실을 감사 로그에 기록합니다.
-   **작동 방식:**
    1.  사용자명, 이메일 중복 여부를 `user_crud`를 통해 확인합니다.
    2.  비밀번호를 해시 처리합니다.
    3.  `user_crud.create_with_hashed_password()`를 호출하여 DB에 새로운 `User` 레코드를 저장합니다.
    4.  `inter_domain` 프로바이더를 통해 `audit_providers.log()`를 호출하여 `USER_CREATED` 이벤트를 기록합니다.

### 4.2. `UserIdentityService.activate_user(...)`

-   **역할:** 지정된 사용자를 활성(active) 상태로 만듭니다.
-   **작동 방식:**
    1.  `user_id`로 사용자를 조회합니다.
    2.  사용자의 `is_active` 플래그를 `True`로 설정하고 DB에 저장합니다.
    3.  `audit_providers.log()`를 호출하여 `USER_ACTIVATED` 이벤트를 기록합니다.

### 4.3. `UserIdentityService.get_user_by...(...)`

-   **역할:** 다양한 조건(사용자명, 이메일, ID)으로 사용자 정보를 조회합니다.
-   **작동 방식:** `user_crud`의 해당 조회 메소드를 직접 호출하여 결과를 반환하는 간단한 Wrapper 역할을 합니다.

---

## 5. API 엔드포인트 (`api/endpoints_identity.py`)

-   **`POST /users/`**: 새로운 사용자 생성. (`system:user:create` 권한 필요)
-   **`GET /users/{username}`**: 사용자명으로 특정 사용자 정보 조회. (`user:read` 권한 필요)
