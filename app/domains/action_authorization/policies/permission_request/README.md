# 접근 요청 정책 (Permission Request Policy)

## 목적
이 정책은 시스템에 제출되는 '접근 요청(Access Request)'에 대한 전체적인 유효성 검사 흐름을 조율하고 관리합니다. 사용자의 존재 여부에 따른 조건부 사용자 생성 및 다양한 검증기(Validator)들을 조합하여 요청의 정당성을 확인합니다.

## 주요 기능 및 흐름
웹페이지의 단일 '가입 요청' 폼으로부터 들어오는 요청을 처리하며, 내부적으로 계정 생성과 권한 요청 처리를 통합합니다.

1.  **사용자 존재 여부 확인 및 조건부 사용자 생성:**
    -   `user_existence_validator`를 호출하여 이메일의 존재 여부를 확인합니다.
    -   **사용자가 없는 경우:** `password`와 `username` 필수 여부 검사 후 `user_identity_provider`를 통해 새로운 비활성 사용자를 생성합니다.
    -   **사용자가 있는 경우:** `password` 필수 여부 검사 및 `user_identity_provider`를 통해 비밀번호를 검증합니다.

2.  **조직 관련 검증 (요청에 `business_registration_number`가 있는 경우):**
    -   `organization_existence_validator`를 호출하여 조직의 존재 여부를 확인합니다.
    -   `user_organization_link_validator`를 호출하여 사용자가 이미 해당 조직 내에 요청된 역할을 가지고 있는지 확인합니다.

3.  **시스템 역할 관련 검증 (요청에 `business_registration_number`가 없는 경우):**
    -   `system_role_assignment_validator`를 호출하여 사용자가 이미 해당 시스템 역할을 가지고 있는지 확인합니다.

4.  **중복 요청 검증:**
    -   `duplicate_permission_request_validator`를 호출하여, 동일한 조건의 `pending` 상태 요청이 이미 있는지 확인합니다.

5.  **요청 역할의 유효성 확인:**
    -   `user_authorization_providers`를 통해 요청된 `role_id`가 유효한 역할인지 확인합니다.

6.  **성공 시 결과 반환:**
    -   모든 검증을 통과하면 `(True, {user_object, organization_object, requested_role_object})`를 반환하여, 상위 계층(`Application`)에서 이 정보를 활용하여 최종적으로 `AccessRequest` 레코드를 생성할 수 있도록 합니다.

## 의존성
-   `validators/` 하위 디렉토리의 개별 검증기들
-   `app.domains.inter_domain`에 정의된 `user_identity_providers`, `organization_providers`, `user_authorization_providers`

## 다음 단계 (Policy 호출 후)
-   상위 계층(Application)은 이 정책의 성공적인 결과(`True, {객체들}`)를 받은 후, `access_requests_command_provider`를 호출하여 데이터베이스에 최종 `AccessRequest` 레코드를 생성합니다.