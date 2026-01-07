# 가이드: 스크립트 기반 시딩(Seeding)을 Alembic 데이터 마이그레이션으로 전환하기

## 1. 왜 마이그레이션이 더 나은가?

현재 `docker-compose.v2.yml`은 `create_system_user.py`와 `create_super_admin.py` 스크립트를 컨테이너 시작 시 실행하여, 초기 데이터(시스템 사용자, 관리자 계정, 기본 역할 및 권한 등)를 생성(시딩)합니다.

이 방식은 개발 초기에는 편리하지만, 다음과 같은 잠재적인 문제를 가집니다:

- **중복 실행 위험**: 서버가 재시작될 때마다 스크립트가 실행되므로, 내부에 "이미 존재하는가?"를 확인하는 방어 코드가 없다면 오류가 발생하거나 데이터를 덮어쓸 수 있습니다.
- **관리의 어려움**: 시간이 지나면서 어떤 초기 데이터가 왜 필요한지, 언제 변경되었는지 이력을 추적하기 어렵습니다.
- **확장성 문제**: 서버 인스턴스가 여러 개일 경우, 동시에 여러 스크립트가 실행되어 데이터베이스에 충돌을 일으킬 수 있습니다.

**Alembic 데이터 마이그레이션**은 이러한 문제를 해결하는, 더 안정적이고 표준적인 방법입니다.

- **장점**:
  - **멱등성(Idempotency)**: 마이그레이션은 데이터베이스별로 단 한 번만 실행되는 것을 보장합니다.
  - **버전 관리**: 모든 데이터 변경이 버전 관리 파일(`.py`)로 남으므로, 추적이 용이합니다.
  - **역할 분리**: 애플리케이션 실행 로직과 데이터베이스 상태 관리 로직이 명확하게 분리됩니다.

---

## 2. 데이터 마이그레이션 생성 방법 (단계별 가이드)

### 2.1. 빈 마이그레이션 파일 생성

먼저, 데이터만 수정하는 빈 마이그레이션 스크립트를 생성합니다. `-m` 뒤에는 이 마이그레이션이 무엇을 하는지 명확하게 설명하는 메시지를 적습니다.

```bash
# fastapi_app2 컨테이너 안에서 실행
docker exec fastapi_app2 alembic revision -m "Seed initial users, roles, and permissions data"
```

이 명령은 `alembic/versions/` 디렉토리에 새로운 파이썬 파일(예: `xxxxxxxxxxxx_seed_initial_data.py`)을 생성합니다. `upgrade`와 `downgrade` 함수는 비어있습니다.

### 2.2. `upgrade` 함수 작성 (데이터 삽입)

생성된 마이그레이션 파일의 `upgrade` 함수 안에, `op.bulk_insert`를 사용하여 데이터를 삽입하는 코드를 작성합니다. `create_super_admin.py`의 로직을 이곳으로 옮겨오는 것입니다.

**핵심 개념**:
- `op.bulk_insert(테이블_객체, [데이터_딕셔너리_목록])`을 사용합니다.
- SQLAlchemy 모델을 직접 사용하지 않고, 마이그레이션 시점의 테이블 스키마를 정의하여 사용해야 합니다. 이렇게 하면 나중에 모델이 변경되어도 마이그레이션 파일은 깨지지 않습니다.

### 2.3. `downgrade` 함수 작성 (데이터 삭제)

`downgrade` 함수에는 `upgrade`에서 생성한 데이터를 삭제하는 코드를 작성합니다. 이는 마이그레이션을 되돌릴 때 필요합니다.

**핵심 개념**:
- 간단한 데이터 삭제는 `op.execute("DELETE FROM 테이블명 WHERE 조건")`을 사용하는 것이 편리합니다.

---

## 3. `docker-compose.v2.yml` 수정

마이그레이션으로 데이터 시딩을 옮긴 후에는, 더 이상 `docker-compose.v2.yml`에서 스크립트를 실행할 필요가 없습니다. `command` 섹션에서 해당 부분을 삭제합니다.

