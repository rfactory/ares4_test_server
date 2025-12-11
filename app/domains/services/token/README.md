# Token Service Domain

## 1. 목적 (Purpose)

이 `token` 서비스 도메인은 시스템의 다른 부분(주로 `AuthenticationPolicy`)의 요청에 따라 JSON Web Tokens (JWT)를 생성하는 단일 책임을 가집니다.

---

## 2. 단일 책임 원칙 (Single Responsibility)

이 서비스의 유일한 책임은 **"주어진 사용자 데이터에 대해 유효한 접근 토큰(Access Token)을 발급하는 것"** 입니다.

-   **포함하는 책임:**
    -   `app.core.security.create_access_token` 유틸리티를 사용한 JWT 생성
    -   설정값에 따른 토큰 만료 시간 적용

-   **포함하지 않는 책임:**
    -   사용자 인증 또는 자격 증명 검증 (이는 `Validator`의 역할)
    -   토큰 발급 여부 결정 (이는 `Policy`의 역할)
    -   데이터베이스와의 모든 상호작용

---

## 3. 구조 (Structure)

-   **`schemas/`**: `Token`이나 `TokenData`와 같이, 토큰 생성에 필요하거나 생성된 토큰의 데이터 구조를 정의하는 Pydantic 모델을 포함합니다.
-   **`services/`**: 실제 토큰 생성 로직을 포함하는 `TokenCommandService`를 포함합니다.
-   **`crud/`**: 이 서비스는 DB와 상호작용하지 않으므로, `crud` 디렉토리는 존재하지 않습니다.

---

## 4. 아키텍처 내에서의 흐름

`AuthenticationPolicy`가 모든 검증(`PasswordValidator`, `TwoFactorCodeValidator` 등)을 성공적으로 마친 후, 최종적으로 이 `TokenCommandService`를 호출하여 사용자에게 발급할 접근 토큰을 생성합니다.

```
+---------------------------+      +---------------------------+      +-------------------------+
|   Authentication Policy   | ---> |   Token Command Provider  | ---> |   Token Command Service |
| (after all validations) |      | (in inter_domain)         |      |     (This service)      |
+---------------------------+      +---------------------------+      +-------------------------+
```
