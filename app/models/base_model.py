from sqlalchemy import Column, DateTime, text, Integer, ForeignKey, Enum, Text
from sqlalchemy.ext.declarative import declared_attr

class TimestampMixin:
    """
    모델에 `created_at` 및 `updated_at` 타임스탬프 컬럼을 추가하기 위한 Mixin입니다.
    - `created_at`: 생성 시 자동으로 설정되며, Null을 허용하지 않습니다.
    - `updated_at`: 생성 시 자동으로 설정되고, 수정 시마다 업데이트되며, Null을 허용하지 않습니다.
    """
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)

# --- 외래 키 믹스인 추가 ---

class UserFKMixin:
    """
    `users` 테이블을 참조하는 Null을 허용하지 않는 `user_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def user_id(cls):
        return Column(Integer, ForeignKey('users.id'), nullable=False)

class NullableUserFKMixin:
    """
    `users` 테이블을 참조하는 Null을 허용하는 `user_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    온톨로지 매핑 및 데이터 무결성 강화를 위해, Null 대신 시스템 사용자 ID(기본값: 1)를 사용합니다.
    **주의: `users` 테이블에 ID가 1인 시스템 사용자가 미리 생성되어 있어야 합니다.**
    """
    @declared_attr
    def user_id(cls):
        # NullableUserFKMixin을 사용하는 모든 필드는 이제 Null을 허용하지 않으며,
        # 기본값으로 시스템 사용자 ID(1)를 가집니다.
        return Column(Integer, ForeignKey('users.id'), nullable=False, server_default=text("1"))

class OrganizationFKMixin:
    """
    `organizations` 테이블을 참조하는 Null을 허용하는 `organization_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def organization_id(cls):
        return Column(Integer, ForeignKey('organizations.id'), nullable=True)

class RoleFKMixin:
    """
    `roles` 테이블을 참조하는 Null을 허용하지 않는 `role_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def role_id(cls):
        return Column(Integer, ForeignKey('roles.id'), nullable=False)

class NullableRoleFKMixin:
    """
    `roles` 테이블을 참조하는 Null을 허용하는 `role_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def role_id(cls):
        return Column(Integer, ForeignKey('roles.id'), nullable=True)

class DeviceFKMixin:
    """
    `devices` 테이블을 참조하는 Null을 허용하지 않는 `device_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def device_id(cls):
        return Column(Integer, ForeignKey('devices.id'), nullable=False)

class PermissionFKMixin:
    """
    `permissions` 테이블을 참조하는 Null을 허용하지 않는 `permission_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def permission_id(cls):
        return Column(Integer, ForeignKey('permissions.id'), nullable=False)

class HardwareBlueprintFKMixin:
    """
    `hardware_blueprints` 테이블을 참조하는 Null을 허용하지 않는 `hardware_blueprint_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def hardware_blueprint_id(cls):
        return Column(Integer, ForeignKey('hardware_blueprints.id'), nullable=False)

class NullableHardwareBlueprintFKMixin:
    """
    `hardware_blueprints` 테이블을 참조하는 Null을 허용하는 `hardware_blueprint_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def hardware_blueprint_id(cls):
        return Column(Integer, ForeignKey('hardware_blueprints.id'), nullable=True)

class CertificateFKMixin:
    """
    `certificates` 테이블을 참조하는 Null을 허용하지 않는 `certificate_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def certificate_id(cls):
        return Column(Integer, ForeignKey('certificates.id'), nullable=False)

class NullableCertificateFKMixin:
    """
    `certificates` 테이블을 참조하는 Null을 허용하는 `certificate_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def certificate_id(cls):
        return Column(Integer, ForeignKey('certificates.id'), nullable=True)

class SupportedComponentFKMixin:
    """
    `supported_components` 테이블을 참조하는 Null을 허용하지 않는 `supported_component_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def supported_component_id(cls):
        return Column(Integer, ForeignKey('supported_components.id'), nullable=False)

class BlueprintPinMappingFKMixin:
    """
    `blueprint_pin_mappings` 테이블을 참조하는 Null을 허용하지 않는 `blueprint_pin_mapping_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def blueprint_pin_mapping_id(cls):
        return Column(Integer, ForeignKey('blueprint_pin_mappings.id'), nullable=False)

class ProductLineFKMixin:
    """
    `product_lines` 테이블을 참조하는 Null을 허용하지 않는 `product_line_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def product_line_id(cls):
        return Column(Integer, ForeignKey('product_lines.id'), nullable=False)

class OrganizationTypeFKMixin:
    """
    `organization_types` 테이블을 참조하는 Null을 허용하지 않는 `organization_type_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def organization_type_id(cls):
        return Column(Integer, ForeignKey('organization_types.id'), nullable=False)

class AssetDefinitionFKMixin:
    """
    `internal_asset_definitions` 테이블을 참조하는 Null을 허용하지 않는 `asset_definition_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def asset_definition_id(cls):
        return Column(Integer, ForeignKey('internal_asset_definitions.id'), nullable=False)

class SubscriptionPlanFKMixin:
    """
    `subscription_plans` 테이블을 참조하는 Null을 허용하지 않는 `plan_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def plan_id(cls):
        return Column(Integer, ForeignKey('subscription_plans.id'), nullable=False)

class DeviceComponentInstanceFKMixin:
    """
    `device_component_instances` 테이블을 참조하는 Null을 허용하지 않는 `device_component_instance_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def device_component_instance_id(cls):
        return Column(Integer, ForeignKey('device_component_instances.id'), nullable=False)

class UserConsumableFKMixin:
    """
    `user_consumables` 테이블을 참조하는 Null을 허용하지 않는 `user_consumable_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def user_consumable_id(cls):
        return Column(Integer, ForeignKey('user_consumables.id'), nullable=False)

class AlertRuleFKMixin:
    """
    `alert_rules` 테이블을 참조하는 Null을 허용하지 않는 `alert_rule_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def alert_rule_id(cls):
        return Column(Integer, ForeignKey('alert_rules.id'), nullable=False)

class ProductionEventFKMixin:
    """
    `production_events` 테이블을 참조하는 Null을 허용하지 않는 `production_event_id` 외래 키 컬럼을 모델에 추가하기 위한 Mixin입니다.
    """
    @declared_attr
    def production_event_id(cls):
        return Column(Integer, ForeignKey('production_events.id'), nullable=False)
        
class LogBaseMixin:
    """
    로그 모델 공통 필드를 위한 Mixin. 온톨로지에서 '이벤트' 단일 객체 취급 용이.
    """
    @declared_attr
    def event_type(cls):
        return Column(Enum('DEVICE', 'AUDIT', 'CONSUMABLE_USAGE', 'SERVER_MQTT_CERTIFICATE_ISSUED', 'DEVICE_CERTIFICATE_CREATED', 'CERTIFICATE_REVOKED', 'SERVER_CERTIFICATE_ACQUIRED_NEW', name='log_event_type'), 
                      nullable=False, comment="로그 유형 (온톨로지 통합 쿼리 용)")

    @declared_attr
    def log_level(cls):
        return Column(Enum('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', name='log_level'), 
                      nullable=True, comment="로그 심각도 (선택적)")

    @declared_attr
    def description(cls):
        return Column(Text, nullable=True, comment="로그 설명/메시지")