# Ares4 인증 및 권한 관리 아키텍처 (계층형 구조)

## 1. 핵심 원칙

- **데이터 무결성 및 보존**: `Audit Logs`, `Telemetry Data` 등 모든 기록은 삭제/수정이 불가하다.
- **최소 권한 원칙**: 각 역할(Role)은 부여된 업무 수행에 필요한 최소한의 권한(Permission)만 가진다.
- **자기 관리 원칙**: 모든 사용자는 자신의 계정 정보 수정 및 삭제(탈퇴)를 오직 본인만 수행할 수 있다.
- **관리자 역할 분리 및 상호 견제**: 최상위 관리자(`Prime_Admin`, `System_Admin`) 간의 권한을 명확히 분리하고, 특정 상황에서만 서로를 견제하거나 비상 권한을 위임받는 메커니즘을 도입한다.

---

## 2. 아키텍처 구현 로드맵 및 T0 거버넌스

본 아키텍처는 아래 3단계에 걸쳐 점진적으로 구현됩니다.

- **1단계 (현재): 기본 보안 강화 및 기반 다지기**
    - `is_superuser` 직접 검사 로직을 제거하고 모든 권한 확인이 `authorization_service`를 통하도록 통일합니다. (글로벌 T0 역할은 **임시로 1명**으로 제한)
    - `devices`, `data` 도메인 등 현재 발견된 보안 문제를 해결합니다.

- **2단계 (차기): 글로벌 T0 거버넌스 구현**
    - 글로벌 `Prime_Admin`(최대 2명)과 글로벌 `System_Admin`(최대 3명)의 다수 임명을 허용합니다.
    - 이들 간의 '임명/해임 투표'를 처리하는 **모듈화된 투표 시스템**을 구현합니다.
    - 글로벌 `Prime_Admin` 부재 시, '공동 책임' 비상 모델을 적용합니다.

- **3단계 (최종): 조직별 거버넌스 확장**
    - 2단계에서 만든 투표 시스템과 RBAC 엔진을 **각 조직(테넌트)에 맞게 확장**합니다.
    - 각 조직이 자신들만의 `Organization_Prime_Admin`을 두고, 자체적으로 관리자 거버넌스를 운영할 수 있도록 구현합니다.

### 2.1. 글로벌 T0 관리자 거버넌스 (2단계 목표)

- **역할 구성 (정원)**
    - `Prime_Admin`: 최대 **2명**. 서비스 운영의 최종 책임자.
    - `System_Admin`: 최대 **3명**. 시스템 아키텍처 및 규칙의 최종 책임자.

- **임명 절차 (투표 시스템)**
    - **`System_Admin` 임명:** `Prime_Admin` 전원의 **만장일치** 투표로 비어있는 `System_Admin` 자리를 임명합니다.
    - **`Prime_Admin` 임명:** `System_Admin` 전원의 **과반수** 투표로 비어있는 `Prime_Admin` 자리를 임명합니다.

- **견제 절차 (투표 시스템)**
    - **`Prime_Admin` 해임:** `System_Admin` 전원의 **과반수** 투표로 `Prime_Admin`의 역할을 해임합니다.

- **비상 절차 (자동화)**
    - 시스템에 `Prime_Admin`이 **0명**이 되는 즉시 '비상 운영 모드'로 자동 전환됩니다.
    - 비상 모드에서는 모든 `System_Admin`에게 임시로 `Prime_Admin`의 역할 권한이 공동으로 부여됩니다.
    - 새로운 영구 `Prime_Admin`이 임명되면 비상 모드는 해제되고 임시 권한은 회수됩니다.

### 2.2. 조직별 관리자 거버넌스 (3단계 목표)

- **역할 구성 (정원)**
    - `Organization_Prime_Admin`: 각 조직 내 최대 **2명**. `System_Admin` 역할은 조직 레벨에 존재하지 않습니다.

- **관리 범위**
    - `Organization_Prime_Admin`은 소속된 조직 내의 하위 역할과 사용자만 관리합니다.

