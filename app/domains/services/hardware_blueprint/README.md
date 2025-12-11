# Hardware Blueprint 서비스

## 1. 개요

`hardware_blueprint` 서비스는 하드웨어의 사양 및 설계를 정의하는 '청사진(blueprint)' 정보를 관리하는 역할을 담당합니다.

본 서비스는 CQRS(Command Query Responsibility Segregation) 원칙에 따라 명확하게 책임이 분리되어 있습니다.

-   **Command**: 청사진의 생성(Create), 수정(Update), 삭제(Delete)를 담당합니다.
-   **Query**: 청사진 정보를 조회(Read)하는 책임을 가집니다.

## 2. 핵심 기능

### Command (데이터 변경)

-   `create_blueprint`: 새로운 하드웨어 청사진을 생성합니다.
-   `update_blueprint`: 기존 하드웨어 청사진을 수정합니다.
-   `delete_blueprint`: 하드웨어 청사진을 삭제합니다.

**참고**: 모든 Command 작업은 아키텍처 가이드라인에 따라 감사 로그(`audit_log`)를 자동으로 기록합니다.

### Query (데이터 조회)

-   `get_blueprint_by_id`: 고유 ID로 특정 청사진을 조회합니다.
-   `get_blueprint_by_version_and_name`: 버전과 이름을 조합하여 청사진을 조회합니다.
-   `get_multiple_blueprints`: 다양한 필터 조건(ID, 버전, 이름, 제품 라인 ID 등)을 사용하여 청사진 목록을 조회합니다.
-   `get_valid_component_ids_for_blueprint`: 특정 청사진에 호환되는 유효 부품(component)의 ID 목록을 조회합니다.

## 3. 외부 사용법

다른 도메인에서 `hardware_blueprint` 서비스의 기능을 사용하기 위해서는, 반드시 `app/domains/inter_domain/hardware_blueprint/` 디렉토리에 위치한 Provider를 통해야 합니다.

-   **Command Provider**: `hardware_blueprint_command_provider`
-   **Query Provider**: `hardware_blueprint_query_provider`

**직접 서비스 파일을 임포트하는 것은 금지됩니다.**
