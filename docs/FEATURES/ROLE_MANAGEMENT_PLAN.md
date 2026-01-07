# [PLAN] 동적 역할/권한 관리 페이지 구현 계획서 (v1.9)

> **v1.9 변경 이력**: 전체 기능 구현에 앞서, '컨텍스트 전환' 기능이 선행되어야 함을 인지하고, 이를 위한 'Phase 0'을 최우선 순위로 추가함.

## 1. 구현 단계 (Phased Approach)

> **설계 의도**: 복잡성을 관리하고, 각 단계의 결과물을 명확히 하기 위해 전체 구현을 4단계로 분리한다. 컨텍스트 전환(기반) -> API(데이터) -> UI(화면) -> 필터링 적용(로직) 순으로 진행한다.

### [ ] Phase 0: 컨텍스트 전환 기능 구현 (선행 작업)
- **목표**: 사용자가 자신이 속한 여러 조직 중 하나를 '현재 작업 컨텍스트'로 선택하고, 시스템 전체가 이를 인지하도록 하는 기반을 마련한다.
- [ ] **Task 0.1 (Backend):** `GET /api/v1/users/me/contexts` API 생성 (사용자의 모든 컨텍스트 목록을 역할 정보와 함께 반환)
- [ ] **Task 0.2 (Frontend):** `auth.ts`의 `Context` 타입을 확장하여 `organizationId`, `roleName` 등 추가 정보 포함
- [ ] **Task 0.3 (Frontend):** `authStore`가 `availableContexts`와 `activeContext`를 저장하도록 확장
- [ ] **Task 0.4 (Frontend):** 모든 페이지 상단에 '컨텍스트 전환 드롭다운' UI 구현 (Task 0.1 API 사용)
- [ ] **Task 0.5 (Frontend):** 모든 API 호출 시, `activeContext`의 `organizationId`를 헤더(예: `X-Organization-ID`)에 담아 전송하도록 수정

### [ ] Phase 1: 백엔드 API 구현 (권한 관리)
- [ ] **Task 1.1:** `POST /login` API가 컨텍스트별 구조화된 권한 객체를 반환하도록 수정
- [ ] **Task 1.2:** `GET /api/v1/roles` API 생성
- [ ] **Task 1.3:** `GET /api/v1/permissions` API 생성
- [ ] **Task 1.4:** `GET /api/v1/manageable-resources` API 생성
- [ ] **Task 1.5:** `GET /api/v1/roles/{role_id}/permissions` API 생성
- [ ] **Task 1.6:** `PUT /api/v1/roles/{role_id}/permissions` API 생성 (안전 장치 포함)

### [ ] Phase 2: 프론트엔드 UI 구현 (권한 관리)
- [ ] **Task 2.1:** `authStore`가 구조화된 권한 객체를 저장하도록 확장
- [ ] **Task 2.2:** 사이드바 메뉴가 컨텍스트에 따라 동적으로 렌더링되도록 수정
- [ ] **Task 2.3:** `PermissionsPage.tsx` 생성 및 라우팅
- [ ] **Task 2.4:** 역할 목록 및 권한/ABAC '조건부 빌더' UI 구현
- [ ] **Task 2.5 (보안):** ABAC 규칙 JSON 입력에 대한 Sanitization 및 스키마 기반 검증

### [ ] Phase 3: 필터링 적용 로직 구현
- [ ] **Task 3.1:** `PermissionChecker`가 ABAC 규칙을 읽고 평가하도록 수정
- [ ] **Task 3.2:** 서비스 계층이 평가된 필터 조건을 동적 쿼리로 변환하도록 수정 (SQL 인젝션 방지 로직 포함)
- [ ] **Task 3.3:** API 응답이 `allowed_columns`에 따라 동적으로 필드를 필터링하도록 수정

---

## 2. 핵심 API 명세 및 설계 의도 (Phase 0, 1)

