# Device Management Service Domain

## 1. 목적 (Purpose)

이 `device_management` 서비스 도메인은 시스템의 핵심 객체인 **장치(Device) 엔티티의 전체 생명주기**를 관리하는 단일 책임을 가집니다.

---

## 2. 핵심 아키텍처 (Core Architecture)

이 서비스는 **CQRS (Command Query Responsibility Segregation)** 와 **ID 생성 전략 분리** 원칙에 따라 설계되었습니다.

### 2.1. CQRS 구현

모든 계층 (`services`, `crud`, `schemas`, `providers`)의 파일들은 책임에 따라 `_command` 또는 `_query` 접미사를 사용하여 역할이 명확하게 분리됩니다.

-   **Command 측**: 장치를 생성, 수정, (소프트)삭제하는 책임을 가집니다.
-   **Query 측**: 장치를 조회하는 책임을 가지며, 다양한 조건에 따른 동적 필터링 기능을 제공합니다.

### 2.2. ID 생성 전략 (ID Generation Strategy)

새로운 장치의 고유 식별자(ID) 생성 로직은 서비스 내부가 아닌, `app/core/id_generator.py` 모듈에 위임되어 있습니다. 이를 통해 향후 ID 생성 정책이 변경되더라도 서비스 계층의 수정 없이 `id_generator` 모듈만 수정하여 유연하게 대응할 수 있습니다.

### 2.3. 소프트 삭제 (Soft Delete)

-   `delete_device` 서비스는 실제로 데이터베이스에서 레코드를 삭제하지 않습니다. 대신, `is_active` 플래그를 `False`로 설정하는 **소프트 삭제** 방식을 사용합니다.
-   모든 `Query` 서비스는 기본적으로 `is_active = True` 인 장치만 조회합니다.

---

## 3. 흐름 예시: 장치 생성

1.  외부(주로 `Policy` 계층)에서 `DeviceManagementCommandProvider`를 통해 `create_device`를 호출합니다.
2.  `DeviceManagementCommandService`는 `app/core/id_generator.py`의 `generate_device_id()`를 호출하여 새로운 ID를 발급받습니다.
3.  서비스는 `device_command_crud`의 `create_with_id()` 메소드를 호출하여, 발급받은 ID와 함께 장치 정보를 데이터베이스에 저장합니다.
4.  생성된 장치 객체를 반환합니다.
