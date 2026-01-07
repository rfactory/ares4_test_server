# 최종 마스터 플랜: 사용자 라이프사이클 및 거버넌스 구현 (v4.0)

## 1. 개요

본 문서는 사용자의 가입, 역할 요청(Pull), 관리자의 초대(Push), 그리고 최상위 관리자 거버넌스에 이르는 전체 사용자 생명주기 관리 기능 구현을 위한 마스터 플랜을 정의합니다.

---

## 2. 핵심 아키텍처 원칙

### 2.1. 컨텍스트 경계 (Context Boundary)

- **가장 중요한 원칙:** 모든 관리 기능(사용자 초대, 역할 부여 등)은 행위자(actor)의 현재 컨텍스트 내에서만 유효합니다.
- API 요청 시 `X-Organization-ID` 헤더의 유무로 컨텍스트가 결정됩니다.
- **System 컨텍스트** (`X-Organization-ID` 없음): `System_Admin`은 시스템 전체에 영향을 미치는 스태프를 관리합니다.
- **Organization 컨텍스트** (`X-Organization-ID` 있음): `Organization_Admin`은 해당 조직 내의 멤버만 관리합니다.
- 어떤 관리자도 자신의 컨텍스트를 벗어나 다른 조직의 멤버를 관리하거나 역할을 부여할 수 없습니다.

### 2.2. Tier 시스템 규칙

- **`tier 0` (시스템 최상위):** `System_Admin`, `Prime_Admin`.
  - **보호:** API를 통한 생성, 권한 수정, 역할 정보 수정, 삭제가 절대 불가합니다. 오직 DB 직접 수정으로만 변경 가능합니다.
- **`tier 1` (조직 최상위):** 각 조직의 자동 생성된 `Admin` 역할.
  - **보호:** 사용자가 API로 권한 수정, 이름 수정, 삭제를 할 수 없습니다.
  - **생명주기:** 조직 생성 시 함께 생성되고, 조직 삭제 시 함께 Hard Delete 됩니다.
- **`tier 2` 이상 (일반 역할):** 사용자가 자유롭게 생성하고 관리할 수 있습니다.

---

## 3. 구현 계획 (단계별)

### 1단계: 기반 작업 (시딩 및 T0 거버넌스 정책 완성)

- **구현 전략 노트 (중요):** T0 거버넌스 규칙은 최종적으로 DB에 저장된 규칙 매트릭스를 읽는 동적 '규칙 엔진'으로 구현되어야 합니다. 하지만, 현재는 규칙 엔진이 없으므로, **1단계에서는 모든 규칙을 Python 정책 파일에 하드코딩하여 기능을 우선 완성하고, 테스트가 완료되는 즉시, 이 정책들을 규칙 엔진 기반으로 리팩토링하는 2단계 작업으로 전환해야 합니다.**

1.  **시딩 스크립트 수정 (`create_super_admin.py`):**
    -   `System_Admin`과 `Prime_Admin` 역할을 `tier=0`으로 생성합니다.
    -   `role:create` 권한은 `System_Admin`에게만 부여합니다.
    -   초기 사용자 `ypkim.gs@esgroup.net`에게 `System_Admin` 역할을 할당합니다.

2.  **T0 거버넌스 정책 구현 (`update_user_roles_policy`):**
    -   `System_Admin`은 오직 `Prime_Admin` 역할만 다른 스태프에게 임명/해임할 수 있습니다.
    -   `Prime_Admin`은 `System_Admin`을 해임할 수 없지만, 다른 스태프를 `System_Admin`으로 임명할 수는 있습니다.
    -   `Prime_Admin`은 `tier > 0`인 모든 하위 역할을 자유롭게 임명/해임할 수 있습니다.

3.  **역할 보호 정책 완성:**
    -   모든 역할 관련 정책(`create`, `update`, `delete`, `update_permissions`)에 `tier` 기반 보호 로직이 완전하게 구현되었는지 최종 검토 및 수정합니다.

### 2단계: 사용자 주도 승격/가입 요청 (Pull Model)

