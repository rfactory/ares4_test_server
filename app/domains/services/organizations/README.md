# `organizations` 서비스

## 1. 개요 및 책임

`organizations` 서비스는 **시스템 내의 조직(기업) 정보를 관리**하는 핵심 서비스입니다.

본 서비스는 CQRS(Command Query Responsibility Segregation) 원칙에 따라 명확하게 책임이 분리되어 있습니다.

-   **Command**: 조직의 생성(Create), 수정(Update), 삭제(Delete)를 담당합니다.
-   **Query**: 조직 정보를 조회(Read)하는 책임을 가집니다.

> **참고: 조직과 사용자 간의 관계 관리는 이 서비스의 책임이 아닙니다.** (이는 `user_authorization` 또는 `access_requests`와 같은 다른 도메인의 책임입니다.)

---

## 2. 외부 사용 규칙

다른 도메인에서 `organizations` 서비스의 기능을 사용하기 위해서는, **반드시** `app/domains/inter_domain/organizations/` 디렉토리에 위치한 Provider를 통해야 합니다.

-   **Command Provider**: `organization_command_provider`
-   **Query Provider**: `organization_query_provider`

> **경고:** 서비스 파일을 직접 `import`하여 사용하는 것은 아키텍처 원칙에 위배되므로 절대 금지됩니다.

---

## 3. 핵심 기능

### Command (데이터 변경)

-   `create_organization`: 새로운 조직을 생성합니다.
-   `update_organization`: 기존 조직 정보를 수정합니다.
-   `delete_organization`: 조직을 삭제합니다.

**참고**: 모든 Command 작업은 아키텍처 가이드라인에 따라 감사 로그(`audit_log`)를 자동으로 기록합니다.

### Query (데이터 조회)

-   `get_organization`: 고유 ID로 특정 조직 정보를 조회합니다.
-   `get_organizations`: 여러 조직의 목록을 페이지네이션하여 조회합니다.
-   `get_organization_by_registration_number`: 사업자 등록 번호로 특정 조직을 조회합니다.

---

## 4. 권한 모델 (Permission Model)

이 서비스 자체는 권한을 검사하지 않으며, 호출자인 상위 계층(주로 `Policy` 계층)에서 다음 권한들을 확인해야 합니다.

-   **조직 생성**: `organization:create` 권한 필요.
-   **조직 수정**: `organization:update` 권한 필요 (및 해당 조직에 대한 관리자 여부 확인).
-   **조직 조회**: `organization:read` 권한 필요.

---

## 5. 테스트용 API 엔드포인트

> 이 API들은 외부용이 아닌, 서비스의 개별 기능을 테스트하기 위한 내부용 엔드포인트입니다.

-   `POST /organizations/`: 새로운 조직 생성.
-   `GET /organizations/{organization_id}`: 특정 조직 정보 조회.
-   `GET /organizations/`: 모든 조직 목록 조회.
-   `PUT /organizations/{organization_id}`: 조직 정보 업데이트.