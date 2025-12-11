# Access Requests Service: Detailed Guide

## 1. 개요 (Overview)

이 서비스는 사용자가 시스템 또는 특정 조직 내에서 특정 역할을 부여받기 위해 제출하는 '접근 요청'의 전체 생명주기를 관리합니다. 사용자는 필요한 역할과 이유를 담아 요청을 생성할 수 있으며, 권한을 가진 관리자는 이 요청을 승인하거나 거절할 수 있습니다.

## 2. 주요 사용 시나리오 (Key Usage Scenarios)

### 시나리오 A: 신규 사용자가 특정 조직의 역할과 함께 가입을 요청할 때

1.  **가입 양식 제출:** 사용자가 웹사이트 가입 페이지에서 자신의 정보(이메일, 이름 등)와 함께, 소속되고 싶은 회사(조직)와 부여받고 싶은 역할(예: 'A회사'의 '기술자')을 선택하고 제출합니다.
2.  **요청 생성:** API는 `create_access_request`를 호출합니다.
    -   `user` 테이블에 해당 사용자가 없으므로, `is_active=False` 상태의 신규 사용자 계정을 먼저 생성합니다.
    -   `access_requests` 테이블에 `(user_id, requested_role_id, organization_id, status='pending')` 레코드를 생성합니다.
3.  **관리자 승인:** 'A회사'의 관리자가 자신의 대시보드에서 'pending' 상태인 이 요청을 확인하고 '승인'합니다.
4.  **요청 처리:** API는 `process_access_request`를 호출합니다.
    -   `is_active`를 `True`로 변경하여 사용자 계정을 활성화합니다.
    -   `user_organization_role` 테이블에 레코드를 추가하여 사용자에게 '기술자' 역할을 할당합니다.
    -   사용자는 이제 활성화된 계정으로 로그인하여 '기술자' 역할에 맞는 작업을 수행할 수 있습니다.

### 시나리오 B: 기존 사용자가 추가 역할을 요청할 때

1.  **역할 요청:** 이미 시스템에 로그인하여 활동중인 사용자가, 앱 내에서 더 높은 등급의 역할(예: '관리자')을 추가로 요청합니다.
2.  **요청 생성:** API는 `create_access_request`를 호출합니다. 이미 사용자가 존재하므로, `access_requests` 테이블에 `pending` 상태의 레코드만 생성합니다.
3.  **관리자 거절:** 시스템 최고 관리자가 이 요청을 확인하고, 정책상의 이유로 '거절'하며 사유를 입력합니다.
4.  **요청 처리:** API는 `process_access_request`를 호출합니다.
    -   `access_requests` 레코드의 상태를 `rejected`로 변경하고, 거절 사유를 기록합니다.
    -   사용자에게는 아무 역할도 추가되지 않습니다.

## 3. 아키텍처 및 책임 (Architecture & Responsibilities)

-   **통합 디렉토리 및 CQRS:** 접근 요청 관련 모든 로직은 이 단일 디렉토리에 위치하며, 내부적으로는 `_command` (쓰기/수정)와 `_query` (읽기) 접미사가 붙은 파일들로 책임이 분리되어 있습니다.

-   **`services/`:** `create_access_request`, `process_access_request` 등 여러 도메인의 기능을 조합하여 비즈니스 절차를 수행하는 상위 레벨 로직을 담당합니다.

-   **`crud/`:** 데이터베이스에 대한 단순한 생성, 조회, 수정, 삭제(CRUD) 작업만을 담당합니다.

-   **`schemas/`:** API의 데이터 계약 및 서비스 내부 데이터 전송에 사용되는 Pydantic 모델을 정의합니다. (`AccessRequestCreate`, `AccessRequestUpdate`, `AccessRequestRead` 등)

## 4. 외부 의존성 및 사용법 (External Dependencies & Usage)

-   이 서비스는 다른 도메인의 기능들을 적극적으로 사용하며, 반드시 해당 도메인의 **Provider**를 통해 접근합니다.
    -   **`user_identity_provider`**: 사용자 정보 조회, 생성, 활성화.
    -   **`user_authorization_provider`**: 역할 정보 조회, 역할 할당, 권한 확인.
    -   **`organization_provider`**: 조직 정보 조회.
    -   **`audit_provider`**: 모든 주요 상태 변경에 대한 감사 로그 기록.

-   **외부 노출:** 이 서비스의 모든 기능은 `inter-domain/access_requests`에 위치한 **`command_provider.py`** 와 **`query_provider.py`** 를 통해서만 외부 도메인(예: `Policy`)에 노출되어야 합니다.
