# Two-Factor Code Validator

## 1. 목적 (Purpose)

이 `TwoFactorCodeValidator`는 2단계 인증(2FA) 과정에서 사용자가 제출한 인증 코드의 유효성을 검증하는 단일 책임을 가지는 컴포넌트입니다.

---

## 2. 단일 책임 원칙 (Single Responsibility)

이 검증기의 유일한 책임은 **"제출된 2FA 코드가 해당 사용자의 DB에 저장된 코드와 일치하며, 만료되지 않았는가"** 라는 질문에 `True` 또는 `False`로 답하는 것입니다.

-   **포함하는 책임:**
    -   사용자 이름으로 사용자 정보 조회 (DB에 저장된 2FA 코드와 만료 시간 확인 목적)
    -   제출된 코드와 DB의 코드 비교
    -   코드 만료 시간 확인
    -   검증 실패 시, 감사 로그(`audit_log`) 기록

-   **포함하지 않는 책임:**
    -   최종 로그인 성공 및 토큰 발급 (이는 `Service`의 역할)
    -   사용된 2FA 코드를 DB에서 삭제하는 로직 (이는 `Service`의 역할)
    -   로그인 흐름 전체를 제어 (이는 `Policy`의 역할)

---

## 3. 사용법 (Usage)

이 검증기는 반드시 `AuthenticationPolicy`와 같은 `Policy` 계층에서 호출되어야 합니다. 일반적으로 `PasswordValidator`가 성공적으로 통과한 후, 해당 유저의 2FA가 활성화되어 있을 경우에 호출됩니다.

### `validate` 메소드 시그니처

```python
validate(self, db: Session, *, username: str, code: str) -> Tuple[bool, Optional[str]]
```

-   **입력 (Inputs):**
    -   `db`: SQLAlchemy 세션
    -   `username`: 검증할 사용자의 이름
    -   `code`: 사용자가 제출한 6자리 2FA 코드

-   **출력 (Outputs):**
    -   **성공 시:** `(True, None)`
    -   **실패 시:** `(False, "에러 메시지 문자열")`

---

## 4. 아키텍처 내에서의 흐름

```
+---------------------------+      +---------------------------+      +----------------------------+
|   Authentication Policy   | ---> |  TwoFactorCode Validator  |      | Fetches User via           |
| (after password success)  |      |      (This component)     |      | UserIdentity Provider      |
+---------------------------+      +---------------------------+      | Compares code & expiry     |
        (username, code)                  | (True/False)                | Logs audit on failure      |
                                          V                           +----------------------------+
                               +----------------------------+
                               |  Calls TokenIssuingService |
                               |  Calls 2faClearStateService|
                               +----------------------------+
```

1.  **`AuthenticationPolicy`** 는 `PasswordValidator` 검증 성공 후, 사용자의 2FA가 활성화된 것을 확인합니다.
2.  `Policy`는 이 **`TwoFactorCodeValidator`** 를 호출하여 사용자가 제출한 `code`를 검증합니다.
3.  `TwoFactorCodeValidator`는 `UserIdentity` Provider를 통해 사용자 DB에 저장된 코드 정보와 비교하여 결과를 `Policy`에게 반환합니다.
4.  `Policy`는 이 결과가 `True`일 경우, 토큰 발급 `Service`와 사용된 2FA 코드를 DB에서 삭제하는 `Service`를 순차적으로 호출하여 최종 로그인을 완료시킵니다.
