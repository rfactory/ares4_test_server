# Inter-Domain Logic

이 디렉토리는 여러 도메인 **간의** 통신을 용이하게 하는 공유 비즈니스 로직과 데이터 제공자를 포함합니다.

## 목적

이 디렉토리의 주요 목표는 **느슨한 결합(Loose Coupling)**을 강제하는 것입니다. 한 도메인(예: `accounts`)의 서비스는 다른 도메인(예: `organizations`)의 `crud`나 내부 구현 세부 정보에 직접 의존해서는 안 됩니다.

대신, 이곳에서 제공하는 안정적이고 공개된 계약(함수)에 의존해야 합니다.

## 도메인 간 통신 원칙: 서비스 계층 통신 (Service-to-Service Communication)

'도메인 간의 모든 통신은 서비스 계층을 통해 이루어져야 한다'는 원칙을 수립했습니다.

-   **나쁜 예 (결합도 높음):** `AuthService` (헤드 셰프 A)가 `user_management` 도메인의 `user_crud` (다른 팀 주방 보조 B)를 직접 호출하는 방식.
    -   이는 `AuthService`가 `user_management` 도메인의 내부 구현 상세 정보(CRUD)에 직접 의존하게 만들어, 결합도를 높이고 캡슐화를 저해합니다.
-   **좋은 예 (느슨한 결합):** `AuthService` (헤드 셰프 A)가 `inter_domain` 프로바이더를 통해 **`UserManagementService` (헤드 셰프 B)**를 호출하는 방식.
    -   `UserManagementService`는 요청을 받아 자신의 팀원인 `user_crud`에게 지시하여 데이터를 가져오고, 비즈니스 규칙을 적용한 뒤 `AuthService`에게 응답합니다.
    -   이렇게 하면 각 서비스가 자신의 도메인 비즈니스 로직을 온전히 캡슐화하고, 도메인 간에는 안정적인 서비스 인터페이스를 통해서만 소통하게 되어 아키텍처의 견고성과 유연성이 극대화됩니다.

**결론:** `inter_domain` 프로바이더는 대상 도메인의 `CRUD` 계층이 아닌, **서비스 계층의 공개된 메소드를 호출**하도록 설계되어야 합니다.

## 구조

내부 로직은 데이터를 제공하는 **대상 도메인**에 의해 구성됩니다.

- `inter_domain/<target_domain>/providers.py`

### 예시

`accounts` 서비스가 사업자등록번호로 조직 정보를 가져와야 하는 경우, `inter_domain.organizations.providers`의 함수를 호출합니다.

1. `account_service`는 `inter_domain.organizations.providers`에 있는 `get_organization_by_reg_number()`를 호출합니다.
2. `get_organization_by_reg_number` 함수는 내부적으로 `organization_crud`를 사용하여 데이터를 가져옵니다.

이 방식은 `organizations` 도메인 내부 구조가 변경되더라도 `accounts` 도메인이 영향을 받지 않도록 격리시킵니다.
