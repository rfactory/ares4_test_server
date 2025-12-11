# Services 도메인 아키텍처 가이드라인

## 1. 핵심 원칙: 단일 책임 원칙 (Single Responsibility Principle, SRP)

**모든 서비스 모듈은 단 하나의 주요 책임(a single primary responsibility)을 가져야 합니다.**

이 원칙을 구현하기 위해, `services` 도메인은 모든 기능의 책임을 **CQRS (Command Query Responsibility Segregation)** 에 따라 다음과 같이 명확히 분리합니다.

-   **조회 (Query):** 데이터의 상태를 변경하지 않고, 오직 데이터를 읽고 조회하는 책임만을 가집니다.
-   **명령 (Command):** 데이터의 상태를 변경하는 생성(Create), 수정(Update), 삭제(Delete) 책임만을 가집니다.

하나의 기능(예: `audit`)은 이 두 가지 책임을 모두 가질 수 있지만, 코드 내에서는 `_query` 와 `_command` 접미사를 통해 명확하게 분리되어야 합니다. 기능의 특성에 따라 둘 중 하나의 책임만 가질 수도 있습니다.

## 2. 표준 디렉토리 구조

모든 서비스 디렉토리는 다음 하위 디렉토리를 포함해야 합니다. 단, 기능의 책임에 따라 일부(예: `_command` 또는 `_query`)만 존재할 수 있습니다.

-   `/crud`: 데이터베이스 모델과 직접 상호작용하는 데이터 접근 계층(CRUD 객체)을 포함합니다.
-   `/schemas`: 데이터 유효성 검사, 직렬화 및 전송을 위한 Pydantic 모델을 포함합니다.
-   `/services`: CRUD 계층에 대한 호출을 조율하고 비즈니스 로직을 수행하는 서비스 계층을 포함합니다.

## 3. 의존성 규칙

-   **내부:** 서비스 내에서 의존성 흐름은 `services` -> `crud` 입니다. 스키마는 양쪽 모두에서 사용될 수 있습니다.
-   **외부:** 서비스의 기능은 **반드시** `app/domains/inter_domain` 디렉토리에 위치한 **Provider**를 통해서만 외부에 노출되어야 합니다.
-   **직접 임포트 금지:** 다른 도메인은 서비스 내의 파일을 직접 임포트해서는 안 됩니다.

## 4. 명명 및 구조 규칙 (Naming & Structure Convention)

모든 서비스는 '신규 통합 구조'를 따라야 합니다. 이는 기능별로 디렉토리를 통합하고, 그 안에서 파일 이름으로 책임을 분리하는 방식입니다.

- **서비스 디렉토리:** 기능의 이름을 딴 단일 디렉토리 (예: `audit`, `access_requests`)
- **하위 디렉토리:** 각 서비스 디렉토리는 `crud`, `schemas`, `services` 디렉토리를 포함합니다.
- **파일 이름:** 각 하위 디렉토리 내의 파일들은 책임에 따라 `_<command|query>` 접미사를 사용하여 분리합니다.
    - **서비스 파일:** `services/<feature_name>_<command|query>_service.py` (예: `access_request_command_service.py`)
    - **CRUD 파일:** `crud/<feature_name>_<command|query>_crud.py` (예: `access_request_command_crud.py`)
    - **스키마 파일:** `schemas/<feature_name>_<command|query>.py` (예: `access_request_command.py`)

## 5. 핵심 아키텍처 철학 및 개발 가이드라인

모든 서비스 도메인 개발자는 다음의 아키텍처 원칙과 흐름을 반드시 이해하고 준수해야 합니다.

### 5.1. 계층별 책임 (Separation of Concerns): "Policy는 두뇌, Service는 손과 발"

-   **Policy 계층 (`action_authorization`):** "누가, 어떤 조건에서, 무엇을 할 수 있는가"를 결정하는 모든 비즈니스 규칙과 인가(Authorization) 로직의 유일한 진실의 원천입니다.
-   **Service 계층 (`services`):** **어떠한 비즈니스/인가 로직도 포함해서는 안 되는** '멍청한(Dumb)' 데이터 처리 계층입니다. 오직 `Policy`로부터 명시적인 지시만 받아 수행합니다.
-   **CRUD 계층 (`services`):** `Service`의 지시를 받아 실제 데이터베이스와 통신하는 가장 말단의 계층입니다.