1.  **프론트엔드 (요청 페이지):** 개인 컨텍스트에 '조직/스태프 가입 요청'을 위한 별도의 페이지를 구현합니다.
    -   **조직 검색 기능:** 사용자가 가입을 원하는 조직을 찾을 수 있도록, 조직 이름, 사업자 번호 등 다양한 식별자로 조직을 검색하는 기능을 포함합니다.
2.  **백엔드 (요청 API):** 사용자의 가입 요청(`POST /requests/join`)을 `upgrade_requests` 테이블에 기록합니다.
3.  **프론트엔드 (관리자용):** 어드민 패널에 '요청 관리' 페이지를 구현하여 보류 중인 요청을 목록으로 보여주고, 관리자가 승인/거부할 수 있게 합니다.
4.  **백엔드 (승인 API):** 관리자의 승인 요청(`POST /admin/upgrade-requests/{id}/approve`)을 처리합니다. **승인 시, 요청자에게만 유효한 일회용 인증 코드를 생성하여 이메일로 발송합니다.**

### 3단계: 관리자 주도 초대 (Push Model)

1.  **프론트엔드 (초대 UI):** 어드민 패널의 '스태프/멤버 관리' 페이지에서, **현재 컨텍스트(시스템 또는 조직)에 속한** 기존 사용자를 특정 역할로 초대하는 UI를 구현합니다.
2.  **백엔드 (초대 API):** 관리자가 특정 사용자를 역할로 초대하는 `POST /api/v1/invitations` API를 구현합니다. 이 API 역시 초대받은 사용자에게 인증 코드를 이메일로 발송합니다.

### 4단계: 컨텍스트 기반 역할 목록 연동 (신규)

#### 4.1. 목표
초대 기능 사용 시, 관리자의 현재 컨텍스트(시스템 또는 조직)에 따라 할당 가능한 역할 목록만 드롭다운에 동적으로 표시합니다.

#### 4.2. 백엔드 구현 (FastAPI)

1.  **`role_query_crud.py` 수정:** `get_multi` 메소드를 동적 필터링이 가능하도록 수정하거나, `scope`와 `organization_id`를 인자로 받는 새로운 `get_multi_by_context` 메소드를 추가합니다.
2.  **`role_query_service.py` 수정:** 서비스 계층에 CRUD의 새로운 메소드를 호출하는 로직을 추가합니다.
3.  **`role_query_provider.py` 수정:** 프로바이더 계층에 서비스의 새로운 메소드를 호출하는 로직을 추가합니다.
4.  **`roles.py` 엔드포인트 수정:** `GET /api/v1/roles/` 엔드포인트가 `scope: Optional[str] = None`, `organization_id: Optional[int] = None` 쿼리 파라미터를 받도록 수정하고, 이를 프로바이더에 전달합니다.

#### 4.3. 프론트엔드 구현 (React)

1.  **`rolesService.ts` 생성:** `panel_react/src/services/` 디렉토리에 API 호출을 위한 새 파일을 생성합니다.
    -   `getRoles(params: { scope?: string; organization_id?: number })` 함수를 구현하여, `GET /roles/` API를 쿼리 파라미터와 함께 호출합니다.
2.  **`ManageSystemUsersPage.tsx` 수정:**
    -   `useEffect` 훅을 사용하여 컴포넌트가 마운트될 때 `getRoles({ scope: 'SYSTEM' })`를 호출합니다.
    -   가져온 역할 목록을 state에 저장하고, 드롭다운 메뉴를 이 state와 연결하여 동적으로 렌더링합니다.
3.  **`ManageUsersPage.tsx` 수정:**
    -   `useAuthStore`를 사용하여 현재 활성화된 `activeContext`에서 `organizationId`를 가져옵니다.
    -   `useEffect` 훅에서 `getRoles({ organization_id: activeContext.organizationId })`를 호출합니다.
    -   가져온 역할 목록으로 드롭다운 메뉴를 동적으로 렌더링합니다.

### 5단계: 조건부 동적 규칙 엔진 및 위임 구현 (v8.2 - 최종 계획안)

