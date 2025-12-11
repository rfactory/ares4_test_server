# Authentication Policy

## 1. 목적 (Purpose)

이 `AuthenticationPolicy`는 사용자 인증(Authentication)과 관련된 모든 비즈니스 로직과 흐름을 총괄하는 '두뇌' 역할을 수행합니다. 사용자의 로그인 및 2단계 인증(2FA) 절차의 전체 오케스트레이션을 책임집니다.

---

## 2. 책임과 역할 (Role & Responsibilities)

이 Policy는 `Validator`를 통해 '조건'을 확인하고, 그 결과에 따라 어떤 `Service`를 호출하여 '행동'을 수행할지 결정합니다.

-   **주요 책임:**
    -   `login` 정책: 비밀번호 검증 후, 2FA 필요 여부를 판단하고 다음 단계를 지시합니다.
    -   `verify_2fa` 정책: 2FA 코드 검증 후, 최종 로그인을 완료하고 토큰을 발급하도록 지시합니다.
    -   성공/실패에 대한 최종적인 감사 로그를 기록합니다.

-   **포함하지 않는 책임:**
    -   비밀번호가 올바른지 직접 확인하는 로직 (이는 `PasswordValidator`의 책임)
    -   2FA 코드가 유효한지 직접 확인하는 로직 (이는 `TwoFactorCodeValidator`의 책임)
    -   JWT 토큰을 직접 생성하는 로직 (이는 `TokenCommandService`의 책임)
    -   DB에 2FA 상태를 직접 저장/삭제하는 로직 (이는 `User2faStateCommandService`의 책임)

---

## 3. 핵심 흐름 (Core Flows)

### 3.1. `login(username, password)` 흐름

1.  **`PasswordValidator` 호출:** `username`과 `password`가 유효한지 검증을 요청합니다.
2.  **검증 실패 시:** `Validator`가 기록한 감사 로그 외에 추가 처리 없이 즉시 에러를 반환하고 종료합니다.
3.  **검증 성공 시:** `UserIdentity` Provider를 통해 해당 유저의 `is_two_factor_enabled` 상태를 확인합니다.
4.  **2FA 비활성화 시:**
    a. `USER_LOGIN_SUCCESS` 감사 로그를 기록합니다.
    b. `TokenCommandService`를 호출하여 접근 토큰을 발급받습니다.
    c. 토큰을 반환합니다.
5.  **2FA 활성화 시:**
    a. `User2faStateCommandService`를 호출하여 DB에 저장할 2FA 코드를 생성하고, 생성된 코드를 돌려받습니다.
    b. `EmailService`(가칭)를 호출하여 사용자에게 코드를 발송합니다.
    c. "2FA 코드가 필요합니다" 메시지를 반환합니다.

### 3.2. `verify_2fa(username, code)` 흐름

1.  **`TwoFactorCodeValidator` 호출:** `username`과 `code`가 유효한지 검증을 요청합니다.
2.  **검증 실패 시:** 즉시 에러를 반환하고 종료합니다.
3.  **검증 성공 시:**
    a. `USER_2FA_VERIFIED` 감사 로그를 기록합니다.
    b. `User2faStateCommandService`를 호출하여 사용된 코드를 DB에서 삭제하도록 지시합니다.
    c. `TokenCommandService`를 호출하여 최종 접근 토큰을 발급받습니다.
    d. 토큰을 반환합니다.