```yaml
# 수정 전
command: >
  sh -c "alembic upgrade head && \
         python scripts/create_system_user.py && \
         python scripts/create_super_admin.py && \
         uvicorn app.main:app --host 0.0.0.0 --port 8000"

# 수정 후
command: >
  sh -c "alembic upgrade head && \
         uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

---

## 4. 실제 마이그레이션 코드 예시

아래는 `create_system_user.py`와 `create_super_admin.py`의 모든 로직을 하나의 Alembic 마이그레이션 파일로 변환한 전체 코드 예시입니다.

**파일명**: `alembic/versions/xxxxxxxxxxxx_seed_initial_users_roles_permissions.py`

```python
"""Seed initial users, roles, and permissions data

Revision ID: xxxxxxxxxxxx
Revises: (이전 마이그레이션 ID)
Create Date: 2025-12-19 10:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import table, column
from app.core.security import get_password_hash # 비밀번호 해싱 함수

# revision identifiers, used by Alembic.
revision: str = 'xxxxxxxxxxxx'
down_revision: Union[str, Sequence[str], None] = '1337bad63175' # 이전에 생성된 마지막 마이그레이션 ID
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed initial data into the database."""
    # 각 테이블에 대한 스키마를 마이그레이션 시점에 맞게 정의
    organization_types_table = table('organization_types', 
        column('id', sa.Integer),
        column('name', sa.String),
        column('description', sa.String)
    )
    permissions_table = table('permissions', 
        column('id', sa.Integer),
        column('name', sa.String),
        column('description', sa.String)
    )
    roles_table = table('roles', 
        column('id', sa.Integer),
        column('name', sa.String),
        column('description', sa.String),
        column('scope', sa.String)
    )
    users_table = table('users', 
        column('id', sa.Integer),
        column('email', sa.String),
        column('username', sa.String),
        column('password_hash', sa.String),
        column('is_active', sa.Boolean),
        column('is_staff', sa.Boolean),
        column('is_superuser', sa.Boolean)
    )

    # 1. 기본 조직 유형 생성
    op.bulk_insert(organization_types_table, [
        {'id': 1, 'name': 'General Corporation', 'description': 'A standard corporate entity.'}
    ])

    # 2. 필수 권한 생성
    op.bulk_insert(permissions_table, [
        {'id': 1, 'name': 'organization:create', 'description': 'Create a new organization'},
        {'id': 2, 'name': 'organizations:read', 'description': 'Read the list of organizations'},
        {'id': 3, 'name': 'organization_type:create', 'description': 'Create a new organization type'}
    ])

    # 3. 시스템 역할 및 관리자 역할 생성
    op.bulk_insert(roles_table, [
        {'id': 1, 'name': 'SYSTEM', 'description': 'System internal role', 'scope': 'SYSTEM'},
        {'id': 2, 'name': 'SUPER_ADMIN', 'description': 'Super Admin with all permissions', 'scope': 'SYSTEM'}
    ])

    # 4. 시스템 사용자 및 관리자 사용자 생성
    op.bulk_insert(users_table, [
        {'id': 1, 'email': 'system@ares4.esgroup.net', 'username': 'ares_user', 'password_hash': 'system_internal', 'is_active': True, 'is_staff': False, 'is_superuser': False},
        {'id': 2, 'email': 'ypkim.gs@esgroup.net', 'username': 'yoonpyo', 'password_hash': get_password_hash('Yoonpyo04118!'), 'is_active': True, 'is_staff': True, 'is_superuser': True}
    ])

    # PostgreSQL에서 ID 시퀀스를 수동으로 업데이트해야 할 수 있음
    op.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));")
    op.execute("SELECT setval('roles_id_seq', (SELECT MAX(id) FROM roles));")
    op.execute("SELECT setval('permissions_id_seq', (SELECT MAX(id) FROM permissions));")
    op.execute("SELECT setval('organization_types_id_seq', (SELECT MAX(id) FROM organization_types));")

def downgrade() -> None:
    """Remove the initial seed data."""
    # 간단한 구현을 위해, 생성된 데이터의 ID를 기반으로 삭제
    # 실제 프로덕션에서는 더 정교한 로직이 필요할 수 있음
    op.execute("DELETE FROM users WHERE id IN (1, 2);")
    op.execute("DELETE FROM roles WHERE id IN (1, 2);")
    op.execute("DELETE FROM permissions WHERE id IN (1, 2, 3);")
    op.execute("DELETE FROM organization_types WHERE id = 1;")
