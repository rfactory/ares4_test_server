# Device Access Management Service Domain

## 1. 목적 (Purpose)

이 `device_access_management` 서비스 도메인은 **'어떤 사용자가 어떤 장치에 접근할 수 있는지'**에 대한 **접근 관계**를 관리하는 단일 책임을 가집니다. '장치 자체'가 아닌 '사용자와 장치의 관계'에 초점을 맞춥니다.

---

## 2. 핵심 아키텍처 (Core Architecture)

이 서비스는 **CQRS (Command Query Responsibility Segregation)** 패턴에 따라 책임이 명확하게 분리된 '멍청한(Dumb)' 서비스 계층입니다.

-   **`services/device_access_command_service.py`**: 사용자-장치 간의 연결을 생성(`link`), 수정(`update`), 삭제(`remove`)하는 '명령' 책임을 가집니다.
-   **`services/device_access_query_service.py`**: 특정 장치나 사용자에 연결된 관계를 조회하는 '조회' 책임을 가집니다.

---

## 3. Policy 계층으로 이전될 책임들 (Responsibilities to be moved to Policy Layer)

과거 이 서비스는 단순한 DB 조작을 넘어, 복잡한 접근 제어 '두뇌' 로직을 포함하고 있었습니다. 리팩토링을 통해 이 모든 **'두뇌' 로직은 `DeviceAccessPolicy` (향후 생성될) 계층으로 이전**되어야 하며, 현재의 '멍청한' 서비스 계층에는 포함되지 않습니다.

`Policy`가 담당하게 될 주요 책임들은 다음과 같습니다:

*   **컨텍스트 기반 접근 제어**: `personal`, `organization`, `global`과 같은 `active_context`에 따라, 사용자에게 장치에 대한 읽기/수정/삭제 권한이 있는지 확인하는 로직.
*   **소유권 정책**: 장치의 소유권을 다른 사용자에게 이전하거나, 마지막 소유자가 연결을 해제할 때 장치를 초기화하는 것과 같은 비즈니스 정책.
*   **닉네임 정책**: 사용자의 장치 목록 내에서 닉네임이 중복되지 않도록 보장하는 로직 (`NICKNAME_POLICY.md` 참고).

---

## 4. 흐름 예시: Policy가 'viewer' 역할 부여 시

1.  `DeviceAccessPolicy`는 'viewer를 등록할 권한이 있는지' 등 모든 비즈니스 규칙과 권한을 검증합니다.
2.  모든 검증을 통과하면, `Policy`는 `device_access_command_provider.create_link(...)`를 호출합니다.
3.  `DeviceAccessCommandService`는 이 요청을 받아, `user_device_link_command_crud`를 통해 데이터베이스에 새로운 연결 관계 레코드를 생성합니다.
4.  마지막으로, `AuditCommandProvider`를 호출하여 '연결 생성'에 대한 감사 로그를 남깁니다.