- **비상 절차 (자동화)**
    - 조직 내 `Organization_Prime_Admin`이 모두 없어지면, 해당 조직에서 **가장 오래된 스태프(역할 할당일 기준)가 자동으로 임시 `Prime_Admin`으로 승격**됩니다.

---

## 3. 데이터베이스 모델

- **`users`**: 사용자 계정 정보.
  - `id` (PK): 사용자 고유 ID
  - `username` (String, Unique): 사용자 이름
  - `email` (String, Unique): 이메일 주소
  - `password_hash` (String): 해시된 비밀번호
  - `created_at` (DateTime): 계정 생성일
  - `reset_token` (String): 비밀번호 재설정 토큰
  - `reset_token_expires_at` (DateTime): 비밀번호 재설정 토큰 만료 시간
  - `shared_secret` (String): HMAC 통신을 위한 공유 비밀키
  - `last_login` (DateTime): 마지막 로그인 시간
  - `is_active` (Boolean): 계정 활성 상태
  - `email_verification_token` (String): 이메일 인증 토큰
  - `email_verification_token_expires_at` (DateTime): 이메일 인증 토큰 만료 시간
    - **참고**: 이 필드들은 주로 Flutter 앱의 사용자 등록 및 이메일 확인 흐름에 사용되며, `admin_panel`의 관리자 승인 기반 사용자 등록 흐름에서는 직접 사용되지 않습니다.
  - `is_staff` (Boolean): 관리자 패널 접근 가능 여부
  - `is_superuser` (Boolean): 최고 관리자 권한 여부
- **`roles`**: `Prime_Admin`, `System_Admin` 등 역할의 정의.
  - `id` (PK): 역할 고유 ID
  - `name` (String, Unique): 역할 이름 (예: `prime_admin`, `general_admin`, `owner`, `viewer`, `developer`)
  - `description` (Text): 역할에 대한 설명
  - `tier` (Integer): 역할의 계층 (예: 0, 1, 2, 3)
  - `lineage` (String): 역할의 계통 (예: `Ops`, `Dev`, `User`)
  - `numbering` (Integer): 계층 및 계통 내에서의 순번
- **`permissions`**: 시스템의 모든 개별 동작에 대한 권한 정의.
  - `id` (PK): 권한 고유 ID
  - `name` (String, Unique): 권한의 고유한 이름 (예: `user:read`, `device:delete`)
  - `description` (Text): 권한에 대한 상세 설명
- **`role_permissions`**: `roles`와 `permissions` 간의 다대다(N:M) 관계를 정의하는 연결 테이블.
  - `id` (PK): 연결 고유 ID
  - `role_id` (FK to roles.id)
  - `permission_id` (FK to permissions.id)
- **`user_roles`**: `users`와 `roles` 간의 다대다(N:M) 관계를 정의하는 연결 테이블.

- **`registration_requests`**: 사용자 등록 요청 정보.
  - `id` (PK): 요청 고유 ID
  - `username` (String, Unique): 요청된 사용자 이름
  - `email` (String, Unique): 요청된 이메일 주소
  - `password_hash` (String): 해시된 비밀번호
  - `requested_at` (DateTime): 요청 시간
  - `status` (String): 요청 상태 (예: `pending`, `approved`, `rejected`)
  - `approved_by_user_id` (FK to users.id): 요청을 승인한 관리자 ID
  - `approved_at` (DateTime): 승인 시간
  - `rejection_reason` (Text): 거부 사유
  - `requested_role_id` (FK to roles.id): 요청된 역할 ID

- **`upgrade_requests`**: 사용자 역할 승격 요청 정보.
  - `id` (PK): 요청 고유 ID
  - `user_id` (FK to users.id): 요청한 사용자 ID
  - `reason` (Text): 승격 요청 사유
  - `status` (String): 요청 상태 (예: `pending`, `approved`, `rejected`)
  - `requested_at` (DateTime): 요청 시간
  - `reviewed_by_user_id` (FK to users.id): 요청을 검토한 관리자 ID
  - `reviewed_at` (DateTime): 검토 시간
  - `requested_role_id` (FK to roles.id): 요청된 역할 ID

