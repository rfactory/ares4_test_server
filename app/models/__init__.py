from .objects.user import User
from .objects.role import Role
from .objects.permission import Permission
from .objects.organization import Organization
from .objects.organization_type import OrganizationType
from .objects.access_request import AccessRequest
from .objects.product_line import ProductLine
from .objects.device import Device
from .objects.hardware_blueprint import HardwareBlueprint
from .objects.supported_component import SupportedComponent
from .objects.subscription_plan import SubscriptionPlan
from .objects.governance import GovernanceRule # 새로 추가
# TODO: RegistrationRequest 모델은 현재 사용되지 않으며, 해당 파일이 존재하지 않습니다. (2025-12-02)
# from .objects.registration_request import RegistrationRequest

from .relationships.user_organization_role import UserOrganizationRole
from .relationships.organization_device import OrganizationDevice
from .relationships.organization_subscription import OrganizationSubscription
from .relationships.user_device import UserDevice
from .relationships.role_permission import RolePermission
from .relationships.device_component_instance import DeviceComponentInstance
from .relationships.device_component_pin_mapping import DeviceComponentPinMapping
from .relationships.blueprint_valid_pin import BlueprintValidPin
from .relationships.blueprint_pin_mapping import BlueprintPinMapping
from .relationships.blueprint_pin_detail import BlueprintPinDetail
from .relationships.plan_applicable_blueprint import PlanApplicableBlueprint
from .relationships.subscription_plan_feature import SubscriptionPlanFeature
from .relationships.alert_rule import AlertRule
from .relationships.schedule import Schedule
from .relationships.trigger_rule import TriggerRule
from .relationships.user_subscription import UserSubscription
from .relationships.supported_component_metadata import SupportedComponentMetadata
# TODO: UpgradeRequest 모델은 현재 사용되지 않으며, 해당 파일이 존재하지 않습니다. (2025-12-02)
# from .relationships.upgrade_request import UpgradeRequest

from .events_logs.audit_log import AuditLog
from .events_logs.audit_log_detail import AuditLogDetail
from .events_logs.telemetry_data import TelemetryData
from .events_logs.device_log import DeviceLog
from .events_logs.firmware_update import FirmwareUpdate
from .events_logs.consumable_usage_log import ConsumableUsageLog
from .events_logs.consumable_replacement_event import ConsumableReplacementEvent
from .events_logs.alert_event import AlertEvent
from .events_logs.production_event import ProductionEvent
from .events_logs.image_analysis import ImageAnalysis
from .events_logs.telemetry_metadata import TelemetryMetadata
from .events_logs.user_consumable import UserConsumable

from .internal.internal_asset_definition import InternalAssetDefinition
from .internal.internal_asset_inventory import InternalAssetInventory
from .internal.internal_asset_purchase_record import InternalAssetPurchaseRecord
from .internal.internal_blueprint_component import InternalBlueprintComponent
from .internal.internal_component_replacement_event import InternalComponentReplacementEvent


__all__ = [
    "User",
    "Role",
    "Permission",
    "Organization",
    "OrganizationType",
    "AccessRequest",
    "ProductLine",
    "Device",
    "HardwareBlueprint",
    "SupportedComponent",
    "SubscriptionPlan",
    "GovernanceRule", # 새로 추가
    # "RegistrationRequest", # TODO: 모델 복원 시 주석 해제

    "UserOrganizationRole",
    "OrganizationDevice",
    "OrganizationSubscription",
    "UserDevice",
    "RolePermission",
    "DeviceComponentInstance",
    "DeviceComponentPinMapping",
    "BlueprintValidPin",
    "BlueprintPinMapping",
    "BlueprintPinDetail",
    "PlanApplicableBlueprint",
    "SubscriptionPlanFeature",
    "AlertRule",
    "Schedule",
    "TriggerRule",
    "UserSubscription",
    "SupportedComponentMetadata",
    # "UpgradeRequest", # TODO: 모델 복원 시 주석 해제

    "AuditLog",
    "AuditLogDetail",
    "TelemetryData",
    "DeviceLog",
    "FirmwareUpdate",
    "ConsumableUsageLog",
    "ConsumableReplacementEvent",
    "AlertEvent",
    "ProductionEvent",
    "ImageAnalysis",
    "TelemetryMetadata",
    "UserConsumable",

    "InternalAssetDefinition",
    "InternalAssetInventory",
    "InternalAssetPurchaseRecord",
    "InternalBlueprintComponent",
    "InternalComponentReplacementEvent",
]
