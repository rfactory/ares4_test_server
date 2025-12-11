# `user_settings` 도메인 설계 문서

## 1. 도메인의 목적 및 책임

`user_settings` 도메인은 **사용자 계정의 개별 설정을 관리**하는 '전문가 서비스'입니다.

-   **주요 책임:**
    -   사용자의 2단계 인증(2FA) 활성화/비활성화 상태 변경 (`toggle_2fa`)

-   **포함하지 않는 책임:**
    -   사용자 계정 자체의 CRUD (이는 `user_identity` 도메인의 책임)
    -   사용자 인증(로그인) 로직 (이는 `authentication` 도메인의 책임)

---

## 2. 핵심 설계 원칙

### 2.1. 단일 책임 원칙 (Single Responsibility Principle)

-   `UserSettingsService`는 오직 '사용자 설정 변경'이라는 단일 책임만 가집니다.

### 2.2. 외부 의존성 관리

-   이 도메인은 사용자 정보를 직접 조회하거나 수정하지 않습니다. 대신 `inter_domain` 프로바이더를 통해 `user_identity` 서비스에 사용자 정보 조회를 요청합니다.
-   설정 변경 이벤트는 `inter_domain` 프로바이더를 통해 `audit` 서비스에 기록됩니다.
-   **흐름:** `UserSettingsService` → `inter_domain Provider` → `UserIdentityService` / `AuditService`

---

## 3. 권한 모델 (Permission Model)

- **소유자 전용(Owner-Only):** 이 도메인의 모든 기능은 API 계층에서 `get_current_user` 의존성을 통해 전달된, **현재 인증된 사용자 본인**에 대해서만 작동합니다.
- 다른 사용자의 설정을 변경할 수 없으며, 별도의 역할 기반 권한(예: `settings:write`)을 요구하지 않습니다.

---

## 4. 주요 기능 및 작동 방식

### 4.1. `UserSettingsService.toggle_2fa(current_user)`

-   **역할:** 현재 로그인된 사용자의 2단계 인증(2FA) 설정을 켜거나 끕니다.
-   **작동 방식:**
    1.  `inter_domain` 프로바이더를 통해 `user_identity_providers.get_user()`를 호출하여 DB에 있는 최신 사용자 정보를 가져옵니다.
    2.  해당 사용자의 `is_two_factor_enabled` 속성 값을 반전시킵니다 (`True` → `False`, `False` → `True`).
    3.  변경 사항을 데이터베이스에 커밋합니다.
    4.  `inter_domain` 프로바이더를 통해 `audit_providers.log()`를 호출하여 `USER_2FA_ENABLED` 또는 `USER_2FA_DISABLED` 이벤트를 기록합니다.

---

## 5. API 엔드포인트 (`api/endpoints_settings.py`)

-   **`POST /users/settings/me/toggle-2fa`**: 현재 로그인된 사용자의 2FA 설정을 토글합니다. (`get_current_user` 의존성을 통해 사용자를 식별하므로 별도의 `user_id`가 필요 없습니다.)
