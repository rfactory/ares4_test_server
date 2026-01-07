# 동적 권한 시스템 설계 (Dynamic Permission System Design) - 최종 v4

## 1. 목표

API 엔드포인트 레벨에서, 사용자의 역할(Role)과 컨텍스트(Context, 예: 특정 조직)에 기반한 동적 권한을 확인하는, 재사용 가능한 RBAC(Role-Based Access Control) 시스템을 구축한다.

- **동적 관리:** 권한은 코드에 하드코딩되지 않고, 데이터베이스에 저장되어 관리자가 UI 등을 통해 동적으로 수정할 수 있다.
- **재사용성:** 특정 권한(예: "organization:create")을 확인하는 로직을, 필요한 모든 엔드포인트에서 쉽게 가져다 쓸 수 있어야 한다.
- **컨텍스트 지원:** 시스템 전역 권한과 특정 조직 내에서의 권한을 구분하여 확인할 수 있어야 한다.
- **아키텍처 준수:**
    - `Service`는 단일 작업을 수행한다 (Hands).
    - `Validator`는 단순 판단을 내린다 (Nerves).
    - `Policy`는 여러 서비스/밸리데이터를 조율하여 복합적인 비즈니스 규칙을 결정한다 (Brain).
    - `Policy`는 다른 `Policy`를 직접 호출하지 않는다.

## 2. 핵심 개념: 의존성 주입(Dependency Injection)을 통한 권한 정책(Policy) 실행

'권한 확인'은 여러 서비스의 데이터를 조합하는 복합 로직이므로 **Policy**의 역할이다. 이 Policy를 API 엔드포인트가 실행되기 전에 먼저 통과해야 하는 '관문'으로 만들기 위해 FastAPI의 **의존성 주입(Dependency Injection)**을 사용한다. 이 "관문" 의존성이 권한 확인 Policy를 호출하여, 권한이 없으면 API 실행 자체를 차단한다.

## 3. 구현 단계 (권한 확인)

### 3.1. 1단계: `CheckUserPermissionPolicy` 생성 (The Brain)

- **목적:** '사용자가 특정 권한을 가졌는가?'라는 복합적인 비즈니스 질문에 답하는 두뇌(Brain) 역할을 하는 Policy를 만든다.
- **설명:** 이 Policy는 `user_role_assignment_query_provider`와 같은 단순 조회 서비스('Hands')를 호출하여, 필요한 데이터를 수집한 뒤, 컨텍스트(`organization_id`)에 따라 결과를 필터링하고 조합하여 최종적으로 `True` 또는 `False`를 반환하는 오케스트레이션 로직을 수행한다.
- **생성 파일:** `.../policies/permission/check_user_permission_policy.py`

### 3.2. 2단계: `PermissionPolicyProvider` 생성

- **목적:** 방금 만든 `CheckUserPermissionPolicy`를 외부(구체적으로 `dependencies.py`)에서 안전하게 호출할 수 있도록 `inter_domain`을 통해 노출시킨다.
- **생성 파일:** `.../inter_domain/policies/permission/permission_policy_provider.py`

### 3.3. 3단계: `PermissionChecker` 의존성 생성 (The Gateway)

- **목적:** FastAPI 엔드포인트의 '관문' 역할을 하는 의존성 클래스를 만든다.
- **설명:** 이 클래스는 API 요청이 들어오면, `PermissionPolicyProvider`를 호출하여 권한을 확인하고, 권한이 없으면 `403 Forbidden` 오류를 발생시켜 API 실행을 차단한다.
- **수정 파일:** `server2/app/dependencies.py`

### 3.4. 4단계: API 엔드포인트에 의존성 적용

- **목적:** `create_organization` 엔드포인트에 `PermissionChecker` 관문을 설치한다.
- **설명:** 엔드포인트의 `Depends` 목록에 `PermissionChecker("organization:create")`를 추가하여, API 본문이 실행되기 전에 권한 검사를 강제한다.
- **수정 파일:** `server2/app/api/v1/endpoints/panel.py`

### 3.5. 5단계: `create_organization_policy` 정리

- **목적:** 이제 관문에서 권한 검사가 처리되므로, 기존 Policy에서는 해당 코드를 삭제하여 책임을 명확히 분리한다.
- **수정 파일:** `.../policies/organization_management/create_organization_policy.py`

