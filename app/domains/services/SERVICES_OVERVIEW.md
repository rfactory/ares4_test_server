# Services 도메인 기능 명세

이 문서는 `services` 도메인에 포함된 각 하위 도메인(서비스)의 역할과 주요 기능을 요약하여 설명합니다.
각 서비스는 단일 책임 원칙(SRP)과 CQRS(Command Query Responsibility Segregation) 패턴에 따라 `Command` (데이터 변경)와 `Query` (데이터 조회) 책임이 명확하게 분리되어 있습니다.

---

## 1. `access_requests` (접근 요청 관리)

- **설명:** 사용자의 리소스 접근 요청 생성, 상태 변경, 조회 등을 관리합니다.
- **Command:**
    - `create_access_request`: 새로운 접근 요청을 생성합니다.
    - `update_access_request_status`: 접근 요청의 상태(예: 승인, 거절)를 변경합니다.
    - `delete_access_request`: 접근 요청을 삭제합니다.
- **Query:**
    - `get_access_requests`: 조건에 맞는 접근 요청 목록을 조회합니다.
    - `get_access_request_by_id`: ID로 특정 접근 요청을 조회합니다.
- **참고:** 최초 분석 시 `access_request_command_service.py` 파일의 내용이 Provider 코드로 잘못 채워져 있었으나, 이후 수정되었습니다.

## 2. `audit` (감사 로그 관리)

- **설명:** 시스템 내의 주요 이벤트(리소스 생성, 수정, 삭제 등)에 대한 감사 로그를 기록하고 조회하는 중앙 집중식 로깅 서비스를 제공합니다.
- **Command:**
    - `log_creation`: 리소스 생성 이벤트를 기록합니다.
    - `log_update`: 리소스 수정 이벤트를 기록하며, 변경 전/후 데이터를 상세히 저장합니다.
    - `log_deletion`: 리소스 삭제 이벤트를 기록합니다.
- **Query:**
    - `get_logs_with_filter`: 다양한 필터 조건(사용자, 이벤트 타입, 기간 등)을 사용하여 감사 로그를 동적으로 조회합니다.

## 3. `certificate_management` (인증서 관리)

- **설명:** 장치(Device)와 같은 리소스에 대한 디지털 인증서의 발급, 저장, 조회를 관리합니다. Vault와 데이터베이스를 함께 사용합니다.
- **Command:**
    - `create_device_certificate`: 장치에 대한 새 인증서를 발급합니다.
- **Query:**
    - `get_certificate`: ID로 특정 인증서를 조회합니다.
    - `get_certificates`: 인증서 목록을 조회합니다.
- **아키텍처:**
    - `vault_certificate_repository`: Vault와 통신하여 인증서 발급 및 관리를 담당합니다.
    - `db_certificate_repository`: 발급된 인증서의 메타데이터를 주 데이터베이스에 저장합니다.

## 4. `device_management` (장치 관리)

- **설명:** 시스템에 등록된 장치의 생명주기(생성, 정보 수정, 삭제)를 관리합니다.
- **Command:**
    - `create_device`: 고유 ID를 가진 새 장치를 생성하고 감사 로그를 기록합니다.
    - `update_device`: 기존 장치의 정보를 수정하고 변경 이력을 기록합니다.
    - `delete_device`: 장치를 비활성화(Soft Delete) 처리합니다.
- **Query:**
    - `get_devices`: 동적 필터 조건으로 장치 목록을 조회합니다.
    - `get_device_by_id`: ID로 특정 장치를 조회합니다.

## 5. `user_identity` (사용자 신원 관리)

- **설명:** 사용자 계정의 생성, 인증, 정보 수정 등 사용자의 핵심 신원 정보를 관리합니다.
- **Command:**
    - `create_user_and_log`: 신규 사용자를 생성하고 감사 로그를 기록합니다. (비밀번호 해싱, 중복 검사 포함)
    - `update_user`: 사용자 정보를 수정합니다. (Validator/Transformer 패턴 사용)
    - `delete_user`: 사용자를 비활성화(Soft Delete)합니다.
    - `activate_user`: 비활성화된 사용자 계정을 다시 활성화합니다.
- **Query:**
    - `get_user_by_username`: 사용자 이름으로 사용자를 조회합니다.
    - `get_user_by_email`: 이메일로 사용자를 조회합니다.
    - `get_user`: ID로 특정 사용자를 조회합니다.
- **아키텍처:**
    - `validators`: 사용자 정보 수정 시 데이터 유효성을 검사하는 로직을 포함합니다. (예: 이메일 중복 검사)
    - `transformers`: 데이터 저장 전 필요한 변환을 수행합니다. (예: 비밀번호 해싱)

## 6. `device_component_management` (장치-부품 연결 관리)

- **설명:** 특정 장치(Device)와 지원되는 부품(Supported Component) 간의 연결(인스턴스)을 관리합니다.
- **Command:**
    - `attach_component_to_device`: 장치에 부품을 부착(연결)하고 감사 로그를 기록합니다.
    - `detach_component_from_device`: 장치에서 부품을 분리(연결 해제)하고 감사 로그를 기록합니다.
- **Query:**
    - `get_components_for_device`: 특정 장치에 연결된 모든 부품 인스턴스 목록을 조회합니다.

## 7. `hardware_blueprint` (하드웨어 설계도 관리)

- **설명:** 장치의 템플릿 또는 사양에 해당하는 하드웨어 설계도(Blueprint)를 이름과 버전으로 식별하여 관리합니다.
- **Command:**
    - `create_blueprint`: 새로운 하드웨어 설계도를 생성합니다.
    - `update_blueprint`: 기존 설계도를 수정합니다.
    - `delete_blueprint`: 설계도를 삭제합니다.
