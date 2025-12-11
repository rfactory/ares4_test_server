# `server2` 도메인 리팩토링 워크플로우 원칙

이 문서는 `server2` 프로젝트의 도메인 리팩토링을 수행하는 엄격한 워크플로우를 정의합니다. 이 원칙들은 복잡한 의존성 변경을 최소화하고, 코드의 일관성과 안정성을 유지하며, 점진적인 개선을 통해 프로젝트의 건강을 보장하기 위함입니다.

---

## 0. 도메인 역할에 따른 디렉토리 구조 (Application vs. Services)

도메인은 그 역할에 따라 두 가지 유형으로 분류되며, 명확한 구분을 위해 서로 다른 상위 디렉토리에 위치합니다.

### 0.1. `app/domains/services/`
- **역할:** '전문가(Specialist)' 또는 '단일 기능' 도메인.
- **설명:** 다른 도메인에 거의 의존하지 않고 자신의 전문 분야에 대한 핵심 기능을 제공하는 도메인입니다. 이들은 다른 여러 도메인에 의해 호출되는 '재료'와 같습니다.
- **예시:** `authentication`, `audit`, `user_identity`, `user_settings`, `access_requests`, `user_authorization`, `organizations`.

### 0.2. `app/domains/application/`
- **역할:** '지휘자(Orchestrator)' 또는 '워크플로우' 도메인.
- **설명:** 그 자체의 핵심 로직보다는 여러 '전문가 서비스'들을 `inter_domain` 프로바이더를 통해 호출하고, 그 결과를 조합하여 하나의 완성된 비즈니스 워크플로우를 제공하는 도메인입니다.
- **예시:** `user_management`.

---

## 1. '활성' 도메인 경로 최종 확정

- `authentication`, `audit`, `organizations` 등 구현이 완료된 전문가 서비스 도메인은 `app/domains/services/` 아래에 위치합니다.
- `user_management` 등 오케스트레이터 도메인은 `app/domains/application/` 아래에 위치합니다.

---

## 2. 도메인별 순차적 리팩토링

- 의존성이 낮은 하위 레벨의 '전문가 서비스'부터 리팩토링하고, 의존성이 높은 '오케스트레이터'를 마지막에 리팩토링합니다.
- 리팩토링 과정에서 도메인 간 통신은 반드시 `inter_domain` 프로바이더를 통해 이루어지도록 수정합니다.

---

## 3. 핵심 원칙: 상대 경로(Relative Imports) 사용

-   각 도메인 내부의 파일들은 가급적 **상대 경로(Relative Imports)**를 사용하여 서로를 임포트합니다.

---

## 4. 의존성 관리: `inter_domain` 프로바이더 활용

-   도메인 간의 통신은 **`app/domains/inter_domain`** 프로바이더를 통해서만 이루어집니다.
-   서비스는 다른 서비스의 CRUD나 서비스를 직접 임포트하지 않습니다.
-   프로바이더는 대상 도메인의 서비스 계층 메소드를 호출합니다.

---

## 5. 상세 아키텍처 및 권한 원칙 (Detailed Architecture & Permission Principles)

### 5.1. 계층별 역할 원칙 (Role Principles by Layer)

- **CRUD 계층:** 순수한 데이터 접근(CRUD)만을 담당하며, 권한 검사나 비즈니스 로직을 포함하지 않습니다.
- **Dependencies 계층:** FastAPI의 의존성 주입 시스템을 위한 것이며, API 엔드포인트에서만 사용됩니다. 서비스 계층은 이를 직접 사용하지 않고, API 계층에서 전달받은 값을 파라미터로 사용합니다.
    - **전역 의존성 (`app/dependencies.py`):** `get_db`, `get_current_user` 등 모든 도메인에서 공통적으로 사용하는 의존성.
    - **도메인 특화 의존성 (`domain/dependencies/`):** 특정 도메인의 API 내에서만 재사용되는 복잡한 로직이 있을 경우에만 선택적으로 생성합니다.
- **서비스 계층(Service Layer):** 모든 권한 검사, 비즈니스 로직, 복잡한 제약 조건(필터링, 정렬 등) 처리를 담당하는 유일한 계층입니다.

### 5.2. 컬럼 및 로우 레벨 보안 (Column & Row-Level Security)
- **컬럼 레벨 보안:** **서비스 계층**에서 호출자의 역할에 따라 각기 다른 Pydantic 응답 스키마(예: `UserResponseForAdmin`, `UserResponseForSupport`)를 사용하여 반환되는 데이터의 컬럼을 제한합니다.
- **로우 레벨 보안:** **서비스 계층**에서 `current_user`의 속성(예: `organization_id`)을 기반으로 데이터베이스 쿼리에 `filter` 조건을 동적으로 추가하여, 사용자에게 허용된 데이터 행(row)만 반환합니다.
- **C/U/D에 대한 RLS 적용:** 생성/수정 시, 생성/수정하려는 데이터가 자신의 권한 범위(예: 자신의 조직 ID)를 벗어나는지 검사하는 로직을 **서비스 계층**에 추가합니다.

### 5.3. 역할 관리 원칙 (Role Management Principles)
- **최상위(T0) 역할 - 불변성 (Immutability):** `Prime_Admin`, `System_Admin` 역할의 핵심 속성(예: `max_headcount`)은 시스템 거버넌스의 근간이므로 API를 통해 수정할 수 없습니다. 이 값들은 코드 레벨에서 고정되거나, 서버 시작 시 초기화됩니다. **(상세한 T0 역할의 종류 및 정원은 `docs/ARCHITECTURE/AUTH_ARCHITECTURE.md` 문서를 참조합니다.)**
- **하위(T1 이하) 역할 - 가변성 (Mutability):** `Development_Lead` 등 T1 이하의 역할들은 운영 필요에 따라 `role:update` 권한을 가진 관리자에 의해 유연하게 수정될 수 있습니다. (예: 설명 변경, 권한 추가/삭제)

---

## 6. 최종 검증 단계 (Final Verification Step)

모든 도메인의 분리 및 리팩토링이 완료된 후, 반드시 다음을 검증합니다.

- **감사 로그 기록 검증:** 새로 생성되거나 수정된 모든 서비스 도메인의 주요 메소드가 `inter_domain` 프로바이더를 통해 `audit` 서비스의 `log` 기능을 올바르게 호출하는지 최종적으로 검토합니다.
- **권한 모델 검증:** 모든 도메인의 `README.md`에 '권한 모델' 섹션이 명시되어 있으며, 이 내용이 `AUTH_ARCHITECTURE.md` 및 실제 코드 구현과 일치하는지 검증합니다.
