# app/core/abac_managed_resources.py

from app.models.objects.organization import Organization
from app.models.objects.user import User
from app.models.objects.device import Device
from app.models.objects.role import Role
from app.models.objects.permission import Permission
from app.models.objects.access_request import AccessRequest

# ABAC 규칙을 적용할 수 있는 모델을 중앙에서 관리합니다.
# Key: 리소스 이름 (프론트엔드와 일치)
# Value: { model: SQLAlchemy 모델 클래스, exclude_columns: [제외할 컬럼 목록] }
MANAGEABLE_MODELS = {
    "organization": {
        "model": Organization,
        "exclude_columns": ["id", "version", "pg_customer_id", "created_at", "updated_at", "organization_type_id"]
    },
    "organizations": {
        "model": Organization,
        "exclude_columns": ["id", "version", "pg_customer_id", "created_at", "updated_at", "organization_type_id"]
    },
    "user": {
        "model": User,
        "exclude_columns": [
            "id", "password_hash", "reset_token", "reset_token_expires_at",
            "email_verification_token", "email_verification_token_expires_at",
            "is_active", "is_staff", "is_superuser", "is_two_factor_enabled",
            "created_at", "updated_at"
        ]
    },
    "organization_members": {
        "model": User,
        "exclude_columns": [
            "id", "password_hash", "reset_token", "reset_token_expires_at",
            "email_verification_token", "email_verification_token_expires_at",
            "is_active", "is_staff", "is_superuser", "is_two_factor_enabled",
            "created_at", "updated_at"
        ]
    },
    "system_members": {
        "model": User,
        "exclude_columns": [
            "id", "password_hash", "reset_token", "reset_token_expires_at",
            "email_verification_token", "email_verification_token_expires_at",
            "is_active", "is_staff", "is_superuser", "is_two_factor_enabled",
            "created_at", "updated_at"
        ]
    },
    "device": {
        "model": Device,
        "exclude_columns": [
            "id", "cpu_serial", "hmac_key_name", "recovery_token", 
            "recovery_token_expires_at", "created_at", "updated_at", "hardware_blueprint_id"
        ]
    },
    "role": {
        "model": Role,
        "exclude_columns": ["id", "tier", "lineage", "numbering", "max_headcount", "created_at", "updated_at", "organization_id"]
    },
    "permission": {
        "model": Permission,
        "exclude_columns": ["id", "is_system_locked", "created_at", "updated_at"]
    },
    "access-request": {
        "model": AccessRequest,
        "exclude_columns": ["id", "created_at", "updated_at", "requester_id", "target_user_id", "organization_id"]
    },
}
