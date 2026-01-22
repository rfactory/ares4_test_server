from sqlalchemy import Column, DateTime, text, Integer, ForeignKey, Enum, Text, BigInteger
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime

class TimestampMixin:
    """
    모델에 `created_at` 및 `updated_at` 타임스탬프 컬럼을 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)

# --- 외래 키 믹스인 (FK Mixins) ---

class UserFKMixin:
    @declared_attr
    def user_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('users.id'), nullable=False)

class NullableUserFKMixin:
    @declared_attr
    def user_id(cls) -> Mapped[Optional[int]]:
        return mapped_column(BigInteger, ForeignKey('users.id'), index=True, nullable=True)

class OrganizationFKMixin:
    @declared_attr
    def organization_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('organizations.id'), nullable=False)

class NullableOrganizationFKMixin:
    @declared_attr
    def organization_id(cls) -> Mapped[Optional[int]]:
        return mapped_column(BigInteger, ForeignKey('organizations.id'), nullable=True)

class SystemUnitFKMixin:
    @declared_attr
    def system_unit_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('system_units.id'), index=True, nullable=False)

class NullableSystemUnitFKMixin:
    @declared_attr
    def system_unit_id(cls) -> Mapped[Optional[int]]:
        return mapped_column(BigInteger, ForeignKey('system_units.id'), index=True, nullable=True)

class DeviceFKMixin:
    @declared_attr
    def device_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('devices.id'), nullable=False)

class HardwareBlueprintFKMixin:
    @declared_attr
    def hardware_blueprint_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('hardware_blueprints.id'), nullable=False)

# --- [추가] 이전 모델 파일들에서 사용한 핵심 Mixin ---
class SupportedComponentFKMixin:
    """`supported_components` 테이블을 참조하는 외래 키입니다."""
    @declared_attr
    def supported_component_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('supported_components.id'), nullable=False)

class DeviceComponentInstanceFKMixin:
    """`device_component_instances` 테이블을 참조합니다."""
    @declared_attr
    def device_component_instance_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('device_component_instances.id'), nullable=False)

class ProductLineFKMixin:
    @declared_attr
    def product_line_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('product_lines.id'), nullable=False)

class SubscriptionPlanFKMixin:
    @declared_attr
    def subscription_plan_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('subscription_plans.id'), nullable=False)

class AlertRuleFKMixin:
    @declared_attr
    def alert_rule_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('alert_rules.id'), nullable=False)

# --- Role FK Mixins ---
class RoleFKMixin:
    @declared_attr
    def role_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('roles.id'), nullable=False)

class NullableRoleFKMixin:
    @declared_attr
    def role_id(cls) -> Mapped[Optional[int]]:
        return mapped_column(BigInteger, ForeignKey('roles.id'), nullable=True)

# --- Permission FK Mixins ---
class PermissionFKMixin:
    @declared_attr
    def permission_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('permissions.id'), nullable=False)

class NullablePermissionFKMixin:
    @declared_attr
    def permission_id(cls) -> Mapped[Optional[int]]:
        return mapped_column(BigInteger, ForeignKey('permissions.id'), nullable=True)

# --- BlueprintPinMapping FK Mixins ---
class BlueprintPinMappingFKMixin:
    @declared_attr
    def blueprint_pin_mapping_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('blueprint_pin_mappings.id'), nullable=False)

# --- OrganizationType FK Mixins ---
class OrganizationTypeFKMixin:
    @declared_attr
    def organization_type_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('organization_types.id'), nullable=False)

# --- AssetDefinition FK Mixins (InternalAssetDefinition 참조) ---
class AssetDefinitionFKMixin:
    """`internal_asset_definitions` 테이블을 참조하는 외래 키입니다."""
    @declared_attr
    def asset_definition_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('internal_asset_definitions.id'), nullable=False)

# --- UserConsumable FK Mixins ---
class UserConsumableFKMixin:
    """`user_consumables` 테이블을 참조하는 외래 키입니다."""
    @declared_attr
    def user_consumable_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey('user_consumables.id'), nullable=False)

# --- 로그 및 공통 유틸리티 Mixin ---

class LogBaseMixin:
    """로그 및 이벤트 모델을 위한 공통 필드입니다."""
    @declared_attr
    def event_type(cls) -> Mapped[str]:
        return mapped_column(Enum('DEVICE', 'AUDIT', 'CONSUMABLE_USAGE', 'SERVER_MQTT_CERTIFICATE_ISSUED', 
                                 'DEVICE_CERTIFICATE_CREATED', 'CERTIFICATE_REVOKED', 
                                 'SERVER_CERTIFICATE_ACQUIRED_NEW', 'ORGANIZATION_CREATED', 
                                 'ORGANIZATION_UPDATED', 'ORGANIZATION_DELETED', 
                                 'LOGIN_SUCCESS', 'LOGIN_FAILURE', 'PASSWORD_RESET', 'ACCOUNT_LOCK',
                                 name='log_event_type', create_type=False), # create_type=False 추가
                            nullable=False)

    @declared_attr
    def log_level(cls) -> Mapped[Optional[str]]:
        return mapped_column(Enum('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', name='log_level', create_type=False), # create_type=False 추가
                            nullable=True)

    @declared_attr
    def description(cls) -> Mapped[Optional[str]]:
        return mapped_column(Text, nullable=True)