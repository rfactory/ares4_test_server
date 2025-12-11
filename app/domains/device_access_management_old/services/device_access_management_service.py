from sqlalchemy.orm import Session
from typing import List, Optional, Union, Literal, Any
from pydantic import BaseModel, ConfigDict

from ..crud.user_device_link_crud import user_device_link_crud
from ..schemas.user_device import UserDeviceCreate
from app.models.relationships.user_device import UserDevice
from app.models.objects.user import User as DBUser
from app.models.objects.device import Device
from app.core.exceptions import PermissionDeniedError, NotFoundError
from app.domains.inter_domain.audit.providers import audit_providers
from app.domains.inter_domain.user_authorization.providers import user_authorization_providers
from app.domains.inter_domain.device_management.providers import device_management_providers

# 개인 컨텍스트를 위한 특별 응답 스키마
class PersonalDeviceResponse(BaseModel):
    nickname: Optional[str] # Made optional
    role: str
    device: Device

    model_config = ConfigDict(from_attributes=True)


class DeviceAccessManagementService:
    def link_device_to_user(self, db: Session, *, link_in: UserDeviceCreate, actor_user: DBUser) -> UserDevice:
        """사용자를 특정 역할(예: owner, viewer)로 장치에 연결합니다."""
        # TODO: 중복 연결 방지 로직 추가 필요.
        db_link = user_device_link_crud.create(db, obj_in=link_in)

        audit_providers.log(
            db=db,
            event_type="USER_DEVICE_LINK_CREATED",
            description=f"User {link_in.user_id} was linked to device {link_in.device_id} with role '{link_in.role}'.",
            actor_user=actor_user,
            details={"user_id": link_in.user_id, "device_id": link_in.device_id, "role": link_in.role}
        )
        return db_link

    def get_links_for_device(self, db: Session, *, device_id: int) -> List[UserDevice]:
        """특정 장치에 대한 모든 사용자 연결을 가져옵니다."""
        return user_device_link_crud.get_multi_by_device(db, device_id=device_id)

    def remove_link(self, db: Session, *, user_id: int, device_id: int, actor_user: DBUser) -> Optional[UserDevice]:
        """사용자와 장치 간의 연결을 제거합니다."""
        # TODO: user_id와 device_id로 링크 조회 후 제거 로직 필요.
        db_link = user_device_link_crud.remove_by_user_and_device(db, user_id=user_id, device_id=device_id)
        
        if db_link:
            audit_providers.log(
                db=db,
                event_type="USER_DEVICE_LINK_REMOVED",
                description=f"Link between user {user_id} and device {device_id} was removed.",
                actor_user=actor_user,
                details={"user_id": user_id, "device_id": device_id}
            )
        return db_link

    def is_user_owner_of_device(self, db: Session, *, user_id: int, device_id: int) -> bool:
        """사용자가 특정 장치의 'owner'인지 확인합니다."""
        link = user_device_link_crud.get_by_user_and_device_with_role(db, user_id=user_id, device_id=device_id, role='owner')
        return link is not None

    def _get_device_with_access_check(self, db: Session, *, device_id: int, request_user: DBUser, permission_name: str, active_context: Union[Literal['personal', 'global'], int]) -> Device:
        """[내부 헬퍼] 컨텍스트 기반으로 단일 장치에 대한 접근 권한을 확인하는 핵심 로직"""
        db_device = device_management_providers.get_device(db, device_id=device_id)
        if not db_device:
            raise NotFoundError(resource_name="Device", resource_id=str(device_id))

        # 1. 개인 컨텍스트 확인
        if active_context == 'personal':
            if self.is_user_owner_of_device(db, user_id=request_user.id, device_id=device_id):
                return db_device
        
        # 2. 조직 컨텍스트 확인
        elif isinstance(active_context, int):
            if db_device.organization_id == active_context and user_authorization_providers.check_user_permission(db, user=request_user, permission_name=permission_name, organization_id=active_context):
                return db_device

        # 3. 전역 컨텍스트 확인 (관리자용)
        elif active_context == 'global':
            if user_authorization_providers.check_user_permission(db, user=request_user, permission_name=f"{permission_name}_all"):
                return db_device

        raise PermissionDeniedError(f"User does not have permission for '{permission_name}' on device {device_id} in the given context.")

    def get_device_if_user_has_read_access(self, db: Session, *, device_id: int, request_user: DBUser, active_context: Union[Literal['personal', 'global'], int]) -> Device:
        """컨텍스트 기반으로 읽기 권한을 확인하고 장치를 반환합니다."""
        return self._get_device_with_access_check(db, device_id=device_id, request_user=request_user, permission_name="device:read", active_context=active_context)

    def get_device_if_user_has_update_access(self, db: Session, *, device_id: int, request_user: DBUser, active_context: Union[Literal['personal', 'global'], int]) -> Device:
        """컨텍스트 기반으로 수정 권한을 확인하고 장치를 반환합니다."""
        return self._get_device_with_access_check(db, device_id=device_id, request_user=request_user, permission_name="device:update", active_context=active_context)

    def get_device_if_user_has_delete_access(self, db: Session, *, device_id: int, request_user: DBUser, active_context: Union[Literal['personal', 'global'], int]) -> Device:
        """컨텍스트 기반으로 삭제 권한을 확인하고 장치를 반환합니다."""
        return self._get_device_with_access_check(db, device_id=device_id, request_user=request_user, permission_name="device:delete", active_context=active_context)

    def get_visible_device_list(self, db: Session, *, request_user: DBUser, active_context: Union[Literal['personal', 'global'], int], nicknames: Optional[List[str]] = None, skip: int = 0, limit: int = 100) -> List[Any]:
        """활성 컨텍스트에 따라 사용자에게 보여줄 장치 목록을 조회합니다."""
        # 닉네임 필터링을 위한 device_id 목록 초기화
        filtered_device_ids: Optional[List[int]] = None
        if nicknames:
            user_device_links = user_device_link_crud.get_links_by_user(db, user_id=request_user.id, nicknames=nicknames) # type: ignore [arg-type]
            filtered_device_ids = [link.device_id for link in user_device_links]
            if not filtered_device_ids: # 닉네임으로 조회했지만 아무 장치도 찾지 못한 경우
                return []

        if active_context == 'personal':
            # 개인 컨텍스트: 사용자에게 개인적으로 연결된 장치 정보와 역할/닉네임을 함께 반환
            user_device_links = user_device_link_crud.get_links_by_user(db, user_id=request_user.id, nicknames=nicknames)
            return [PersonalDeviceResponse(nickname=link.nickname, role=link.role, device=link.device) for link in user_device_links] # type: ignore [arg-type]

        elif isinstance(active_context, int):
            # 조직 컨텍스트: 해당 조직의 장치 목록을 반환
            org_id = active_context
            if not user_authorization_providers.check_user_permission(db, user=request_user, permission_name="device:read", organization_id=org_id):
                raise PermissionDeniedError(f"{org_id} 조직의 장치를 볼 권한이 없습니다.")
            
            # device_management_providers.get_multi_by_organization는 device_ids 필터를 받음
            return device_management_providers.get_multi_by_organization(db, organization_id=org_id, device_ids=filtered_device_ids, skip=skip, limit=limit)
        
        elif active_context == 'global':
            # 전역 컨텍스트: 모든 장치 목록 반환
            if not user_authorization_providers.check_user_permission(db, user=request_user, permission_name="device:read_all"):
                raise PermissionDeniedError("모든 장치를 볼 수 있는 전역 권한이 없습니다.")
            
            # device_management_providers.get_multi는 device_ids 필터를 받음
            return device_management_providers.get_multi(db, device_ids=filtered_device_ids, skip=skip, limit=limit)
        
        raise PermissionDeniedError("장치 목록 조회를 위한 유효한 컨텍스트가 제공되지 않았습니다.")

device_access_management_service = DeviceAccessManagementService()
