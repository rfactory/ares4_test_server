# 사용자 범위 `nickname` 기반 식별자 정책

## 1. 개요

이 문서는 장치를 식별하고 필터링하는 데 `id`나 `uuid` 대신, 사용자가 지정하는 `nickname`을 사용하는 정책과 구현 방안을 정의합니다. 이 정책의 핵심은 `nickname`의 유일성을 데이터베이스 레벨이 아닌, **각 사용자 범위 내에서 어플리케이션 레벨로 보장**하는 것입니다.

---

## 2. 정책 상세

### 2.1. 기본 `nickname` 생성

-   **시점:** `device_provisioning` 서비스에서 새로운 장치를 프로비저닝하고 `device_access_management` 서비스의 `link_device_to_user`를 호출하여 최초 소유권을 부여할 때.
-   **로직:** 장치의 **'모델명-장치ID'** 형식으로 초기 `nickname`을 자동 생성하여 저장합니다. (예: `ARES-4-123`)

### 2.2. `nickname` 유일성 보장 (사용자 범위)

-   **시점:** 사용자가 `device_access_management` 서비스의 `update_device_nickname` 메소드를 통해 장치의 `nickname`을 수정할 때.
-   **로직:**
    1.  API는 변경하려는 `user_id`, `device_id`, 그리고 `new_nickname`을 받습니다.
    2.  서비스는 `user_device_link_crud`를 통해 해당 `user_id`를 가진 사용자가 소유한 **다른 모든 장치**의 `nickname` 목록을 조회합니다.
    3.  `new_nickname`이 이 목록에 이미 존재한다면, `DuplicateEntryError`와 같은 에러를 발생시켜 등록을 거부합니다.
    4.  중복되지 않는다면, `nickname` 수정을 허용합니다.

### 2.3. `nickname`은 필수값

-   `nickname` 필드는 빈 문자열(`""`)이나 `null`이 될 수 없습니다. `link_device_to_user` 및 `update_device_nickname` 서비스 메소드에서 이 유효성을 검사해야 합니다.

### 2.4. `nickname` 기반 필터링

-   **API:** `GET /users/me/devices?nickname=내주방조명`과 같이, 특정 사용자의 컨텍스트 내에서 `nickname`을 기준으로 장치를 조회하는 기능을 제공해야 합니다.
-   **로직:** `device_access_management` 서비스의 `get_visible_devices`와 같은 메소드는 `nickname` 파라미터를 받아, `user_device_link_crud`를 통해 `user_id`와 `nickname`이 모두 일치하는 `UserDevice` 관계를 조회합니다.
