# 장치 API 및 접근 제어 정책 (Device API & Access Control Policy)

이 문서는 장치 관련 도메인의 API 설계, 컨텍스트 기반 접근 제어, 그리고 고유 식별자 정책을 종합적으로 정의합니다.

---

## 1. 컨텍스트 전환 모델 (Context Switching Model)

시스템은 사용자가 어떤 자격으로 행동하는지에 따라 API의 동작을 다르게 하는 '컨텍스트 전환' 모델을 기반으로 합니다. 사용자는 UI를 통해 다음 세 가지 컨텍스트 중 하나를 명시적으로 선택할 수 있어야 합니다.

-   **`personal` (개인 컨텍스트):** 사용자가 자신의 개인적인 자격으로 행동합니다. `Prime_Admin`일지라도 이 컨텍스트에서는 자신의 개인 장치만 볼 수 있습니다.
-   **`organization` (조직 컨텍스트):** 사용자가 특정 조직의 구성원 또는 관리자 자격으로 행동합니다. API 호출 시, 컨텍스트에 해당하는 `organization_id`가 함께 전달되어야 합니다.
-   **`global` (전역 컨텍스트):** 사용자가 시스템 전체의 관리자(`Prime_Admin` 등) 자격으로 행동합니다. 이 컨텍스트는 `scope='SYSTEM'` 역할을 가진 사용자에게만 허용됩니다.

### 1.1. 컨텍스트 조회 API (Context Discovery API)

사용자가 자신이 선택할 수 있는 컨텍스트의 목록을 조회할 수 있는 API를 제공해야 합니다.

-   **엔드포인트:** `GET /users/me/contexts`
-   **구현 위치:** `user_management` 오케스트레이터 서비스가 이 로직을 처리하기에 적합합니다.
-   **응답 형식 예시:**
    ```json
    [
        {
            "type": "personal",
            "name": "개인 공간"
        },
        {
            "type": "organization",
            "name": "A회사",
            "organization_id": 123
        },
        {
            "type": "organization",
            "name": "B회사",
            "organization_id": 456
        },
        {
            "type": "global",
            "name": "시스템 전체 관리"
        }
    ]
    ```
-   **로직:**
    1.  API는 요청한 사용자의 정보를 조회합니다.
    2.  `personal` 컨텍스트는 항상 목록에 포함됩니다.
    3.  사용자의 `user_role_assignments`를 순회하며, `scope='SYSTEM'`인 역할이 하나라도 있으면 `global` 컨텍스트를 목록에 추가합니다.
    4.  `scope='ORGANIZATION'`인 역할이 있다면, 모든 `organization_id`를 수집하여 중복을 제거하고, 각 `organization_id`에 해당하는 조직 이름과 함께 `organization` 컨텍스트를 목록에 추가합니다.

---

## 2. 통합 API 엔드포인트 설계 (Unified API Endpoint Design)

장치 조회를 위한 API는 유연성과 확장성을 극대화하기 위해 단일 엔드포인트로 통합합니다.

-   **엔드포인트:** `GET /devices`

### 2.1. 핵심 쿼리 파라미터

-   **`active_context: Union[Literal['personal', 'global'], int]` (필수):** API를 호출하는 현재 컨텍스트를 명시합니다. 'personal', 'global' 또는 `organization_id`가 될 수 있습니다.
-   **`nicknames: Optional[List[str]] = None` (선택):** 조회하려는 장치의 `nickname` 목록입니다. 이 파라미터가 제공되면, `active_context` 내에서 해당 `nickname`을 가진 장치들만 필터링하여 반환합니다.

### 2.2. 클라이언트별 사용 예시

-   **Flutter 앱 (개인 장치 목록 전체 조회):**
    -   `GET /devices?active_context=personal`

-   **Flutter 앱 (특정 장치 1개 상세 조회):**
    -   `GET /devices?active_context=personal&nicknames=내주방조명`

-   **기업용 웹 패널 (특정 조직의 장치 목록 전체 조회):**
    -   `GET /devices?active_context=123` (여기서 123은 `organization_id`)

-   **기업용 웹 패널 (특정 조직 내 여러 장치 동시 조회):**
    -   `GET /devices?active_context=123&nicknames=기계A,기계B`

-   **전역 관리자 패널 (모든 장치 목록 조회):**
    -   `GET /devices?active_context=global`

### 2.3. 컨텍스트별 응답 모델 (Context-Specific Response Models)

`GET /devices` API는 `active_context` 값에 따라 다른 응답 모델을 반환하여 사용자 경험을 최적화합니다.

-   **`personal` 컨텍스트 응답:** `List[PersonalDeviceResponse]`
    -   개인 컨텍스트에서는 사용자와 장치의 관계(역할, 별명)가 중요하므로, 이를 포함하는 별도의 스키마로 응답합니다.
    -   **`PersonalDeviceResponse` 스키마 예시:**
        ```python
        class PersonalDeviceResponse(BaseModel):
            nickname: str
            role: str # 'owner' 또는 'viewer'
            device: Device # 전체 장치 정보 모델
        ```

-   **`organization` 및 `global` 컨텍스트 응답:** `List[Device]`
    -   조직 또는 전역 컨텍스트에서는 장치의 객관적인 정보가 중요하므로, 표준 `Device` 스키마의 리스트로 응답합니다.

---

## 3. `nickname` 기반 식별자 정책

`id`나 `uuid` 대신, 사용자 친화적인 `nickname`을 주요 식별자로 사용하며, 정책은 다음과 같습니다.

-   **기본값 생성:** 프로비저닝 시, 시스템은 '모델명-장치ID' 형식으로 초기 `nickname`을 자동 생성합니다.
-   **유일성 보장:** `nickname`은 DB 제약조건이 아닌, **어플리케이션 레벨에서 각 사용자 범위 내에서만 유일성이 보장**됩니다. 사용자가 `nickname`을 수정할 때 서비스 계층에서 중복을 검사합니다.
-   **필수값:** `nickname`은 비어있거나 `null`이 될 수 없습니다.

### 3.1. `nickname` 프로비저닝 상세 워크플로우

1.  **`device_provisioning` 서비스**의 `provision_new_device` 메소드가 호출됩니다.
2.  `device_core_management_providers.create_device`를 통해 `Device` 레코드가 먼저 생성됩니다. 이때는 `nickname`이 없는 상태입니다.
3.  생성된 `Device` 객체로부터 `device.id`와 `device.hardware_blueprint.name` (모델명)을 가져옵니다.
4.  두 값을 조합하여 기본 `nickname`을 생성합니다. (예: `ARES-4-123`)
5.  **`device_access_management_providers.link_device_to_user`**를 호출할 때, 이 기본 `nickname`을 `UserDeviceCreate` 스키마에 포함하여 전달하고, `role`은 `'owner'`로 설정합니다.

---

## 4. 서비스 계층 구현

-   **`device_access_management` 서비스**가 이 모든 로직의 중심이 됩니다.
-   **`get_visible_devices` 메소드:** 이 '스마트' 메소드는 `request_user`와 `active_context`, 그리고 선택적인 `nicknames`를 파라미터로 받아, 위에 정의된 컨텍스트별 분기 로직과 필터링을 모두 수행한 후 최종 결과(`List[PersonalDeviceResponse]` 또는 `List[Device]`)를 반환합니다.
