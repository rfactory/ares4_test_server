# DPoP 구현 및 적용 계획

## 목표

모든 외부 통신(Public API 및 Protected API)에 DPoP를 강제하여, 토큰 탈취 공격에 대한 보안을 강화한다.

## 용어 정리

- **외부 통신:** 클라이언트(React 앱)에서 서버로 오는 모든 HTTP 요청.
- **내부 통신:** 서버 내부의 서비스 간 통신.
- **공개 API (Public API):** 인증이 필요 없는 외부 통신 API (예: 로그인, 회원가입).
- **보호된 API (Protected API):** 반드시 인증(Access Token)이 필요한 외부 통신 API (예: 사용자 정보 조회).

## 단계별 실행 계획

### 1단계: 인증 진입점 DPoP 강제 적용

로그인 및 토큰 갱신 시점부터 DPoP를 필수로 요구하도록 수정합니다.

- **[완료]** `password_validator.py`를 순수 Validator로 리팩토링했습니다.
- **[완료]** `login_policy.py` 수정 완료.
- **[완료]** `refresh_token_policy.py` 수정 완료.
- **[완료]** 관련 엔드포인트(`auth.py`) 및 Provider들이 `Request` 객체를 전달하고 `async`를 사용하도록 수정했습니다.

### 2단계: 모든 보호된 API에 DPoP 강제 적용 (중앙화)

- **[완료]** `app/dependencies.py` 파일의 `get_current_user` 함수 수정 완료. (DPoP 중앙 처리)

### 3단계: 보호된 엔드포인트 감사 (Audit)

- **[완료]** 모든 보호된 API 엔드포인트에 `Depends(get_current_user)`가 적용되고 `async def`로 변경되었음을 확인했습니다.

### 3.5단계: 보안 강화 (Replay Attack 방지)

- **[완료]** **DPoP Nonce 도입** 완료.
- **[완료]** **JTI 블랙리스트 도입** 완료.

### 4단계: React 클라이언트 DPoP 구현

- **[완료]** `jose` 라이브러리를 설치했습니다.
- **[완료]** `src/utils/dpop.ts` 유틸리티 모듈을 생성하고, 서버 요구사항에 맞게 수정했습니다.
- **[완료]** `axios` 인터셉터를 구현하여 모든 요청에 DPoP 관련 헤더를 자동으로 추가하도록 했습니다.
- **[완료]** 로그인, 토큰 갱신 로직이 DPoP를 포함하여 동작하도록 수정했습니다.

### 5단계: 클라이언트 토큰 갱신 Race Condition 해결 (최종 단계)

- **문제 정의:** 여러 API 요청이 동시에 Access Token 만료(401) 응답을 받을 경우, 각 요청이 개별적으로 토큰 갱신을 시도합니다. 첫 번째 갱신 요청이 성공하면 Refresh Token이 회전(교체)되어 무효화됩니다. 이후 도착하는 다른 갱신 요청들은 이미 무효화된 Refresh Token을 사용하게 되어 `401` 오류를 받고, 이는 무한 인증 루프로 이어질 수 있습니다.

- **해결 방안:** 토큰 갱신 로직에 **잠금(Locking) 메커니즘**을 도입하여, 한 번에 하나의 토큰 갱신 요청만 처리되도록 보장합니다.
    1.  전역 변수로 `isRefreshing` 플래그(boolean)와 갱신을 기다리는 요청을 저장할 큐(`failedQueue`)를 선언합니다.
    2.  API 요청이 `401` 오류를 받으면, 먼저 `isRefreshing` 플래그를 확인합니다.
    3.  **`isRefreshing`이 `false`일 경우 (첫 번째 401 요청):**
        -   `isRefreshing`을 `true`로 설정합니다.
        -   토큰 갱신 API(`/login/refresh`)를 호출합니다.
        -   **성공 시:** 새로운 Access Token을 저장하고, `failedQueue`에 쌓인 모든 대기 요청을 새 토큰으로 재실행(resolve)합니다. 큐를 비웁니다.
        -   **실패 시:** `failedQueue`에 쌓인 모든 요청을 실패(reject) 처리하고 큐를 비웁니다. 사용자를 로그아웃 처리합니다.
        -   모든 과정이 끝나면 `isRefreshing`을 `false`로 재설정합니다.
    4.  **`isRefreshing`이 `true`일 경우 (후속 401 요청):**
        -   새로운 토큰 갱신을 시작하지 않습니다.
        -   대신, `Promise`를 생성하여 나중에 첫 번째 갱신이 완료되었을 때 실행될 수 있도록 `resolve`와 `reject` 함수를 `failedQueue`에 추가합니다.
        -   이 `Promise`를 반환하여, 원래 API 호출부가 갱신이 끝날 때까지 기다리게 만듭니다.
