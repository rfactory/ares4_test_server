# [기능] 조직 관리를 위한 모달 대시보드

## 1. 개요 (무엇을 만들고 어떻게 작동하는가)

이 문서는 시스템 관리자가 특정 조직을 효과적으로 관리할 수 있도록 돕는 "조직 관리 모달 대시보드" 기능의 상세 구현 계획을 설명합니다. 기존에는 조직 목록에서 특정 조직을 관리하려면 별도의 페이지로 이동해야 했으나, 이 기능이 구현되면 시스템 관리자는 메인 조직 목록 페이지를 떠나지 않고도 모달 창 안에서 선택된 조직의 모든 관리 기능을 수행할 수 있게 됩니다. 이는 사용자 경험을 향상시키고 작업 효율성을 높일 것입니다.

**작동 방식:**
-   **UI:** 모달 대시보드는 중앙 집중식 "기능 레지스트리(Feature Registry)"를 기반으로 하는 모듈식 확장 가능 아키텍처로 구축됩니다. 이 레지스트리는 조직이 가질 수 있는 모든 관리 기능(예: 멤버, 장치, 설정 등)을 정의합니다. 대시보드는 이 레지스트리를 읽어 탐색 메뉴(예: 탭)와 콘텐츠를 동적으로 생성합니다. 이 설계는 향후 '조직' 관련 기능이 추가될 때, 해당 기능이 모달 대시보드와 전체 페이지 조직 뷰 모두에 자동으로 나타나도록 보장합니다.
-   **백엔드:** `system:context_switch` 권한을 가진 시스템 관리자가 모달을 통해 특정 조직의 컨텍스트에 들어갈 때, 백엔드는 "임시 관리자 티켓" 개념을 JWT 클레임에 담아 해당 관리자에게 임시적인 관리 권한을 부여합니다. 이 방식은 실제 조직 멤버 목록에는 표시되지 않으면서, 시스템 관리자가 그 조직의 관리자처럼 행동하여 문제를 해결하거나 작업을 수행할 수 있도록 합니다. 이 임시 권한으로 수행되는 모든 작업은 기존 권한 체크를 거치며, 감사 로그에 기록되어 추적 가능합니다.

---

## 2. 상세 구현 계획

### **1단계: 백엔드 - 임시 관리자(JWT 기반) 및 API 기반 구축**

*   **[완료]** **1-1. 컨텍스트 전환을 위한 신규 인증 엔드포인트 생성:** `auth.py`에 `POST /api/v1/auth/context-switch` 엔드포인트를 추가하여 임시 JWT를 발급하는 기능을 구현했습니다.
*   **[완료]** **1-2. `PermissionChecker` 기능 강화 (JWT 클레임 검사):** `dependencies.py`를 수정하여, API 요청 시 `temp_org_id` 클레임을 확인하고 `system:context_switch` 권한을 검사하도록 로직을 강화했습니다.
*   **[완료]** **1-3. `GET /organizations/{id}` 엔드포인트 생성:** `organizations.py`에 단일 조직의 상세 정보를 조회하는 API를 구현했습니다.
*   **[완료]** **1-4. 초기 대시보드 API 생성:** 대시보드 기능에 필요한 `GET /organizations/{id}/members` 등의 API가 이미 존재함을 확인했습니다.

### **2단계: 프론트엔드 - 플러그인 방식의 기능 아키텍처 구축**

*   **목표:** 조직의 다양한 관리 "기능" 또는 "모듈"을 정의하는 중앙 집중식 기능 레지스트리를 구축하여, UI 확장성을 보장합니다.

*   **[완료]** **2-1. 기능 레지스트리 생성:** `featureRegistry.ts` 파일을 생성하고 `OrganizationFeature` 인터페이스를 정의했습니다.
*   **[완료]** **2-2. 임시 기능 컴포넌트 생성:** `OrgDetailsPanel.tsx`, `OrgMembersPanel.tsx` 등 기능 패널 컴포넌트의 뼈대를 생성했습니다.
*   **[완료]** **2-3. 레지스트리 채우기:** `featureRegistry.ts`가 실제 패널 컴포넌트를 가리키도록 업데이트했습니다.
*   **2-4. 임시 API 클라이언트 생성 함수 구현:**
    *   **목표:** 임시 JWT를 사용하여 API 요청을 보낼 수 있는 격리된 `axios` 인스턴스를 생성하는 팩토리 함수를 만듭니다.
    *   **파일:** `panel_react/src/services/apiService.ts`
    *   **작업:** `createTemporaryApiClient(token: string)` 함수를 새로 만듭니다. 이 함수는 임시 토큰을 `Authorization` 헤더로 사용하는 새로운 `axios` 인스턴스를 생성하여 반환합니다.

### **3단계: 프론트엔드 - 모달 대시보드 핵심 로직 구현**

*   **[완료]** **3-1. 모달 셸(Shell) 생성:** `OrganizationDetailsModal.tsx` 컴포넌트의 기본 구조를 생성했습니다.
*   **[완료]** **3-2. `OrganizationsPage`에 모달 통합:** `OrganizationsPage.tsx`에서 '편집' 버튼 클릭 시 `OrganizationDetailsModal`이 열리도록 연결했습니다.
*   **3-3. 임시 컨텍스트 API 로직 구현:**
    *   **목표:** 모달이 열릴 때 임시 JWT를 발급받고, 이 토큰을 사용하는 임시 API 클라이언트를 생성하여 하위 패널 컴포넌트들에게 전달합니다.
    *   **파일:** `panel_react/src/components/OrganizationDetailsModal.tsx`
    *   **작업:**
        1.  `useEffect` 훅 내에서, `organizationId`가 유효하면 `/auth/context-switch` API를 호출하여 `temporaryToken`을 받아옵니다.
        2.  받아온 `temporaryToken`으로 `createTemporaryApiClient`를 호출하여 `tempApiClient` 인스턴스를 생성하고, 이를 컴포넌트의 state에 저장합니다.
        3.  `ActiveComponent`를 렌더링할 때, `organization` 객체와 함께 `apiClient={tempApiClient}` prop을 전달합니다.

### **4단계: 프론트엔드 - 기능 패널 수정**

*   **목표:** 각 기능 패널이 전역 `apiClient` 대신, prop으로 전달받은 임시 `apiClient`를 사용하여 데이터를 요청하도록 수정합니다.
*   **4-1. `OrgMembersPanel.tsx` 수정:**
    *   **파일:** `panel_react/src/features/organization/panels/OrgMembersPanel.tsx`
    *   **작업:** `apiClient`를 prop으로 받도록 인터페이스를 수정하고, `getOrganizationMembers`를 호출할 때 이 prop을 사용하도록 변경합니다.
*   **4-2. `OrgDetailsPanel.tsx` 수정:**
    *   **파일:** `panel_react/src/features/organization/panels/OrgDetailsPanel.tsx`
    *   **작업:** `apiClient`를 prop으로 받도록 수정하고, 향후 데이터 수정/저장 기능이 추가될 때 이 클라이언트를 사용하도록 준비합니다.
