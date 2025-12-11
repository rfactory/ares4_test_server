# `user_management` 오케스트레이터 도메인 설계 문서

## 1. 도메인의 목적 및 책임

`user_management` 도메인은 **사용자 생명주기 및 권한 관련 복합 비즈니스 워크플로우를 조율(orchestrate)**하는 '오케스트레이터 서비스'입니다. 여러 전문가 서비스들의 기능을 조합하여 고수준의 비즈니스 기능을 제공합니다.

-   **주요 책임:**
    -   사용자 생성 및 접근 요청 시작 (`create_user_and_request_access`)
    -   접근 요청 조회 (`get_access_requests`)
    -   접근 요청 처리 (`process_access_request_workflow`)

-   **포함하지 않는 책임:**
    -   사용자 신원 관리 (이는 `user_identity` 도메인의 책임)
    -   사용자 설정 관리 (이는 `user_settings` 도메인의 책임)
    -   역할 할당 (이는 `user_authorization` 도메인의 책임)
    -   개별 접근 요청 관리 (이는 `access_requests` 도메인의 책임)

---

## 2. 핵심 설계 원칙

### 2.1. 오케스트레이션 (Orchestration)

-   이 도메인은 직접적으로 로직을 수행하기보다, `inter_domain` 프로바이더를 통해 다른 전문가 서비스들을 순서대로 호출하고 그 결과를 조합하여 비즈니스 워크플로우를 완성합니다.

### 2.2. 외부 의존성 관리

-   모든 하위 서비스 호출은 `inter_domain` 프로바이더를 통해서만 이루어집니다.

---

## 3. 권한 모델 (Permission Model)

-   **자체 권한 로직 없음:** `UserManagementCoordinator` 자체는 복잡한 권한 로직을 직접 수행하지 않습니다.
-   **하위 서비스 위임:** 각 기능에 대한 권한 검사는 이 오케스트레이터가 호출하는 하위 전문가 서비스(예: `access_requests`)에서 책임지고 수행합니다.
-   **API 계층의 역할:** API 엔드포인트(`endpoints_user.py`)에서는 `get_current_user`와 같은 전역 의존성을 통해 호출자의 인증 상태를 확인하고, 필요한 경우 하위 서비스의 권한 검사 결과를 HTTP 예외로 변환하여 반환합니다.

---

## 4. 주요 기능 및 작동 방식

### 4.1. `UserManagementCoordinator.create_user_and_request_access(...)`

-   **역할:** 새로운 사용자 계정을 생성(필요시)하고, 해당 사용자를 위한 접근 요청을 시작하는 고수준 워크플로우.
-   **작동 방식:**
    1.  `inter_domain` 프로바이더를 통해 `UserIdentityService`에게 사용자 조회(`get_user_by_email`)를 요청합니다.
    2.  사용자가 존재하지 않으면, `UserIdentityService`를 통해 사용자 계정 생성(`create_user_and_log`)을 요청합니다.
    3.  `inter_domain` 프로바이더를 통해 `AccessRequestService`에게 접근 요청 생성(`create_access_request`)을 요청합니다.

### 4.2. `UserManagementCoordinator.get_access_requests(...)`

-   **역할:** 접근 요청 목록을 조회하는 워크플로우를 조율.
-   **작동 방식:** `inter_domain` 프로바이더를 통해 `AccessRequestService`에게 접근 요청 조회(`get_access_requests`)를 요청합니다.

### 4.3. `UserManagementCoordinator.process_access_request_workflow(...)`

-   **역할:** 접근 요청의 처리(승인/거절) 워크플로우를 조율.
-   **작동 방식:** `inter_domain` 프로바이더를 통해 `AccessRequestService`에게 접근 요청 처리(`process_access_request`)를 요청합니다.

---

## 5. API 엔드포인트 (`api/endpoints_user.py`)

-   **`POST /management/access-request`**: 사용자 생성 및 접근 요청 시작.
-   **`GET /management/access-requests`**: 접근 요청 목록 조회.
-   **`PUT /management/access-requests/{request_id}`**: 접근 요청 처리.
