from sqlalchemy.orm import Session
from typing import Optional

from app.core.exceptions import DuplicateEntryError, NotFoundError
from app.models.objects.device import Device
from app.models.objects.organization import Organization
from app.models.objects.user import User
from ..crud.organization_device_link_command_crud import organization_device_link_command_crud
from ..crud.organization_device_link_query_crud import organization_device_link_query_crud
from ..schemas.organization_device_link_command import OrganizationDeviceLinkCreate, OrganizationDeviceLinkUpdate
from app.models.relationships.organization_device import OrganizationDevice
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class OrganizationDeviceLinkCommandService:
    def assign_device(
        self, db: Session, *, link_in: OrganizationDeviceLinkCreate, actor_user: User
    ) -> OrganizationDevice:
        """장치를 조직에 할당합니다."""
        # 방어적 확인: 조직 ID와 장치 ID가 유효한지 확인
        if not db.query(Organization).filter(Organization.id == link_in.organization_id).first():
            raise NotFoundError("Organization", str(link_in.organization_id))
        if not db.query(Device).filter(Device.id == link_in.device_id).first():
            raise NotFoundError("Device", str(link_in.device_id))

        # 중복 할당 방지
        existing_link = organization_device_link_query_crud.get_by_organization_id_and_device_id_and_relationship_type(
            db,
            organization_id=link_in.organization_id,
            device_id=link_in.device_id,
            relationship_type=link_in.relationship_type.value # Enum 값을 문자열로 전달
        )
        if existing_link:
            raise DuplicateEntryError(
                "OrganizationDeviceLink",
                "organization_id, device_id, relationship_type",
                f"{link_in.organization_id}-{link_in.device_id}-{link_in.relationship_type.value}"
            )

        new_link = organization_device_link_command_crud.create(db, obj_in=link_in)
        db.flush()

        audit_command_provider.log_creation(
            db=db,
            actor_user=actor_user,
            resource_name="OrganizationDeviceLink",
            resource_id=new_link.id,
            new_value=new_link.as_dict()
        )
        return new_link

    def unassign_device(self, db: Session, *, link_id: int, actor_user: User) -> OrganizationDevice:
        """장치의 조직 할당을 해제합니다 (soft-delete)."""
        db_link = organization_device_link_query_crud.get(db, id=link_id)
        if not db_link:
            raise NotFoundError("OrganizationDeviceLink", str(link_id))

        old_value = db_link.as_dict()
        unassigned_link = organization_device_link_command_crud.remove(db, id=link_id)
        db.flush()

        audit_command_provider.log_update(
            db=db,
            actor_user=actor_user,
            resource_name="OrganizationDeviceLink",
            resource_id=unassigned_link.id,
            old_value=old_value,
            new_value=unassigned_link.as_dict()
        )
        return unassigned_link

    def update_assignment(
        self, db: Session, *, link_id: int, link_in: OrganizationDeviceLinkUpdate, actor_user: User
    ) -> OrganizationDevice:
        """장치 할당 정보를 업데이트합니다."""
        db_link = organization_device_link_query_crud.get(db, id=link_id)
        if not db_link:
            raise NotFoundError("OrganizationDeviceLink", str(link_id))
        
        old_value = db_link.as_dict()

        # 관계 유형 변경 시 중복 체크
        if link_in.relationship_type and link_in.relationship_type.value != db_link.relationship_type.value:
            existing_link = organization_device_link_query_crud.get_by_organization_id_and_device_id_and_relationship_type(
                db,
                organization_id=db_link.organization_id,
                device_id=db_link.device_id,
                relationship_type=link_in.relationship_type.value # Enum 값을 문자열로 전달
            )
            if existing_link and existing_link.id != link_id:
                raise DuplicateEntryError(
                    "OrganizationDeviceLink",
                    "organization_id, device_id, relationship_type",
                    f"{db_link.organization_id}-{db_link.device_id}-{link_in.relationship_type.value}"
                )

        updated_link = organization_device_link_command_crud.update(db, db_obj=db_link, obj_in=link_in)
        db.flush()

        audit_command_provider.log_update(
            db=db,
            actor_user=actor_user,
            resource_name="OrganizationDeviceLink",
            resource_id=updated_link.id,
            old_value=old_value,
            new_value=updated_link.as_dict()
        )
        return updated_link

organization_device_link_command_service = OrganizationDeviceLinkCommandService()