- **`audit_logs`**: 시스템 내 사용자 및 관리자 활동 기록.
  - `id` (PK): 로그 고유 ID
  - `actor_user_id` (FK to users.id): 활동을 수행한 사용자 ID
  - `target_user_id` (FK to users.id, NULLABLE): 활동의 대상이 된 사용자 ID (예: 관리자가 특정 사용자를 변경한 경우)
  - `action` (String): 수행된 활동 (예: `user:login`, `device:created`)
  - `timestamp` (DateTime): 활동 발생 시간
  - `details` (JSON): 활동에 대한 추가 상세 정보 (예: `ip_address`, `user_agent`, 변경된 필드 값)
  - **관계**: `actor_user_id`는 `actor`라는 이름으로 `User` 모델과 관계를 맺고, `target_user_id`는 `target`이라는 이름으로 `User` 모델과 관계를 맺어, 관련 사용자 정보를 쉽게 참조할 수 있도록 합니다.

---

## 2.1. 역할 계층 구조 (Tier-based System)

- **Tier 0: 최고 관리자 (C-Level)**: 시스템의 최종 의사결정 및 관리 주체.
  - `Prime_Admin` (최고 운영 책임자)
  - `System_Admin` (최고 기술 책임자)

- **Tier 1: 총괄 관리자 (Lead / Manager)**: 각 팀의 운영 및 개발을 총괄.
  - `Operations_Lead` (운영 총괄)
  - `Development_Lead` (개발 총괄)

- **Tier 2: 실무 담당자 (Specialist / Agent)**: 각 분야의 실무를 담당.
  - `User_Support` (사용자 지원 담당)
  - `Device_Technician` (기기 기술자)
  - `Software_Engineer` (소프트웨어 엔지니어)
  - `Hardware_Engineer` (하드웨어 엔지니어)

- **Tier 3: 일반 사용자 (End-User)**
  - `Owner`

---

## 3. 권한 (Permissions) 상세 정의

시스템의 모든 개별 동작은 다음과 같은 권한으로 정의됩니다.

| 리소스 (Resource) | 권한 이름 | 설명 |
| :--- | :--- | :--- |
| **User** | `user:read` | 다른 사용자의 정보를 조회할 수 있는 권한. |
| | `user:delete:staff` | 다른 staff 계정을 삭제하는 절차를 시작할 수 있는 권한. (실제 삭제는 API 로직에 따름) |
| | `user:update:role` | 다른 staff 계정의 역할을 변경(부여/해제)할 수 있는 권한. |
| **Device** | `device:read` | 기기 정보를 조회하는 권한. |
| | `device:delete` | 기기를 비활성화/연결 해제하는 권한. |
| **Role** | `role:read` | 역할 목록 및 할당된 권한을 조회하는 권한. |
| | `role:create`, `role:update`, `role:delete` | 역할을 생성, 수정, 삭제하는 권한. |
| **Permission** | `permission:read` | 권한 목록을 조회하는 권한. |
| | `permission:create`, `permission:update`, `permission:delete` | 시스템 권한을 생성, 수정, 삭제하는 권한. |
| **Audit Log** | `audit:read` | 감사 로그를 조회하는 권한. |
| **Device Command**| `command:send` | 기기로 제어 명령을 전송하는 권한. |

* `user:create` 권한은 존재하지 않음. 계정 생성은 오직 공개된 가입 페이지를 통해서만 가능.
* `user:update` (타인 정보 수정) 권한은 존재하지 않음. 역할 수정만 별도 권한으로 분리.

---

## 4. 역할별 상세 정의 및 권한 매트릭스

- **R**: Read (조회)
- **U**: Update (수정)
- **D**: Delete (삭제)
- **C**: Create (생성)
- **X**: Execute (실행, 예: `command:send`)
- **-**: 권한 없음

