# services/device_command_service.py

import logging # 로깅 추가
from sqlalchemy.orm import Session

# --- Model Imports ---
from app.models.objects.device import Device as DBDevice
from app.models.objects.user import User
from app.models.objects.organization import Organization
from app.models.objects.hardware_blueprint import HardwareBlueprint

# --- ID Generator and Exceptions ---
from app.core.id_generator import generate_device_id
from app.core.exceptions import NotFoundError, DuplicateEntryError

# --- CRUD and Schema Imports ---
from ..crud.device_command_crud import device_command_crud
from ..schemas.device_command import DeviceCreate, DeviceUpdate

# --- Provider & Repository Imports ---
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from ..repositories.vault_hmac_repository import vault_hmac_repository # Vault HMAC 리포지토리 추가

logger = logging.getLogger(__name__) # 로거 인스턴스

class DeviceManagementCommandService:
    """장치의 생명주기(생성, 수정, 삭제)를 관리하는 Command 서비스입니다."""

    def create_device(self, db: Session, *, obj_in: DeviceCreate, actor_user: User) -> DBDevice:
        """새로운 장치를 생성하고, 이 과정에서 ID 생성 전략을 사용해 고유 식별자를 발급하고 Vault에 HMAC 키를 생성합니다."""
        # 방어적 확인
        if not db.query(HardwareBlueprint).filter(HardwareBlueprint.id == obj_in.hardware_blueprint_id).first():
            raise NotFoundError("HardwareBlueprint", str(obj_in.hardware_blueprint_id))
        if db.query(DBDevice).filter(DBDevice.cpu_serial == obj_in.cpu_serial).first():
            raise DuplicateEntryError("Device", "cpu_serial", obj_in.cpu_serial)

        # 1. UUID와 함께 DB에 장치 레코드 생성
        new_id = generate_device_id()
        new_device = device_command_crud.create_with_id(db, obj_in=obj_in, current_id=new_id)
        db.flush() # ID를 즉시 얻기 위해 flush

        # 2. Vault에 HMAC 키 생성
        try:
            hmac_key_name = vault_hmac_repository.create_hmac_key(device_id=str(new_device.id))
            # 3. DB에 Vault 키 이름 저장
            new_device.hmac_key_name = hmac_key_name
            db.add(new_device)
            db.flush()
        except Exception as e:
            # Vault 키 생성 실패 시 롤백 로직 추가 필요 (여기서는 로깅만)
            # 혹은, 장치 생성을 트랜잭션으로 묶어 전체 롤백
            logger.error(f"Failed to create Vault HMAC key for device {new_device.id}: {e}")
            # 이 경우 생성된 장치를 삭제하거나, 에러를 다시 발생시켜 전체 트랜잭션을 롤백해야 함
            raise

        # 4. 감사 로그 기록
        audit_command_provider.log_creation(
            db=db,
            actor_user=actor_user,
            resource_name="Device",
            resource_id=new_device.id,
            new_value=new_device.as_dict()
        )
        return new_device

    def update_device(self, db: Session, *, device_id: int, obj_in: DeviceUpdate, actor_user: User) -> DBDevice:
        """기존 장치 정보를 업데이트합니다."""
        db_obj = device_command_crud.get(db, id=device_id)
        # 방어적 확인 (FKs)
        if obj_in.hardware_blueprint_id and not db.query(HardwareBlueprint).filter(HardwareBlueprint.id == obj_in.hardware_blueprint_id).first():
            raise NotFoundError("HardwareBlueprint", str(obj_in.hardware_blueprint_id))

        old_value = db_obj.as_dict()
        updated_device = device_command_crud.update(db, db_obj=db_obj, obj_in=obj_in)
        db.flush()

        audit_command_provider.log_update(
            db=db,
            actor_user=actor_user,
            resource_name="Device",
            resource_id=updated_device.id,
            old_value=old_value,
            new_value=updated_device.as_dict()
        )
        return updated_device

    def delete_device(self, db: Session, *, device_id: int, actor_user: User) -> DBDevice:
        """장치를 비활성화하여 소프트 삭제합니다."""
        db_obj = device_command_crud.get(db, id=device_id)
        old_value = db_obj.as_dict()
        
        # remove 메소드는 device_command_crud에 소프트 삭제로 구현되어 있음
        deleted_device = device_command_crud.remove(db, id=device_id)
        db.flush()
        
        audit_command_provider.log_update(
            db=db,
            actor_user=actor_user,
            resource_name="Device",
            resource_id=deleted_device.id,
            old_value=old_value,
            new_value=deleted_device.as_dict()
        )
        return deleted_device

device_management_command_service = DeviceManagementCommandService()