#### 5.1. 신규 권한 정의 및 할당:

1.  `permissions` 테이블에 `system:context_switch` 권한을 추가합니다.
2.  `Prime_Admin` 역할에만 이 `system:context_switch` 권한을 할당합니다. `System_Admin`에게는 할당하지 않습니다.

#### 5.2. `create_super_admin.py` 시딩 수정:

1.  `governance_rules` 테이블에 다음 규칙들을 시딩합니다:
    *   **T0 역할 관리 규칙:**
        *   `Prime_Admin`과 `System_Admin` 간의 상호 임명 (인원수 제한 조건 포함).
        *   `System_Admin`은 `Prime_Admin`을 해임 가능하지만, `Prime_Admin`은 `System_Admin`을 해임 불가.
    *   **PA의 시스템 내 `tier > 1` 역할 관리 규칙:**
        *   `Prime_Admin`은 `SYSTEM` 컨텍스트에서 `tier가 1보다 큰 시스템 역할`(`scope = SYSTEM`)을 할당하거나 해임할 수 있습니다. (`tier = 1`은 조직 Admin용으로 제외)
    *   **비상 모드 규칙:** 비상 모드 시 `System_Admin`에게 `Prime_Admin`의 모든 권한을 임시 위임.
2.  **삭제:** `PrimeAdminCanSwitchContext` 거버넌스 규칙은 삭제합니다 (이제 `system:context_switch` 권한으로 관리).

#### 5.3. `governance_validator.py` 로직 강화:

1.  `evaluate_rule` 메소드에 `conditions` (예: `max_headcount`, `target_role_tier > 1`, `target_role_scope`) 처리 로직을 구현합니다.
2.  비상 모드 활성화 여부를 확인하고, 활성화 시 `System_Admin`을 `Prime_Admin`으로 간주하는 로직을 추가합니다.

#### 5.4. `switch_context_policy.py` 수정:

1.  `system:context_switch` 권한을 확인하는 `PermissionChecker` 로직으로 변경합니다.

#### 5.5. 향후 작업 명시:

1.  조직 생성 시 `OrgAdmin` 관련 규칙 동적 시딩.
2.  컨텍스트 전환을 위한 임시 JWT 발급 및 `get_current_user` 의존성 수정.
3.  JWT 보안 강화 (Refresh Token Rotation & DPoP).

### 6단계: 인증 코드를 통한 최종 승인 (공통 워크플로우)

1.  **프론트엔드 (인증 페이지):** 2단계와 3단계의 흐름을 마무리하기 위한 '인증 코드 입력' 페이지를 개인 컨텍스트에 구현합니다. 이 페이지는 조직을 검색하고 요청을 시작하는 '가입 요청' 페이지와는 명확히 구분됩니다.
2.  **백엔드 (최종 승인 API):** `POST /api/v1/invitations/accept` API를 구현합니다.
    -   **핵심 보안 로직:** 코드를 제출한 **현재 로그인한 사용자**가 **해당 코드의 원래 대상이었는지** 교차 확인 후, 최종적으로 역할을 할당하고 코드를 비활성화합니다.

---

## 8단계: JWT 보안 강화 (Refresh Token Rotation & DPoP)

### 8.1. 목표

- 현재의 단순 JWT 인증 방식의 보안 취약점을 개선하고, 최신 보안 표준을 적용합니다.
- 토큰 탈취 공격에 대한 방어력을 강화하고, 사용자 세션 관리를 보다 안전하게 만듭니다.

### 8.2. 백엔드 구현 (FastAPI)

1.  **Refresh Token 구현:**
    *   로그인 시 짧은 수명의 Access Token과 긴 수명의 Refresh Token을 함께 발급합니다.
    *   Refresh Token은 DB 또는 Redis에 안전하게 저장합니다 (사용자 ID, 만료 시간, 재사용 방지를 위한 고유 ID 등 포함).
2.  **Refresh Token Rotation:**
    *   Access Token 만료 시 Refresh Token을 사용하여 새로운 Access Token과 Refresh Token 쌍을 발급합니다.
    *   이전 Refresh Token은 사용 즉시 무효화하거나, 짧은 기간 동안 재사용을 허용하는 '원타임 토큰' 방식으로 구현하여 재사용 공격을 방지합니다.