### 5.2. 개발 워크플로우: 스키마 우선 접근법

모든 개발은 데이터 계약(스키마) 정의에서 시작하며, 단일 책임 원칙에 따라 각 파일을 생성합니다.

1.  **스키마 정의 (`schemas/`):** 책임에 따라 `_command.py` 및/또는 `_query.py` 파일을 생성하여 데이터 계약을 정의합니다.
2.  **CRUD 구현 (`crud/`):** 스키마를 기반으로 `_command_crud.py` 및/또는 `_query_crud.py` 파일을 생성하여 DB 상호작용 로직을 구현합니다.
3.  **서비스 구현 (`services/`):** CRUD를 호출하는 `_command_service.py` 및/또는 `_query_service.py` 파일을 생성합니다.
4.  **Provider 노출 (`inter-domain/`):** 외부 도메인에 기능을 노출할 `command_provider.py` 및/또는 `query_provider.py` 파일을 생성합니다.
5.  **Policy에서 사용 (`action_authorization/policies/`):** 생성된 Provider들을 조합하여 최종 비즈니스 로직을 완성합니다.

### 5.3. 서비스 간 상호작용 예시

`Service`가 다른 도메인의 `Service` 기능을 호출해야 할 경우, 아래 예시와 같이 반드시 `inter-domain` Provider를 통해야 합니다.

**예시:** `AccessRequestCommandService`가 로그 기록을 위해 `Audit` 서비스 호출
```python
# 위치: .../services/access_requests/services/access_request_command_service.py

# 올바른 방법: 다른 도메인의 Provider를 import 한다.
from ...inter_domain.audit.audit_command_provider import audit_command_provider

class AccessRequestCommandService:
    def create_access_request(self, ..., actor_user: User):
        # 1. 자신의 핵심 책임(CRUD 호출)을 수행
        db_obj = access_request_crud_command.create(...)
        
        # 2. 다른 도메인의 기능이 필요할 경우, Provider를 통해 호출
        audit_command_provider.log(db=db, actor_user=actor_user, ...)
```

### 5.4. 절대적 가이드라인

> **경고: 이 규칙들은 반드시 지켜져야 하며, 임의로 우회하거나 위반해서는 안 됩니다.**

-   **규칙 1:** `Service` 또는 `CRUD` 계층에 권한 검사, 비즈니스 규칙, 컨텍스트 인식 로직을 **절대로 추가하지 마시오.**
-   **규칙 2:** `Service`는 다른 `Service`를 직접 `import`할 수 없으며, 모든 도메인 간 통신은 **반드시 `inter-domain` Provider를 통해야 합니다.**
-   **규칙 3:** 모든 인가 로직은 **반드시 `Policy` 계층에서 구현되어야 합니다.**
-   **규칙 4:** 모든 신규 서비스 및 리팩토링은 **반드시 '신규 통합 구조'(예: `services/audit/`)를 따라야 합니다.**

### 5.5. 추가 아키텍처 원칙 (Additional Architectural Principles)

-   **삭제 정책 (Deletion Policy)**: `remove` 또는 `delete` 기능을 구현할 때는, 이 작업이 데이터베이스에서 레코드를 완전히 삭제(Hard Delete)할지, `is_active` 플래그를 변경하는 등 상태만 변경(Soft Delete)할지를 신중하게 결정해야 합니다. 다른 데이터와 관계를 맺고 있거나, 작업 이력을 보존해야 할 가치가 있다면 소프트 삭제를 우선적으로 고려합니다.

-   **로깅 정책 (Logging Policy)**:
    -   **감사 로그(`audit_log`)**: 사용자의 로그인 실패, 리소스의 생성/수정/삭제 등, 보안상 의미가 있거나 상태를 변경하는 **'명령(Command)'** 작업은 감사 로그를 기록하는 것을 원칙으로 합니다.
    -   **예외적 감사 로깅**: 단순 **'조회(Query)'** 작업은 기본적으로 감사 로그를 기록하지 않습니다. 다만, 조회하는 데이터가 매우 민감하여 '누가 데이터를 읽었는가'를 추적해야 할 필요가 있을 경우, **`Policy` 계층의 판단**에 따라 예외적으로 감사 로그를 기록할 수 있습니다.