- **Query:**
    - `get_blueprint_by_id`: ID로 설계도를 조회합니다.
    - `get_blueprint_by_version_and_name`: 이름과 버전으로 설계도를 조회합니다.
    - `get_multiple_blueprints`: 여러 설계도 목록을 조회합니다.
    - `get_valid_component_ids_for_blueprint`: 특정 설계도에 유효한 부품 ID 목록을 조회합니다.

## 8. `organization_device_link` (조직-장치 연결 관리)

- **설명:** 조직(Organization)과 장치(Device) 간의 관계를 관리합니다.
- **Command:**
    - `assign_device`: 특정 관계 유형으로 장치를 조직에 할당합니다.
    - `unassign_device`: 장치와 조직 간의 연결을 비활성화(soft-delete)합니다.
    - `update_assignment`: 관계 유형 등 기존 할당 정보를 수정합니다.
- **Query:**
    - `get_link_by_ids`: 조직 ID, 장치 ID, 관계 유형으로 특정 연결을 조회합니다.
    - `get_all_links_for_organization`: 특정 조직에 연결된 모든 장치 목록을 조회합니다.
    - `get_all_links_for_device`: 특정 장치에 연결된 모든 조직 목록을 조회합니다.

## 9. `organizations` (조직 관리)

- **설명:** 조직 정보를 관리합니다.
- **Command:**
    - `create_organization`: 새로운 조직을 생성합니다.
    - `update_organization`: 기존 조직 정보를 수정합니다.
    - `delete_organization`: 조직을 물리적으로 삭제(Hard-delete)합니다.
- **Query:**
    - `get_organization`: ID로 특정 조직을 조회합니다.
    - `get_organizations`: 조직 목록을 페이징하여 조회합니다.
    - `get_organization_by_registration_number`: 사업자 등록 번호로 조직을 조회합니다.

## 10. `role_management` (역할 관리)

- **설명:** 사용자 역할을 관리합니다.
- **Command:**
    - `create_role`: 새로운 역할을 생성합니다.
    - `update_role`: 기존 역할을 수정합니다.
    - `delete_role`: 역할을 삭제합니다.
- **Query:**
    - `get_role`: ID로 역할을 조회합니다.
    - `get_role_by_name`: 이름으로 역할을 조회합니다.
    - `get_all_roles`: 모든 역할 목록을 페이징하여 조회합니다.

## 11. `supported_component_management` (지원 부품 관리)

- **설명:** 시스템에서 지원하는 부품의 유형을 관리합니다.
- **Command:**
    - `create_supported_component`: 새로운 유형의 지원 부품을 시스템에 등록합니다.
- **Query:**
    - `get_all_supported_components`: 등록된 모든 지원 부품 목록을 조회합니다.

## 12. `telemetry` (원격 측정 데이터 관리)

- **설명:** 장치로부터 수신된 원격 측정(telemetry) 데이터를 관리합니다. 데이터의 무결성을 위해 수정 및 삭제 기능이 의도적으로 배제되었습니다.
- **Command:**
    - `create_multiple_telemetry`: 여러 원격 측정 데이터를 일괄적으로 생성합니다.
- **Query:**
    - `get_telemetry_data`: 다양한 필터를 사용하여 원격 측정 데이터를 조회합니다.

## 13. `token` (JWT 토큰 발급)

- **설명:** JWT 접근 토큰 발급의 단일 책임을 가지는 명령(Command) 전용 서비스입니다.
- **Command:**
    - `issue_token`: 주어진 사용자에 대해 새로운 JWT 접근 토큰을 생성하고, 로그인 이벤트를 감사합니다.
- **Query:** 없음

## 14. `user_2fa_state` (사용자 2단계 인증 상태 관리)

- **설명:** 사용자의 2단계 인증(2FA) 상태를 관리하는 명령(Command) 전용 서비스입니다.
- **Command:**
    - `set_code`: 새로운 2FA 코드를 생성하고 만료 시간을 설정하여 사용자 레코드에 저장합니다.
    - `clear_code`: 사용된 2FA 코드를 사용자 레코드에서 삭제합니다.
- **Query:** 없음

## 15. `user_device_link` (사용자-장치 연결 관리)

- **설명:** 사용자와 장치 간의 관계(연결)를 관리합니다.
- **Command:**
    - `link_device_to_user`: 사용자와 장치 간의 새로운 연결을 생성합니다.
    - `update_link`: 별명, 역할 등 기존 연결 정보를 수정합니다.
    - `remove_link`: 사용자와 장치 간의 연결을 물리적으로 삭제(Hard-delete)합니다.
- **Query:**
    - `get_link_by_user_and_device`: 사용자 ID와 장치 ID로 특정 연결을 조회합니다.
    - `get_all_links_for_user`: 특정 사용자에 대한 모든 장치 연결을 조회합니다.
    - `get_all_links_for_device`: 특정 장치에 대한 모든 사용자 연결을 조회합니다.

## 16. `user_role_assignment` (사용자 역할 할당 관리)

- **설명:** 특정 조직(Organization) 내에서 사용자에게 역할을 할당하는 것을 관리합니다.
- **Command:**
    - `assign_role`: 조직 내에서 사용자에게 역할을 할당하며, 역할의 최대 인원수 제한을 확인합니다.
- **Query:**
    - `get_assignments_for_user`: 특정 사용자의 모든 역할 할당 목록을 조회합니다.

## 17. `user_settings` (사용자 설정 관리)

- **설명:** 개별 사용자 계정 설정을 관리하는 명령(Command) 전용 서비스입니다.
- **Command:**
    - `toggle_2fa`: 현재 사용자의 2단계 인증(2FA) 설정(`is_two_factor_enabled` 플래그)을 켜거나 끕니다.
- **Query:** 없음