# 역할(Role) CRUD 기능 구현 계획 (v1.0)

## 1. 목표

'역할 관리' 페이지 내에서 `Role` 객체에 대한 전체 CRUD(생성, 조회, 수정, 삭제) 기능 구현.

## 2. 단계 (Phases)

이 프로젝트는 두 가지 주요 단계로 나뉩니다:

- **1단계: 백엔드 API 구현** (역할의 생성, 수정, 삭제 엔드포인트)
- **2단계: 프론트엔드 UI 구현** (새로운 API와 UI 컴포넌트 연결)

---

## 1단계: 백엔드 API 구현

### 작업 1.1: `POST /api/v1/roles` 구현 (역할 생성)

1.  **스키마:** `services/role_management/schemas/role_command.py`에 `RoleCreate` 요청 스키마를 추가합니다.
2.  **CRUD:** `crud/role_command_crud.py`에 `create` 메소드를 추가합니다. (`CRUDBase`에 이미 존재할 수 있음)
3.  **서비스:** `services/role_management/services/role_command_service.py`에 `create_role` 메소드를 추가합니다. 이 서비스는 중복된 역할 이름이 있는지 확인합니다.
4.  **프로바이더:** `inter_domain/role_management/role_command_provider.py`에 `create_role` 메소드를 추가합니다.
5.  **엔드포인트:** `api/v1/endpoints/roles.py`에 `POST /` 엔드포인트를 추가하고, `PermissionChecker("role:create")`로 보호합니다.

### 작업 1.2: `PUT /api/v1/roles/{role_id}` 구현 (역할 수정)

1.  **스키마:** `services/role_management/schemas/role_command.py`에 `RoleUpdate` 요청 스키마를 추가합니다.
2.  **CRUD:** `crud/role_command_crud.py`에 `update` 메소드를 추가합니다. (`CRUDBase`)
3.  **서비스:** `services/role_management/services/role_command_service.py`에 `update_role` 메소드를 추가합니다. 중복 이름 확인을 포함합니다.
4.  **프로바이더:** `inter_domain/role_management/role_command_provider.py`에 `update_role` 메소드를 추가합니다.
5.  **엔드포인트:** `api/v1/endpoints/roles.py`에 `PUT /{role_id}` 엔드포인트를 추가합니다. `PermissionChecker("role:update")`로 보호하고, `SUPER_ADMIN` 등 시스템 역할을 수정하지 못하게 하는 안전 장치를 추가합니다.

### 작업 1.3: `DELETE /api/v1/roles/{role_id}` 구현 (역할 삭제)

1.  **CRUD:** `crud/role_command_crud.py`에 `remove` 메소드를 추가합니다. (`CRUDBase`)
2.  **서비스:** `services/role_management/services/role_command_service.py`에 `delete_role` 메소드를 추가합니다.
3.  **프로바이더:** `inter_domain/role_management/role_command_provider.py`에 `delete_role` 메소드를 추가합니다.
4.  **엔드포인트:** `api/v1/endpoints/roles.py`에 `DELETE /{role_id}` 엔드포인트를 추가합니다. `PermissionChecker("role:delete")`로 보호하고, 안전 장치를 추가합니다.

### 작업 1.4: 신규 권한 시딩 (Seeding)

1.  **시딩 스크립트 수정:** `scripts/create_super_admin.py`의 `ESSENTIAL_PERMISSIONS` 딕셔너리에 `"role:create"`와 `"role:delete"` 권한을 추가합니다.

---

## 2단계: 프론트엔드 UI 구현

### 작업 2.1: "역할 생성" UI 구현

1.  **버튼:** `RoleManagementPage.tsx`에 "Create New Role" 버튼을 추가합니다.
2.  **모달 컴포넌트:** `src/components/`에 `CreateRoleModal.tsx` 컴포넌트를 새로 생성합니다. 이 모달은 `name`, `description`, `scope`(System/Organization) 필드를 가진 폼을 포함합니다.
3.  **API 함수:** `roleApi.ts`에 `createRole` 함수를 새로 생성합니다.
4.  **통합:** `RoleManagementPage.tsx`에서 버튼, 모달, API 호출을 함께 연결합니다.

### 작업 2.2: "역할 삭제" UI 구현

1.  **버튼:** `RoleManagementPage.tsx`의 역할 목록 테이블 각 행에 "삭제" `IconButton`을 추가합니다.
2.  **확인 다이얼로그:** 버튼 클릭 시, 삭제 여부를 재확인하는 다이얼로그를 표시합니다.
3.  **API 함수:** `roleApi.ts`에 `deleteRole` 함수를 새로 생성합니다.
4.  **통합:** 버튼, 다이얼로그, API 호출을 연결합니다. 성공적으로 삭제되면 역할 목록을 새로고침합니다.

### 작업 2.3: "역할 수정" UI 구현 (선택적)

1.  **UI:** `RoleDetailsPanel.tsx`에 "Edit" 버튼을 추가합니다.
2.  **모달 또는 인라인 수정:** 클릭 시, 역할의 `name`과 `description`을 수정할 수 있게 합니다.
3.  **API 함수:** `roleApi.ts`에 `updateRole` 함수를 새로 생성합니다.
