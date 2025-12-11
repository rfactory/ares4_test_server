# `device_access_management` 도메인 설계 문서

## 1. 도메인의 목적 및 책임

`device_access_management` 도메인은 **사용자(User)와 장치(Device) 간의 접근 관계를 정의하고 관리**하는 '전문가 서비스'입니다.

-   **주요 책임:**
    -   사용자와 장치 간의 연결(Link) 생성, 조회, 삭제 (예: `UserDevice` 관계)
    -   특정 사용자가 장치에 대해 'owner', 'viewer' 등의 역할을 갖는지 확인
    -   `active_context`에 기반하여, 특정 장치에 대한 사용자별 접근 권한 (읽기, 수정, 삭제) 확인
    -   장치 소유권 이전 및 해제 정책 준수 (특히 마지막 owner 제거 시 장치 초기화 트리거)

-   **포함하지 않는 책임:**
    -   장치 자체의 CRUD (이는 `device_management`의 책임)
    -   시스템/조직 레벨의 역할 기반 권한 (이는 `user_authorization`의 책임)

---

## 2. 핵심 설계 원칙

### 2.1. 컨텍스트 기반 접근 제어 (Context-Based Access Control)

-   모든 접근 제어는 `DEVICE_API_AND_ACCESS_POLICY.md`에 정의된 '컨텍스트 전환 모델'을 따릅니다.
-   모든 '스마트' 접근 메소드는 반드시 `active_context` 파라미터를 받아, 이 컨텍스트에 맞는 권한만 확인해야 합니다.

---

## 3. 주요 기능 및 작동 방식

### 3.1. `link_device_to_user(...)`

-   **역할:** 사용자와 장치 간에 특정 역할(예: 'owner', 'viewer')로 연결 관계를 생성합니다.
-   **작동 방식:** `user_device_link_crud.create()`를 호출하고, 감사 로그(`audit_providers.log`)를 기록합니다.

### 3.2. `remove_link(...)`

-   **역할:** 사용자와 장치 간의 연결 관계를 해제합니다.
-   **작동 방식:** `user_device_link_crud.remove_by_user_and_device()`를 호출하고, 감사 로그(`audit_providers.log`)를 기록합니다.

### 3.3. `is_user_owner_of_device(...)`

-   **역할:** 특정 사용자가 특정 장치의 'owner'인지 확인합니다.
-   **작동 방식:** `user_device_link_crud`를 통해 'owner' 역할의 연결을 조회합니다.

### 3.4. `get_device_if_user_has_read_access(...)` 외 '스마트' 접근 메소드

-   **역할:** API 계층으로부터 `active_context`를 전달받아, 사용자에게 특정 장치에 대한 읽기/수정/삭제 권한이 있는지 확인하고, 권한이 있으면 장치 정보를 반환합니다.
-   **핵심:** API 계층에서 비즈니스 로직(권한 확인)을 분리하여 서비스 계층에서 통합 처리합니다.
-   **작동 순서:**
    1.  **컨텍스트 분기:** `active_context` 값에 따라 로직이 분기됩니다.
    2.  **`personal` 컨텍스트:**
        -   사용자가 해당 장치의 `owner`인지 확인합니다. (`is_user_owner_of_device`)
        -   `owner`가 맞으면 장치 정보를 반환하고, 아니면 `PermissionDeniedError`를 발생시킵니다.
    3.  **`organization` 컨텍스트 (`int` 타입):**
        -   조회하려는 장치의 `organization_id`가 `active_context`로 전달된 `organization_id`와 일치하는지 확인합니다.
        -   일치한다면, `user_authorization` 서비스를 통해 사용자가 해당 조직에 대해 `device:read`와 같은 권한을 가졌는지 확인합니다.
        -   모든 조건이 맞으면 장치 정보를 반환하고, 아니면 `PermissionDeniedError`를 발생시킵니다.
    4.  **`global` 컨텍스트:**
        -   `user_authorization` 서비스를 통해 사용자가 `device:read_all`과 같은 전역 권한을 가졌는지 확인합니다.
        -   권한이 있으면 장치 정보를 반환하고, 아니면 `PermissionDeniedError`를 발생시킵니다.

---

## 4. 권한 모델 (Permission Model)

-   이 도메인 내의 모든 접근 제어 로직은 `DEVICE_API_AND_ACCESS_POLICY.md`에 정의된 정책을 따릅니다.
-   `is_user_owner_of_device`와 같은 메소드를 통해 개별 자산(`Device`)에 대한 소유 기반 권한을 관리하며, `user_authorization_providers.check_user_permission`을 통해 역할 기반의 시스템/조직 권한을 활용합니다.

---

## 5. `inter_domain` 프로바이더

-   `app/domains/inter_domain/device_access_management/providers.py`를 통해 이 서비스의 모든 핵심 메소드가 다른 도메인에 노출됩니다.
