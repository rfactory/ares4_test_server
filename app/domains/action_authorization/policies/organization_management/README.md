# Organization Management Policies

이 디렉토리는 조직(Organization)의 생성, 수정, 삭제와 같은 핵심 라이프사이클 이벤트를 관리하는 Policy들을 정의합니다.

각 Policy는 아키텍처 원칙에 따라 '두뇌' 역할을 수행하며, 비즈니스 규칙의 최종적인 집행과 트랜잭션의 일관성을 보장합니다.

## 아키텍처 패턴: Policy-Driven Orchestration

모든 작업은 다음과 같은 흐름으로 `Policy`에 의해 지휘(Orchestration)됩니다.

1.  **API Endpoint**: 프론트엔드로부터의 HTTP 요청을 받아, 적절한 `Policy`를 호출합니다.
2.  **Policy**: 작업의 전체 흐름을 관리합니다.
    a.  **권한 검증 (Authorization)**: `PermissionValidator` 등을 호출하여 행위자가 이 작업을 수행할 권한이 있는지 확인합니다.
    b.  **데이터 검증 (Validation)**: `organization_business_registration_uniqueness` 등 여러 `Validator`들을 호출하여 데이터의 정합성과 비즈니스 규칙을 검증합니다.
    c.  **실행 (Execution)**: 모든 검증을 통과하면, `inter-domain` Provider를 통해 `Service`를 호출하여 실제 데이터 조작을 지시합니다.
    d.  **감사 (Auditing)**: `Service`가 성공적으로 작업을 완료하면, 그 결과를 바탕으로 `AuditCommandService`를 호출하여 감사 로그를 기록합니다.
    e.  **트랜잭션 관리**: 이 모든 과정은 단일 트랜잭션으로 관리되며, `Policy`가 성공적으로 완료된 후 API 엔드포인트에서 최종 `commit`이 이루어집니다.

## 포함될 Policies

### 1. `create_organization_policy.py`

- **역할**: 새로운 조직을 생성하는 전체 프로세스를 담당합니다.
- **실행 흐름**:
    1. `permission_validator.validate(user, permission_name="organization:create")`를 호출하여 권한을 확인합니다.
    2. `validate_organization_type_exists.validate(id=org_in.organization_type_id)`를 호출하여 조직 유형의 유효성을 확인합니다.
    3. `validate_unique_business_registration.validate(number=org_in.business_registration_number)`를 호출하여 사업자 번호의 중복 여부를 확인합니다.
    4. `organization_command_provider.create_organization(org_in=...)`을 호출하여 조직 생성을 실행하고, `Service` 내부에서 실행 로그가 기록되도록 합니다.
    5. 성공적으로 생성된 `Organization` 객체를 반환합니다.

### 2. `update_organization_policy.py` (예정)

- **역할**: 기존 조직의 정보를 수정하는 전체 프로세스를 담당합니다.
- **실행 흐름**:
    1. `permission_validator`를 통해 수정 권한을 확인합니다.
    2. `organization_existence_validator`를 통해 수정할 조직이 실제로 존재하는지 확인합니다.
    3. 변경하려는 데이터의 유효성을 검증합니다 (예: 수정하려는 사업자 번호가 다른 조직과 중복되지 않는지).
    4. `organization_command_provider.update_organization(...)`을 호출하여 수정을 실행하고, `Service` 내부에서 변경 전/후 데이터에 대한 감사 로그가 기록되도록 합니다.

### 3. `delete_organization_policy.py` (예정)

- **역할**: 조직을 삭제하는 전체 프로세스를 담당합니다.
- **실행 흐름**:
    1. `permission_validator`를 통해 삭제 권한을 확인합니다.
    2. `organization_existence_validator`를 통해 삭제할 조직이 실제로 존재하는지 확인합니다.
    3. `organization_command_provider.delete_organization(...)`을 호출하여 삭제를 실행하고, `Service` 내부에서 삭제된 데이터에 대한 감사 로그가 기록되도록 합니다.