| 역할 (Role) | 계통 | App Users | Devices | Audit Logs | System Roles & Permissions | Components & Hardware | Telemetry | Commands |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`Prime_Admin` (T0)** | Ops | R, U(역할), D(스태프) | R, U, D, C | R | R | R, U, D, C | R | X |
| **`System_Admin` (T0)** | Dev | R, D(`Prime_Admin`만) | R | R | R, U, D, C | R, U, D, C | R | - |
| **`Operations_Lead` (T1)** | Ops | R, U(비활성화) | R, U, C | R | - | R | R | X |
| **`Development_Lead` (T1)** | Dev | R | R | R | R | R, U, C | R | - |
| **`User_Support` (T2)** | Ops | R (제한적) | R (제한적) | - | - | - | R (제한적) | X (제한적) |
| **`Device_Technician` (T2)**| Ops | - | R, U | - | - | R | R | X |
| **`Software_Engineer` (T2)**| Dev | R | R | R | - | R | R | - |
| **`Hardware_Engineer` (T2)**| Dev | - | R | - | - | R, U, C | - | - |
| **`Owner` (T3)** | User | - | R (자신) | - | - | - | R (자신) | X (자신) |

**참고:**
- **권한 상속**: 상위 티어의 역할은 하위 티어 역할의 권한을 대부분 포함하며, 더 넓은 범위의 권한을 가집니다.
  - 예: `Operations_Lead`는 `User_Support`와 `Device_Technician`의 권한을 포함하고, 추가로 사용자 비활성화 및 기기 생성 권한을 가집니다.
- `App Users`의 `U(역할)`: 사용자의 역할을 변경하는 권한입니다. (`Prime_Admin`만 보유)
- `App Users`의 `D(스태프)`: 규칙에 따라 다른 스태프를 삭제하는 권한입니다. (`Prime_Admin`, `System_Admin`만 보유)
- `(제한적)`: 역할에 따라 조회 가능한 데이터의 범위나 종류가 제한됨을 의미합니다.
  - **`User_Support`의 `App Users: R (제한적)`**: 사용자의 `username`, `email`, `is_active` 상태만 조회 가능.
  - **`User_Support`의 `Devices: R (제한적)`**: 기기의 `nickname`, `status`, `last_seen` 등 기본 상태 정보만 조회 가능.
  - **`User_Support`의 `Telemetry: R (제한적)`**: 최근 24시간 이내의 데이터만 조회 가능.
- `(자신)`: 자기 소유의 리소스에 대해서만 권한이 있음을 의미하며, 어드민 패널이 아닌 API 접근 기준입니다.

---

## 5. 사용자 계정 관리 API 로직

### 5.1. 자기 계정 관리 API

- **`PUT /api/users/me` (자기 정보 수정)**
  - **주체**: 로그인한 모든 사용자.
  - **로직**: 인증된 사용자의 ID를 기반으로 자신의 정보를 수정한다.

- **`DELETE /api/users/me` (자기 계정 삭제/탈퇴)**
  - **주체**: 로그인한 모든 사용자.
  - **로직**: 인증된 사용자의 ID를 기반으로 자신의 계정을 삭제한다. 관련 데이터는 규정에 따라 처리하고 감사 로그를 남긴다.

### 5.2. 타인 계정 관리 API (관리자용)

- **`PUT /api/users/{user_id}/roles` (타인 역할 수정)**
  - **주체**: `Prime_Admin` 역할 보유자.
  - **권한 확인**: `user:update:role` 권한이 있는지 확인한다.
  - **로직**: 대상 사용자의 역할을 변경한다.

- **`DELETE /api/users/{user_id}` (타인 계정 삭제)**
  - **주체**: `Prime_Admin` 또는 `System_Admin` 역할 보유자.
  - **로직**:
    1. **권한 확인**: `user:delete:staff` 권한이 있는지 확인한다.
    2. **대상 확인 (일반 사용자)**: 삭제 대상이 `is_staff=False`인 일반 사용자이면, **삭제를 금지**한다.
    3. **상호 견제 로직**:
        - **A(`Prime_Admin`)가 B(`System_Admin`)를 삭제 시도**: **금지**.
        - **A(`System_Admin`)가 B(`Prime_Admin`)를 삭제 시도**: **허용**. (삭제 후 A에게 임시 `Prime_Admin` 권한 위임 및 알림 발송)
        - **A(`System_Admin`)가 B(다른 staff)를 삭제 시도**:
            - `Prime_Admin`이 시스템에 존재하면: **삭제 금지**.
            - `Prime_Admin`이 시스템에 없으면: **허용**.
    4. 모든 조건을 통과하면 삭제를 수행하고 감사 로그를 남긴다.

