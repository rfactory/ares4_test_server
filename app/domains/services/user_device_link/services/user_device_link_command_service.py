# --- 명령 관련 서비스 ---
# 이 파일은 사용자와 기기 연결 상태의 변경(생성, 수정, 삭제)을 담당하는 서비스입니다.
# [핵심 원칙] 이 서비스는 순수한 데이터 조작만을 담당하며, 비즈니스 로직 및 권한 검사는 Policy 계층에서 처리됩니다.

from sqlalchemy.orm import Session
from typing import Optional

from app.core.exceptions import NotFoundError # Policy에서 확인하지만, 서비스 내부의 방어적 코드로 남겨둠
from app.models.relationships.user_device import UserDevice
from app.models.objects.user import User
from app.models.objects.device import Device # 기기 존재 여부 확인용
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

from ..crud.user_device_link_command_crud import user_device_link_command_crud
from ..crud.user_device_link_query_crud import user_device_link_query_crud
from ..schemas.user_device_link_command import UserDeviceLinkCreate, UserDeviceLinkUpdate

class UserDeviceLinkCommandService:
    def link_device_to_user(
        self,
        db: Session,
        *,
        link_in: UserDeviceLinkCreate,
        actor_user: User,
    ) -> UserDevice:
        """
        사용자와 기기 간의 새로운 링크를 생성합니다.
        모든 비즈니스 로직 및 권한 검증은 Policy 계층에서 완료되었다고 가정합니다.
        """
        # 방어적 확인: user_id와 device_id가 유효한지 확인
        existing_user = db.query(User).filter(User.id == link_in.user_id).first()
        if not existing_user:
            raise NotFoundError("User", str(link_in.user_id))
        
        existing_device = db.query(Device).filter(Device.id == link_in.device_id).first()
        if not existing_device:
            raise NotFoundError("Device", str(link_in.device_id))

        # 1. CRUD를 통해 새로운 링크 생성
        new_link = user_device_link_command_crud.create(db, obj_in=link_in)

        # db.commit() 및 db.refresh()는 Policy 계층에서 담당합니다.

        # 3. 감사 로그 기록
        audit_command_provider.log_creation(
            db=db,
            actor_user=actor_user,
            resource_name="UserDeviceLink",
            resource_id=new_link.id,
            new_value=new_link.as_dict() # as_dict() 메소드가 모델에 있다고 가정
        )

        return new_link

    def update_link(
        self,
        db: Session,
        *,
        user_id: int,
        device_id: int,
        link_in: UserDeviceLinkUpdate,
        actor_user: User,
    ) -> Optional[UserDevice]:
        """
        사용자와 기기 간의 기존 링크를 업데이트합니다.
        모든 비즈니스 로직 및 권한 검증은 Policy 계층에서 완료되었다고 가정합니다.
        """
        link_to_update = user_device_link_query_crud.get_by_user_id_and_device_id(
            db, user_id=user_id, device_id=device_id
        )
        if not link_to_update:
            raise NotFoundError("User-Device Link", f"User ID: {user_id}, Device ID: {device_id}")

        old_value = link_to_update.as_dict() if hasattr(link_to_update, 'as_dict') else str(link_to_update)

        updated_link = user_device_link_command_crud.update(db, db_obj=link_to_update, obj_in=link_in)
        # db.commit() 및 db.refresh()는 Policy 계층에서 담당합니다.

        audit_command_provider.log_update(
            db=db,
            actor_user=actor_user,
            resource_name="UserDeviceLink",
            resource_id=updated_link.id,
            old_value=old_value,
            new_value=updated_link.as_dict() if hasattr(updated_link, 'as_dict') else str(updated_link)
        )
        return updated_link

    def remove_link(
        self,
        db: Session,
        *,
        user_id: int,
        device_id: int,
        actor_user: User,
    ) -> None:
        """
        사용자와 기기 간의 링크를 삭제합니다. (하드 삭제)
        모든 비즈니스 로직 및 권한 검증은 Policy 계층에서 완료되었다고 가정합니다.
        """
        link_to_delete = user_device_link_query_crud.get_by_user_id_and_device_id(
            db, user_id=user_id, device_id=device_id
        )
        if not link_to_delete:
            raise NotFoundError("User-Device Link", f"User ID: {user_id}, Device ID: {device_id}")
        
        deleted_value = link_to_delete.as_dict() if hasattr(link_to_delete, 'as_dict') else str(link_to_delete)

        user_device_link_command_crud.remove(db, id=link_to_delete.id)
        # db.commit()은 Policy 계층에서 담당합니다.

        audit_command_provider.log_deletion(
            db=db,
            actor_user=actor_user,
            resource_name="UserDeviceLink",
            resource_id=link_to_delete.id,
            deleted_value=deleted_value
        )
        return
user_device_link_command_service = UserDeviceLinkCommandService()
