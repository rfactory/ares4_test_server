# `authentication` 도메인 설계 문서

## 1. 도메인의 목적 및 책임

`authentication` 도메인은 **"사용자가 누구인지"**를 확인하고 증명하는, 즉 **"인증(Authentication)"** 과 관련된 모든 책임을 가집니다.

-   **주요 책임:**
    -   사용자의 자격 증명(ID/비밀번호) 검증
    -   2단계 인증(2FA) 코드 발송 및 검증
    -   인증 성공 시, 접근 토큰(Access Token) 발급

-   **포함하지 않는 책임:**
    -   사용자 정보 자체의 관리 (이는 `user_identity` 도메인의 책임)
    -   발급된 토큰을 사용한 API 접근 권한 확인 (이는 `authorization`의 책임)

---

## 2. 핵심 설계 원칙

### 2.1. 도메인 분리

`authentication` 도메인은 사용자 정보가 필요한 경우에도 `user_identity` 도메인의 CRUD나 데이터베이스 모델에 직접 접근하지 않습니다. 대신, `inter_domain` 프로바이더를 통해 `UserIdentityService`가 제공하는 공개된 인터페이스만을 사용합니다.

- **흐름:** `AuthService` → `inter_domain Provider` → `UserIdentityService`

이를 통해 `user_identity` 도메인의 내부 구현이 변경되어도 `authentication` 도메인은 영향을 받지 않는, 느슨한 결합(Loose Coupling)을 유지합니다.

---

## 3. 권한 모델 (Permission Model)

- **공개 엔드포인트:** `login` 및 `verify_2fa` API는 시스템에 접근하려는 모든 사용자가 호출할 수 있는 공개된 엔드포인트입니다.
- **자격 증명 기반 보안:** 이 도메인의 보안은 역할 기반 권한 검사(RBAC)가 아닌, 사용자가 제공한 자격 증명(비밀번호, 2FA 코드)의 유효성을 검증하는 것에 의존합니다.

---

## 4. 주요 기능 및 작동 방식

### 4.1. `AuthService.login(username, password)`

-   **역할:** 사용자 로그인 프로세스의 첫 단계를 처리합니다.
-   **작동 방식:**
    1.  `inter_domain` 프로바이더를 통해 `UserIdentityService`에게 `username`에 해당하는 사용자 정보 조회를 요청합니다.
    2.  사용자가 없거나 비밀번호가 일치하지 않으면, 로그인 실패를 감사 로그에 기록하고 `PermissionDeniedError`를 발생시킵니다.
    3.  비밀번호가 일치하면, 로그인 성공을 감사 로그에 기록합니다.
    4.  만약 해당 사용자의 `is_two_factor_enabled` 플래그가 `True`이면, 이메일로 2FA 코드를 발송하고 토큰 발급 없이 "2FA 코드가 필요합니다"라는 메시지를 반환합니다.
    5.  2FA가 비활성화된 사용자라면, 즉시 접근 토큰(Access Token)을 발급하여 반환합니다.

### 4.2. `AuthService.verify_2fa(username, code)`

-   **역할:** 2단계 인증 코드의 유효성을 검증하고 최종적으로 로그인을 완료합니다.
-   **작동 방식:**
    1.  `inter_domain` 프로바이더를 통해 `username`에 해당하는 사용자 정보를 조회합니다.
    2.  데이터베이스에 저장된 `email_verification_token`과 사용자가 제출한 `code`를 비교합니다.
    3.  코드가 유효하지 않거나 만료되었다면, `PermissionDeniedError`를 발생시킵니다.
    4.  코드가 유효하면, 사용된 토큰을 DB에서 삭제하고 2FA 인증 성공을 감사 로그에 기록합니다.
    5.  최종적으로 접근 토큰(Access Token)을 발급하여 반환합니다.

---

## 5. 향후 확장 방향

이 도메인은 다음과 같은 인증 관련 기능들이 추가될 때 확장될 수 있습니다.

-   **비밀번호 재설정 기능:** 비밀번호 재설정 토큰을 발급하고 검증하는 API. 관련 스키마는 `authentication/schemas`에 추가됩니다.
-   **소셜 로그인 기능:** Google, Kakao 등 외부 OAuth 제공자를 통한 인증 기능.
