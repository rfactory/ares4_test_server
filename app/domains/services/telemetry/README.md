# Telemetry 서비스 도메인 아키텍처 가이드라인

## 목적
이 서비스 도메인은 장치로부터의 텔레메트리 데이터를 안전하고 견고하게 수집 및 조회하는 것을 담당합니다.

## 핵심 원칙: 불변성(Immutability) 및 추가 전용(Append-Only)
**텔레메트리 데이터는 오직 기기가 보내는 '진실된 정보'로 간주됩니다.** 따라서 다음 원칙을 준수합니다:
- **데이터 생성(Create)만 허용**: 외부에서는 텔레메트리 데이터를 새로 생성하는 것만 가능합니다.
- **수정(Update) 및 삭제(Delete) 불가**: 일단 저장된 텔레메트리 데이터는 그 누구도 수정하거나 삭제할 수 없습니다. 이는 데이터의 무결성을 보장하기 위함입니다.
- **엄격한 생성 권한**: 텔레메트리 데이터 생성은 오직 시스템 내부의 신뢰할 수 있는 구성 요소(예: MQTT 프로세서)에 의해서만 가능하며, `Policy` 계층에서 엄격하게 통제됩니다.

## 구조: CQRS (Command Query Responsibility Segregation)
이 서비스는 CQRS 패턴을 따르며, Command와 Query의 책임을 명확히 분리합니다.

### 1. Command 측면 (데이터 생성)
- **책임**: 텔레메트리 데이터를 수집하고 데이터베이스에 영속화합니다.
- **스키마**: `schemas/telemetry_command.py`에서 `TelemetryCommandDataCreate`와 같은 Pydantic 모델을 정의하여 들어오는 데이터의 유효성을 검사합니다.
- **CRUD**: `crud/telemetry_command_crud.py`에는 `create_multiple` 메소드가 있어, 여러 텔레메트리 기록을 한 번의 데이터베이스 트랜잭션으로 효율적으로 저장합니다.
- **서비스**: `services/telemetry_command_service.py`는 `create_multiple_telemetry` 메소드를 통해 CRUD 계층을 호출하고 트랜잭션을 관리합니다. 개별 텔레메트리 데이터 입력에 대한 감사 로깅은 수행하지 않습니다.
- **Provider**: `inter_domain/telemetry/telemetry_command_provider.py`는 외부 도메인에서 텔레메트리 데이터를 생성하기 위한 안정적인 인터페이스를 제공합니다.

### 2. Query 측면 (데이터 조회)
- **책임**: 저장된 텔레메트리 데이터를 필터링하고 조회합니다.
- **스키마**: `schemas/telemetry_query.py`에서 `TelemetryQueryDataRead`와 같은 Pydantic 모델을 정의하여 조회된 데이터의 형식을 제공하고, `TelemetryFilter` 스키마로 다양한 필터링 옵션을 정의합니다.
- **CRUD**: `crud/telemetry_query_crud.py`에는 `get_multiple_telemetry_data` 메소드가 있어, 필터 조건에 따라 데이터베이스에서 텔레메트리 기록을 효율적으로 조회합니다.
- **서비스**: `services/telemetry_query_service.py`는 `get_telemetry_data` 메소드를 통해 CRUD 계층을 호출하여 데이터를 반환합니다. 조회 작업에 대한 감사 로깅은 기본적으로 수행하지 않습니다.
- **Provider**: `inter_domain/telemetry/telemetry_query_provider.py`는 외부 도메인에서 텔레메트리 데이터를 조회하기 위한 안정적인 인터페이스를 제공합니다.

## 감사 로깅 정책
- **데이터 생성**: 텔레메트리 데이터의 특성(대용량, 자동 생성)상 개별 데이터 생성에 대한 감사 로그는 기록하지 않습니다.
- **데이터 조회**: 기본적으로 감사 로그를 기록하지 않습니다. 다만, `Policy` 계층의 판단에 따라 특정 민감 데이터 조회 시에만 예외적으로 감사 로그를 기록할 수 있습니다.