### `GET /api/v1/users/me/contexts` (신규, 최우선 구현)
- **설명**: 현재 로그인한 사용자가 접근할 수 있는 모든 컨텍스트의 목록을 조회한다.
- **응답 예시**:
  ```json
  {
    "contexts": [
      { "uniqueId": "personal", "name": "Personal Space", "type": "PERSONAL", "organizationId": null, "roleName": null },
      { "uniqueId": "system", "name": "System Admin", "type": "SYSTEM", "organizationId": null, "roleName": "SUPER_ADMIN" },
      { "uniqueId": "org-123", "name": "ESGroup - Admin", "type": "ORGANIZATION", "organizationId": 123, "roleName": "ORG_ADMIN" },
      { "uniqueId": "org-456", "name": "Ares4 Test - Viewer", "type": "ORGANIZATION", "organizationId": 456, "roleName": "VIEWER" }
    ]
  }
  ```
- **의도**: 프론트엔드가 하드코딩 없이, 사용자별로 동적인 컨텍스트 전환 UI를 구성하고, 각 컨텍스트에 맞는 `organizationId`를 후속 API 호출에 사용할 수 있도록 모든 정보를 제공한다.

### `POST /api/v1/login/access-token` (수정)
- **설명**: 로그인 성공 시, 컨텍스트별로 그룹화된 구조적인 권한 객체를 반환한다.
- **응답 예시**:
  ```json
  {
    "user": {
      "permissions": {
        "system": ["role:read"],
        "organizations": {
          "org_id_A": ["device:update"],
          "org_id_B": ["device:read"]
        }
      }
    }
  }
  ```
- **의도**: 프론트엔드가 로그인 직후, 모든 컨텍스트에 대한 사용자의 권한을 미리 파악하여, 동적 UI(메뉴 등)를 구성할 수 있게 한다.

### `PUT /api/v1/roles/{role_id}/permissions`
- **필요 권한**: `role:update` (오직 `System_Admin`만 보유)
- **핵심 안전 장치 (비즈니스 로직)**:
  1.  **규칙: 순수 ABAC 기반 계층 관리**: `tier` 컬럼 대신, `role:manage` 권한과 이 권한에 연결된 `filter_condition`을 통해 상위 역할이 하위 역할만 관리할 수 있도록 강제한다. 이를 통해 최고 관리자의 '셀프 권한 상승'을 원천 차단한다.
  2.  **규칙: 권한 상속의 부분집합 원칙**: 요청자는 자신이 가지지 않은 권한을 하위 역할에 부여할 수 없다.
  3.  **규칙: 조직(스코프) 교차 접근 방지**: `ORGANIZATION` 스코프의 역할을 수정할 때, 요청자와 대상 역할의 `organization_id`가 일치하는지 확인한다.

---

## 3. ABAC 규칙 상세 정의 및 구현 방안

### 3.1. 정책 결합 알고리즘 (Policy Combination Algorithm)
- **규칙**: 사용자가 여러 역할을 가질 경우, 각 역할에서 파생된 모든 필터 조건(`filter_condition`)은 **논리적 AND로 결합**되고, `allowed_columns`는 **교집합(Intersection)**으로 결합된다.
- **의도**: 'Deny-overrides' 원칙을 채택하여, 항상 가장 제한적인 규칙을 적용함으로써 보안을 강화한다.

### 3.2. 속성 소스 (Attribute Source)
- **user.***: 인증된 사용자의 JWT 토큰 `claims` 또는 DB의 `users` 테이블에서 가져온다. (예: `user.department`)
- **resource.***: API 요청의 대상이 되는 리소스 객체에서 가져온다. (예: `resource.country`)
- **environment.***: API 요청 시점의 서버 환경에서 가져온다. (예: `environment.time_of_day`)

---

## 4. 베스트 프랙티스 및 장기 목표

- **API 개선**: `PUT` 외에 `PATCH` API를 도입하여, 역할 권한의 부분 업데이트를 지원한다.
- **테스트**: `PermissionChecker` 및 동적 쿼리 생성 로직에 대한 속성 기반 테스트(Property-based testing)를 구축한다.
- **버전 관리**: 역할/권한 변경 사항에 대한 이력 추적(Immutable History) 시스템 도입을 검토한다.
- **외부 정책 엔진**: OPA(Open Policy Agent) 등을 도입하여 정책 평가 로직을 중앙에서 관리하는 아키텍처를 고려한다.
- **고급 거버넌스**: 이 기본 관리 기능이 안정화된 이후, 투표/비상절차/정원제한 등 고급 거버넌스 기능을 별도 프로젝트로 구현한다.