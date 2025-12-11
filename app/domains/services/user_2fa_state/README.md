# User 2FA State Service Domain

## 1. 목적 (Purpose)

이 `user_2fa_state` 서비스 도메인은 2단계 인증(2FA) 과정에서 사용되는 일회성 인증 코드의 상태를 데이터베이스에 저장하고 삭제하는 단일 책임을 가집니다.

---

## 2. 단일 책임 원칙 (Single Responsibility)

이 서비스의 유일한 책임은 **"특정 사용자의 2FA 인증 상태(토큰, 만료시간)를 관리하는 것"** 입니다.

-   **포함하는 책임:**
    -   안전한 난수 코드를 생성.
    -   생성된 코드와 만료 시간을 사용자의 DB 레코드에 저장 (`crud` 계층 호출).
    -   사용된 코드를 사용자의 DB 레코드에서 삭제 (`crud` 계층 호출).

-   **포함하지 않는 책임:**
    -   생성된 코드를 이메일로 발송하는 책임 (이는 별도의 `email` 서비스의 역할).
    -   제출된 코드를 검증하는 책임 (이는 `TwoFactorCodeValidator`의 역할).
    -   언제 코드를 생성하고 삭제할지 결정하는 책임 (이는 `Policy`의 역할).

---

## 3. 구조 (Structure)

-   **`schemas/`**: 2FA 상태를 설정하거나 삭제할 때 필요한 데이터(예: 사용자 ID)의 구조를 정의합니다.
-   **`crud/`**: 실제 데이터베이스의 `User` 모델에 `email_verification_token`과 `email_verification_token_expires_at` 필드를 업데이트하고 `db.commit()`을 호출하는 DB 상호작용 로직을 포함합니다.
-   **`services/`**: `crud` 계층을 호출하여 2FA 상태 관리 로직을 수행하는 `User2faStateCommandService`를 포함합니다.

---

## 4. 아키텍처 내에서의 흐름

1.  **코드 생성 시:** `AuthenticationPolicy`가 `PasswordValidator` 검증 후 2FA가 필요하다고 판단하면, 이 `User2faStateCommandService`의 `set_code`와 같은 메소드를 호출합니다. 서비스는 코드를 생성하여 `crud`를 통해 DB에 저장하고, 생성된 코드를 `Policy`에 반환합니다. 그 후 `Policy`는 이 코드를 `EmailService`에 넘겨 발송을 지시합니다.

2.  **코드 삭제 시:** `AuthenticationPolicy`가 `TwoFactorCodeValidator` 검증 성공 후, 최종 로그인을 완료하기 직전에 이 `User2faStateCommandService`의 `clear_code`와 같은 메소드를 호출하여 사용된 일회성 코드를 DB에서 삭제하도록 지시합니다.