---

## 4. 컨텍스트 및 역할 관리 심화 설계

### 4.1. 목표

사용자 경험과 보안을 향상시키기 위해, 권한에 기반하여 동적으로 컨텍스트를 제공하고, 역할 할당 규칙을 명확히 한다.

### 4.2. 1단계: 동적 컨텍스트 목록 생성 (로그인 시)

- **목적:** 사용자가 로그인할 때, 자신이 접근할 수 있는 컨텍스트(개인, 조직, 시스템) 목록만 받도록 한다.
- **수정 파일:** `.../policies/authentication/login_policy.py`
- **구현:**
    1.  `login_policy`의 `execute` 함수는 로그인 성공 후, `user_role_assignment_query_provider`를 호출하여 해당 사용자의 모든 역할 할당(`assignments`) 목록을 가져온다.
    2.  이 `assignments` 목록을 분석하여 접근 가능한 컨텍스트 목록(`available_contexts`)을 동적으로 생성한다.
        -   모든 사용자는 기본적으로 'PERSONAL' 컨텍스트를 가진다.
        -   `assignment.organization_id`가 있는 경우, 해당 조직 정보를 바탕으로 'ORGANIZATION' 컨텍스트를 목록에 추가한다. (중복 제거 포함)
        -   `assignment.role.scope`가 'SYSTEM'인 역할이 있는 경우, 'SYSTEM' 컨텍스트를 목록에 추가한다.
    3.  최종 로그인 응답에 `user`, `token`과 함께 이 `available_contexts` 목록을 포함하여 프론트엔드에 전달한다.

### 4.3. 2단계: 역할 할당의 유일성 보장 (핵심 비즈니스 규칙)

- **목적:** 한 명<의 사용자는 하나의 조직 내에서 단 하나의 역할만 가질 수 있도록 보장한다.
- **구현 주체:** 사용자에게 조직 역할을 할당하는 `Policy` (예: `AssignOrganizationRolePolicy` - 신규 생성 필요)
- **구현:**
    1.  역할을 할당하기 전에, 먼저 `user_role_assignment_query_provider`를 사용하여 `(user_id, organization_id)`로 기존 할당 내역이 있는지 조회한다.
    2.  **만약 기존 할당이 있다면,** 새로운 역할로 교체하는 '업데이트(UPDATE)' 로직을 수행한다.
    3.  **만약 기존 할당이 없다면,** 새로 역할을 할당하는 '생성(CREATE)' 로직을 수행한다.
    4.  이러한 '있으면 업데이트, 없으면 생성' 로직을 통해, 데이터베이스의 `UniqueConstraint`에 의존하지 않고, 비즈니스 레벨에서 데이터의 정합성을 보장한다.

### 4.4. 3단계: 안전한 컨텍스트 전환 구현

- **목적:** 프론트엔드에서만 처리되는 불안전한 컨텍스트 전환을, 백엔드 검증을 포함하는 안전한 방식으로 개선한다.
- **API 신규 생성:** `POST /api/v1/token/switch-context` 엔드포인트를 `common.py`에 추가한다.
- **구현:**
    1.  프론트엔드 사용자가 컨텍스트 드롭다운에서 새로운 컨텍스트(예: 특정 `organization_id`)를 선택하면, 이 신규 API를 호출한다.
    2.  백엔드는 요청을 받으면, `CheckUserPermissionPolicy` 등을 재사용하여, 현재 사용자가 정말로 해당 컨텍스트에 접근할 권한이 있는지 다시 확인한다.
    3.  권한이 확인되면, 백엔드는 **해당 컨텍스트 정보(`organization_id`)가 포함된 새로운 단기 JWT 토큰**을 발급하여 프론트엔드에 돌려준다.
    4.  프론트엔드는 이 새로운 '컨텍스트 토큰'을 저장하고, 이후 모든 API 요청에 이 토큰을 사용한다.
    5.  `get_current_user` 의존성은 이 컨텍스트 토큰을 해석하여, 사용자의 신원뿐만 아니라 현재 사용자가 어떤 조직 컨텍스트에서 요청을 보내고 있는지를 명확히 알 수 있게 된다.