- **`PUT /api/users/{user_id}` (타인 정보 수정)**
  - 이 API는 타인 정보 수정을 허용하지 않는다. 역할 수정은 별도 API를 사용한다.

### 5.3. 사용자 요청 관리 API 로직 (관리자용)

사용자 등록 및 역할 승격 요청은 관리자의 검토 및 승인/거부 과정을 거칩니다.

- **`GET /api/admin/registration-requests` (등록 요청 목록 조회)**
  - **주체**: `Prime_Admin`, `System_Admin` 역할 보유자.
  - **로직**: 모든 보류 중인 사용자 등록 요청 목록을 조회한다.
- **`POST /api/admin/registration-requests/{request_id}/approve` (등록 요청 승인)**
  - **주체**: `Prime_Admin`, `System_Admin` 역할 보유자.
  - **로직**: 특정 `request_id`의 등록 요청을 승인하고, 해당 정보를 바탕으로 새로운 사용자 계정을 생성한다.
- **`POST /api/admin/registration-requests/{request_id}/reject` (등록 요청 거부)**
  - **주체**: `Prime_Admin`, `System_Admin` 역할 보유자.
  - **로직**: 특정 `request_id`의 등록 요청을 거부하고, 거부 사유를 기록한다.

- **`GET /api/admin/upgrade-requests` (승격 요청 목록 조회)**
  - **주체**: `Prime_Admin`, `System_Admin` 역할 보유자.
  - **로직**: 모든 보류 중인 역할 승격 요청 목록을 조회한다.
- **`POST /api/admin/upgrade-requests/{request_id}/approve` (승격 요청 승인)**
  - **주체**: `Prime_Admin`, `System_Admin` 역할 보유자.
  - **로직**: 특정 `request_id`의 승격 요청을 승인하고, 대상 사용자의 역할을 업데이트한다.
- **`POST /api/admin/upgrade-requests/{request_id}/reject` (승격 요청 거부)**
  - **주체**: `Prime_Admin`, `System_Admin` 역할 보유자.
  - **로직**: 특정 `request_id`의 승격 요청을 거부하고, 거부 사유를 기록한다.

---

## 6. 감사 로그 (Audit Log) 정책

### 6.1. 기록 대상
- **관리자 활동 (어드민 패널)**: 로그인, 로그아웃, 로그인 실패, 관리자 페이지 접근 (`page:view`)
- **데이터 변경 (API)**: 모든 생성(Create), 수정(Update), 삭제(Delete) 작업 (예: `role:updated`, `device:created`)
- **Flutter 앱 사용자 활동**: 
  - 계정 관리: `user:updated_self`, `user:password_changed_self`, `user:deleted_self`
  - 기기 관리: `device:claimed`, `device:unclaimed`, `device:nickname_updated`
  - 기기 제어: `device:command_sent`
  - 인증: `user:login_flutter`, `user:logout_flutter`

### 6.2. 계층별 조회 정책

`Audit Log`는 역할의 등급(Tier)에 따라 접근 범위와 데이터의 상세 수준이 차등 적용된다.

- **Tier 0 (`Prime_Admin`, `System_Admin`)**
  - **접근 범위**: 모든 로그를 조회할 수 있다.
  - **상세 수준**: 모든 컬럼과 `details` JSON의 모든 내용을 제한 없이 조회할 수 있다.

- **Tier 1 (`Operations_Lead`, `Development_Lead`)**
  - **접근 범위**: 모든 로그를 조회할 수 있다.
  - **상세 수준**: 민감 정보(예: `ip_address`, `user_agent`)가 제외된 제한된 정보만 조회할 수 있다.

- **Tier 2 (`Software_Engineer`)**
  - **접근 범위**: `system:error`, `db:migration` 등 기술적인 이벤트와 관련된 로그만 조회할 수 있다.
  - **상세 수준**: Tier 1과 동일하게 민감 정보가 제외된 제한된 정보만 조회할 수 있다.
