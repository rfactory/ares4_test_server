# Password Validator

## 1. 목적 (Purpose)

이 `PasswordValidator`는 제출된 사용자 이름과 비밀번호의 유효성을 검증하는 단일 책임을 가지는 컴포넌트입니다.

---

## 2. 단일 책임 원칙 (Single Responsibility)

이 검증기의 유일한 책임은 **"제출된 비밀번호가 해당 사용자의 저장된 비밀번호 해시와 일치하는가"** 라는 질문에 `True` 또는 `False`로 답하는 것입니다.

-   **포함하는 책임:**
    -   사용자 이름으로 사용자 정보 조회
    -   `app.core.security.verify_password`를 사용한 비밀번호와 해시 비교
    -   검증 실패 시, 감사 로그(`audit_log`) 기록

-   **포함하지 않는 책임:**
    -   로그인 성공 후 토큰 발급 (이는 `Service`의 역할)
    -   2단계 인증(2FA) 확인 (이는 별도의 `Validator`의 역할)
    -   어떤 조건에서 로그인을 허용할지 결정 (이는 `Policy`의 역할)

---

## 3. 사용법 (Usage)

이 검증기는 반드시 `Policy` 계층에서 호출되어야 합니다. API 엔드포인트에서 직접 호출해서는 안 됩니다.

### `validate` 메소드 시그니처

```python
validate(self, db: Session, *, username: str, password: str) -> Tuple[bool, Optional[str]]
```

-   **입력 (Inputs):**
    -   `db`: SQLAlchemy 세션
    -   `username`: 검증할 사용자의 이름
    -   `password`: 사용자가 제출한 평문 비밀번호

-   **출력 (Outputs):**
    -   **성공 시:** `(True, None)`
    -   **실패 시:** `(False, "에러 메시지 문자열")`

---

## 4. 아키텍처 내에서의 흐름

```
+-----------------------+      +---------------------------+      +-----------------------+
|   Application Layer   | ---> |   Authentication Policy   | ---> |   Password Validator  |
| (e.g., /login API)    |      | (in action_authorization) |      | (This component)      |
+-----------------------+      +---------------------------+      +-----------------------+
        (password)                    (password)                            | (True/False)
                                                                            V
                                     +--------------------------------------+
                                     | Fetches User via UserIdentity Provider |
                                     | Compares hash via Core Security Util   |
                                     | Logs audit on failure                  |
                                     +--------------------------------------+
```

1.  **API 계층**이 사용자로부터 `username`과 `password`를 받습니다.
2.  API는 **`AuthenticationPolicy`** 를 호출하며 이 값들을 전달합니다.
3.  `AuthenticationPolicy`는 로그인 흐름의 첫 단계로, 이 **`PasswordValidator`** 를 호출합니다.
4.  `PasswordValidator`는 `UserIdentity` 도메인 Provider를 통해 사용자 정보를 조회하고, 비밀번호를 검증한 뒤 그 결과를 `Policy`에게 반환합니다.
5.  `Policy`는 이 결과를 바탕으로 2FA를 진행할지, 토큰 발급 `Service`를 호출할지 등의 다음 단계를 결정합니다.
