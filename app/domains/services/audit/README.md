# Audit Service: Architectural Guidelines

이 문서는 `audit` 서비스의 아키텍처를 설명하며, `server2`의 모든 신규 서비스가 따라야 할 **표준 개발 워크플로우와 가이드라인**을 제시합니다.

## 1. 핵심 철학: "Policy는 두뇌, Service는 손과 발"

-   **`Policy` 계층 (The Brain - `action_authorization` 도메인 소속):**
    -   "누가, 어떤 조건에서, 무엇을 할 수 있는가"를 결정하는 모든 비즈니스 규칙과 인가(Authorization) 로직의 유일한 진실의 원천입니다.
    -   여러 `Service`와 `Validator`를 오케스트레이션하여 하나의 완전한 비즈니스 트랜잭션을 구성합니다.

-   **`Service` 계층 (The Hands - `services` 도메인 소속):**
    -   복잡한 비즈니스 규칙이나 권한 검사 로직을 포함해서는 안 되지만, 시스템 안정성을 위해 **'방어적 확인(Defensive Check)'**은 포함할 수 있는 데이터 처리 계층입니다.
    -   **'방어적 확인'**이란, 상위 계층(`Policy`)에서 모든 검증을 통과했더라도, 서비스가 동작하기 위한 최소한의 전제 조건(예: 전달받은 ID에 해당하는 데이터가 DB에 실제로 존재하는지)을 확인하는 것을 의미합니다. 이는 잘못된 ID 전달과 같은 예외적인 상황으로부터 시스템을 보호하는 '2차 방어막' 역할을 합니다.
    -   이러한 방어적 확인 외에는, 오직 상위 계층으로부터 "이 조건으로 데이터를 가져와" 또는 "이 데이터로 저장해" 와 같은 명시적인 지시만 받아 수행합니다.

## 2. 표준 개발 워크플로우: 스키마 우선 접근법 (Schema-First Approach)

모든 서비스 개발은 데이터 계약(Data Contract)인 스키마를 정의하는 것에서부터 시작합니다.

### 1단계: 스키마 정의 (The Data Contract)

1.  **위치:** `services/<feature_name>/schemas/`
2.  **파일 생성:** 책임을 분리하여 `_command.py` 와 `_query.py` 두 개의 파일을 생성합니다.
3.  **내용:**
    -   `_command.py`: 데이터 생셩(`Create`) 및 수정(`Update`)에 사용될 Pydantic 모델을 정의합니다.
    -   `_query.py`: 데이터 조회(`Read`) 및 응답(`Response`)에 사용될 Pydantic 모델을 정의합니다.

### 2단계: CRUD 구현 (The Fingers)

1.  **위치:** `services/<feature_name>/crud/`
2.  **파일 생성:** `_command_crud.py`와 `_query_crud.py` 파일을 생성합니다.
3.  **내용:**
    -   `_command_crud.py`: `Create`, `Update`, `Delete` 등 DB 상태를 변경하는 메소드만 구현합니다.
    -   `_query_crud.py`: `get`, `get_multi` 등 DB 상태를 조회만 하는 메소드를 구현합니다.

### 3단계: 서비스 구현 (The Hands)

1.  **위치:** `services/<feature_name>/services/`
2.  **파일 생성:** `_command_service.py`와 `_query_service.py` 파일을 생성합니다.
3.  **내용:** 각 서비스 파일은 자신과 책임이 동일한 CRUD 파일을 `import`하여 해당 메소드를 호출하는 단순한 래퍼(wrapper) 역할을 합니다.

### 4단계: Provider 노출 (The Interface)

1.  **위치:** `inter-domain/<feature_name>/`
2.  **파일 생성:** `command_provider.py` 와 `query_provider.py` 파일을 생성합니다.
3.  **내용:** 각 Provider 파일은 방금 만든 서비스의 기능을 외부 도메인에 노출하는 안정적인 인터페이스 역할을 합니다.

### 5단계: Policy에서 사용 (The Brain)

-   개발된 서비스의 Provider는 `Policy` 계층에서 최종적으로 사용됩니다.
-   `Policy`는 `Active Context`와 `Permission`을 확인하고, 그 결과에 따라 어떤 Provider의 어떤 메소드를 호출할지 결정합니다.

## 3. `audit` 서비스의 최종 구조

이 워크플로우를 따라 완성된 `audit` 서비스의 최종 구조는 다음과 같으며, 이는 모든 신규 서비스가 따라야 할 표준입니다.

```
# 1. 서비스 계층
server2/app/domains/services/audit/
├── crud/
│   ├── audit_command_crud.py
│   └── audit_query_crud.py
├── schemas/
│   ├── audit_command.py
│   └── audit_query.py
└── services/
    ├── audit_command_service.py
    └── audit_query_service.py

# 2. Provider 인터페이스 계층
server2/app/domains/inter-domain/audit/
├── command_provider.py
└── query_provider.py

# 3. Policy/Validator 두뇌 계층
server2/app/domains/action_authorization/
├── policies/audit_access/policy.py
└── validators/permission/validator.py
```

## 4. 감사 로깅 정책 (Audit Logging Policy)

모든 서비스는 보안 및 규정 준수를 위해 데이터 변경 사항을 추적해야 하지만, 로깅의 범위와 방식은 작업의 종류에 따라 달라야 합니다.

### 4.1. 쓰기 작업 (Create, Update, Delete)

-   **원칙**: 데이터의 상태를 변경하는 모든 쓰기 작업은 **반드시 감사 로그를 기록해야 합니다.**
-   **구현**: `_command_service.py` 파일 내의 해당 메소드(예: `create_...`, `update_...`, `delete_...`)가 CRUD 작업을 수행한 직후, `audit_command_provider`의 구조화된 메소드(`log_creation`, `log_update`, `log_deletion`)를 호출하여 로그를 기록합니다.
-   **책임**: 로그 기록의 책임은 해당 데이터 변경을 수행하는 **서비스 계층**에 있습니다.

### 4.2. 읽기 작업 (Read)

-   **원칙**: 데이터의 상태를 변경하지 않는 일반적인 읽기 작업은, 과도한 로그 생성과 시스템 부하를 방지하기 위해 **기본적으로 감사 로그를 기록하지 않습니다.**
-   **예외적 로깅**: 하지만, 특정 데이터가 매우 민감하여 '누가 그 데이터를 읽었는지'를 반드시 기록해야 할 필요가 있을 수 있습니다. 이러한 예외적인 경우의 판단과 로그 기록 책임은 서비스 계층이 아닌 **`Policy` 계층**에 있습니다.
-   **구현**: 민감 데이터 조회를 오케스트레이션하는 `Policy`는, `_query_service.py`를 호출하여 데이터를 조회한 직후, 이것이 로깅이 필요한 특별한 경우라고 판단하면 `audit_command_provider.log_creation` 메소드 등을 직접 호출하여 '읽기 이벤트'에 대한 로그를 생성해야 합니다. (예: `resource_name="SensitiveDataReadEvent"`)