3.  **DPoP (Demonstrating Proof-of-Possession) 구현 (선택 사항이나 권장):**
    *   클라이언트가 토큰을 소유하고 있음을 암호학적으로 증명하는 DPoP 헤더를 Access Token 요청에 포함합니다.
    *   서버는 DPoP 헤더의 유효성을 검증하여 토큰 탈취 및 재사용 공격을 방지합니다.
4.  **Token Revocation (토큰 무효화):**
    *   로그아웃 또는 보안 이벤트 발생 시 Refresh Token을 즉시 무효화하는 기능을 구현합니다.
5.  **`get_current_user` 의존성 수정:**
    *   새로운 토큰 모델에 맞춰 `get_current_user` 의존성 로직을 수정합니다 (Access Token 및 Refresh Token 검증).

### 8.3. 프론트엔드 구현 (React & Flutter)

1.  **토큰 저장:** Access Token과 Refresh Token을 안전하게 저장하는 로직을 구현합니다 (Secure Cookies, LocalStorage, Secure Storage 등).
2.  **토큰 갱신:** Access Token 만료 시 Refresh Token을 사용하여 자동으로 새로운 토큰을 요청하는 로직을 구현합니다.
3.  **DPoP 헤더 생성 (선택 사항):** DPoP 구현 시, 클라이언트에서 DPoP 헤더를 생성하여 요청에 포함하는 로직을 추가합니다.

---

## 9. 단계 9: 통합 패널 및 구독 기반 기능 분리 (구상)

### 9.1. 통합 사용자 인터페이스 (Unified Panel)

-   **목표:** 개인 사용자, 조직 멤버/관리자, 시스템 관리자 모두가 동일한 `panel_react` 애플리케이션을 사용하도록 단일 인터페이스를 제공합니다.
-   **구현:**
    -   **RBAC 기반 UI:** 사용자의 역할과 컨텍스트에 따라 보여지는 메뉴, 기능, 데이터가 동적으로 변경되어야 합니다.
    -   **컨텍스트 전환:** 여러 조직에 속하거나 시스템 관리 권한을 가진 사용자를 위해, UI 내에서 명확하게 컨텍스트를 전환하는 기능이 필요합니다.

### 9.2. 구독자 전용 접근

-   **목표:** 패널의 모든 핵심 기능은 유료 구독자에게만 제공합니다.
-   **구현:**
    -   로그인 직후, 백엔드 API를 통해 사용자의 구독 상태를 확인합니다.
    -   **구독자:** 정상적으로 패널을 사용합니다.
    -   **비구독자:** 기능이 제한된 '구독 안내' 페이지로 리디렉션합니다.

### 9.3. 제어 방식 분리 (서버 API vs. 블루투스)

-   **목표:** 구독 상태에 따라 장치 제어 방식을 분리하여 구독의 가치를 높입니다.
-   **데이터 흐름:** 구독 여부와 관계없이 모든 장치의 데이터(텔레메트리)는 서버로 전송 및 축적됩니다.
-   **구현:**
    -   **비구독자:** 모바일 앱(`ares4_flutter`)에서 블루투스(BLE)를 통해 장치를 직접 제어합니다. 서버를 통한 원격 제어 기능은 비활성화됩니다.
    -   **구독자:** 기존과 동일하게 모바일 앱 및 웹 패널에서 서버 API를 통해 장치를 원격으로 제어할 수 있습니다.
    -   **백엔드:** 장치 제어 관련 모든 API는 요청자의 구독 상태를 확인하여 비구독자의 요청을 거부해야 합니다.

---

## 10. 부록: 미완료된 이전 작업

- 상기 계획을 진행하기에 앞서, `ORGANIZATION_DEFAULT_ROLE_PLAN.md`에서 정의되었으나 아직 완료되지 않은 **'3단계: '비상 모드' 권한 위임 구현'** 작업을 먼저 완료해야 합니다.