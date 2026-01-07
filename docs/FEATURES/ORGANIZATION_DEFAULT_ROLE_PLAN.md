# 최종 계획: 조직별 기본 역할 및 보호 정책 구현 (v2.0)

## 1. 목표

- 조직 생성 시, 해당 조직의 관리자 역할을 자동으로 생성한다.
- 시스템 최상위 역할(`SUPER_ADMIN`)과 각 조직의 자동 생성된 관리자 역할을 API를 통한 임의의 수정 및 삭제로부터 보호한다.

## 2. Tier 시스템 규칙 (최종 확정)

- **`tier 0`:** 시스템 최상위 역할 (`SUPER_ADMIN`). 
  - **보호 정책:** API를 통한 생성, 권한 수정, 역할 정보(이름 등) 수정, 삭제가 절대 불가하다.
  - **변경 방법:** 오직 서버 관리자의 직접적인 DB 수정으로만 변경 가능하다.

- **`tier 1`:** 조직별 자동 생성 관리자 역할.
  - **보호 정책:** 사용자가 API를 통해 임의로 권한을 수정하거나, 역할을 삭제하거나, 역할의 이름을 변경하는 것이 불가하다.
  - **생명 주기:** 해당 역할이 속한 조직이 생성될 때 함께 생성되며, 조직이 삭제될 때 함께 **Hard Delete** 된다.

- **`tier 2` 이상:** 사용자가 자유롭게 생성 및 관리할 수 있는 일반 역할.
  - **보호 정책:** 해당 역할에 대한 CRUD 권한을 가진 사용자에 의해 관리된다.

## 3. 구현 계획

### 0단계: 선행 오류 수정

1.  **`log_event_type` ENUM 추가:** `PUT /roles/{id}/permissions` API 호출 시 발생하는 `500` 오류를 해결하기 위해, `log_event_type` ENUM에 `ROLE_PERMISSIONS_UPDATED`를 추가하는 Alembic 마이그레이션을 생성하고 실행한다.

### 1단계: 역할 보호 정책 구현

1.  **정책 파일 생성/수정:**
    - **`create_role_policy.py`:** 사용자가 API를 통해 `tier`를 0 또는 1로 설정하려는 시도를 차단한다.
    - **`update_role_policy.py` (신규 생성):** `PUT /roles/{role_id}` 엔드포인트에 적용될 정책. 대상 역할의 `tier`가 0 또는 1이면, `name` 등 정보 변경을 시도할 때 `ForbiddenError` (403)를 발생시킨다.
    - **`delete_role_policy.py` (신규 생성):** `DELETE /roles/{role_id}` 엔드포인트에 적용될 정책. 대상 역할의 `tier`가 0 또는 1이면 `ForbiddenError` (403)를 발생시킨다. 또한, 역할이 현재 사용자에게 할당되어 사용 중이면 `ConflictError` (409)를 발생시킨다.
    - **`update_role_permissions_policy.py` (수정):** 대상 역할의 `tier`가 0 또는 1이면, 권한 목록 수정을 시도할 때 `ForbiddenError` (403)를 발생시키는 로직을 추가한다.
2.  **엔드포인트 적용 (`roles.py`):** `POST`, `PUT`, `DELETE` 엔드포인트가 위에서 생성/수정한 정책들을 사용하도록 수정한다.

### 2단계: 조직 관리자 역할 자동화

1.  **조직 생성 로직 수정 (`organization_command_service.py`):** `create_organization` 서비스가 조직 생성 후, 해당 조직의 기본 'Admin' 역할을 `tier=1`로 자동 생성하도록 수정한다.
2.  **조직 삭제 로직 수정 (`organization_command_service.py`):** `delete_organization` 서비스가 조직 삭제 시, 해당 조직에 속한 모든 역할(`tier 1` 포함)도 함께 삭제하도록 수정한다.

### 3단계: '비상 모드' 권한 위임 구현

1.  **상태 확인 메커니즘 구현:** 시스템의 `Prime_Admin`이 0명인지 확인하는 로직을 구현한다. (예: 역할 변경 관련 서비스 내에서 트리거)
2.  **`PermissionChecker` 수정:** '비상 모드'가 활성화되면 `System_Admin`에게 `Prime_Admin`의 권한을 부여하는 로직을 추가한다.

### 4단계: 프론트엔드 UI 수정

1.  **`CreateRoleModal.tsx`:** `scope` 필드를 현재 컨텍스트에 따라 자동 설정하고 읽기 전용으로 수정한다.
2.  **`RoleManagementPage.tsx`:** 역할 목록 테이블에서 `ID` 컬럼을 제거한다.
3.  **`RolePermissionEditModal.tsx`:** `create`, `delete` 권한에 대해 "Allowed Columns" UI를 숨긴다.
4.  **(백엔드) `common.py`:** `get_manageable_resources` API가 `id` 컬럼을 반환하지 않도록 수정한다.