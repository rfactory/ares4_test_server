import logging
import uuid
import secrets
from sqlalchemy.orm import Session
from typing import Optional, Tuple, List
from datetime import datetime, timezone

# --- Model Imports ---
from app.models.objects.device import Device as DBDevice, DeviceStatusEnum
from app.models.objects.user import User
from app.models.objects.hardware_blueprint import HardwareBlueprint
from app.models.objects.system_unit import SystemUnit

# --- ID Generator and Exceptions ---
from app.core.id_generator import generate_device_id
from app.core.exceptions import NotFoundError, DuplicateEntryError

# --- CRUD and Schema Imports ---
from ..crud.device_command_crud import device_command_crud
from ..schemas.device_command import DeviceCreate, DeviceUpdate

# --- Provider & Repository Imports ---
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from ..repositories.vault_hmac_repository import vault_hmac_repository
from app.domains.inter_domain.device_management.hmac_command_provider import hmac_command_provider
from app.domains.inter_domain.certificate_management.certificate_command_provider import certificate_command_provider

logger = logging.getLogger(__name__)

class DeviceManagementCommandService:
    """장치의 생명주기(생성, 수정, 삭제)를 관리하는 Command 서비스입니다."""

    def _get_default_blueprint_id(self, db: Session) -> Optional[int]:
        """
        [수정] 기본 블루프린트를 찾되, 없으면 None을 반환합니다. (강제성 제거)
        """
        blueprint = db.query(HardwareBlueprint).order_by(HardwareBlueprint.id.asc()).first()
        if not blueprint:
            # 에러 대신 경고 로그만 남기고 통과시킵니다.
            logger.warning("⚠️ 등록된 HardwareBlueprint가 없습니다. 기기는 'Unknown Device'로 등록됩니다.")
            return None
        return blueprint.id

    def _get_target_unit_id(self, db: Session, target_unit_name: str = None) -> Optional[int]:
        """
        이름으로 유닛을 찾습니다. 없거나 이름이 안 들어오면 None을 리턴합니다.
        """
        if not target_unit_name:
            return None 

        unit = db.query(SystemUnit).filter(SystemUnit.name == target_unit_name).first()
        if unit:
            return unit.id
        else:
            logger.warning(f"⚠️ 요청받은 유닛 '{target_unit_name}'을 찾을 수 없습니다. 무소속으로 설정합니다.")
            return None

    def create_device(self, db: Session, *, obj_in: DeviceCreate, actor_user: Optional[User] = None) -> DBDevice:
        """새로운 장치를 생성하고 고유 식별자 발급 및 Vault에 HMAC 키를 생성합니다."""
        
        # [수정] Blueprint ID가 있을 때만 DB 존재 여부 확인
        if obj_in.hardware_blueprint_id:
            if not db.query(HardwareBlueprint).filter(HardwareBlueprint.id == obj_in.hardware_blueprint_id).first():
                raise NotFoundError("HardwareBlueprint", str(obj_in.hardware_blueprint_id))
        
        # 시리얼 중복 확인
        if db.query(DBDevice).filter(DBDevice.cpu_serial == obj_in.cpu_serial).first():
            raise DuplicateEntryError("Device", "cpu_serial", obj_in.cpu_serial)

        # 1. UUID와 함께 DB에 장치 레코드 생성
        new_id = generate_device_id()
        new_device = device_command_crud.create_with_id(db, obj_in=obj_in, current_id=new_id)
        db.flush()

        # 2. Vault에 HMAC 키 생성
        try:
            if obj_in.hmac_key_name:
                logger.info(f"🔑 Using pre-defined HMAC key path: {obj_in.hmac_key_name}")
                new_device.hmac_key_name = obj_in.hmac_key_name
            else:
                logger.info("🛠️ Generating new HMAC key via Transit Engine...")
                hmac_key_name = vault_hmac_repository.create_hmac_key(device_id=str(new_device.id))
                new_device.hmac_key_name = hmac_key_name
            
            db.add(new_device)
            db.flush()
        except Exception as e:
            logger.error(f"Failed to finalize Vault HMAC for device {new_device.id}: {e}")
            raise

        # 3. 감사 로그 기록
        audit_command_provider.log_creation(
            db=db, 
            actor_user=actor_user, 
            resource_name="Device",
            resource_id=new_device.id, 
            new_value=new_device.as_dict()
        )
        return new_device
    
    async def execute_factory_enrollment_transaction(
        self, db: Session, cpu_serial: str, client_ip: str,
        target_unit_name: str = None, components: List[str] = None, auto_activate: bool = False
    ) -> dict:
        """
        [핵심] 공장 등록 통합 트랜잭션. 
        청사진과 유닛이 없어도 기기를 등록할 수 있도록 유연하게 처리합니다.
        """
        # A. 정체성 데이터 생성
        new_uuid = str(uuid.uuid4())
        new_hmac_key = secrets.token_hex(32)
        vault_path = f"ares4/hmac/{cpu_serial}"

        # B. HMAC 저장
        hmac_svc = hmac_command_provider.get_service()
        hmac_svc.store_device_hmac(path=vault_path, key=new_hmac_key)

        bp_id = self._get_default_blueprint_id(db)
        unit_id = self._get_target_unit_id(db, target_unit_name)

        # 상태 결정 (자동 활성화 요청이 있고 + 유닛도 배정되었을 때만 ONLINE)
        if auto_activate and unit_id:
            initial_status = "ONLINE"
        else:
            initial_status = "PENDING"

        # C. DB 등록
        obj_in = DeviceCreate(
            cpu_serial=cpu_serial,
            uuid=new_uuid,
            status=initial_status,
            hmac_key_name=vault_path,
            hardware_blueprint_id=bp_id, # None이어도 OK
            system_unit_id=unit_id       # None이어도 OK
        )
        
        # 시스템 유저(actor=None) 권한으로 생성
        new_device = self.create_device(db, obj_in=obj_in, actor_user=None)
        
        new_device.hmac_secret_key = new_hmac_key
        db.add(new_device)
        db.flush()
        db.refresh(new_device)

        # D. mTLS 인증서 발급
        cert_svc = certificate_command_provider.get_service()
        certs = cert_svc.create_device_certificate(db=db, common_name=new_uuid)
        
        db.flush()
        logger.info(f"⚙️ [Service] Device {new_uuid} prepared for commitment.")

        return {
            "device_id": new_uuid,
            "hmac_key": new_hmac_key,
            **certs,
            "status": initial_status,
            "unit_id": unit_id,
            "blueprint_id": bp_id
        }
    
    def update_device(self, db: Session, *, device_id: int, obj_in: DeviceUpdate, actor_user: Optional[User] = None) -> DBDevice:
        """기존 장치 정보를 업데이트합니다."""
        db_obj = device_command_crud.get(db, id=device_id)
        
        if obj_in.hardware_blueprint_id:
            if not db.query(HardwareBlueprint).filter(HardwareBlueprint.id == obj_in.hardware_blueprint_id).first():
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

    def delete_device(self, db: Session, *, device_id: int, actor_user: Optional[User] = None) -> DBDevice:
        """장치를 비활성화하여 소프트 삭제합니다."""
        db_obj = device_command_crud.get(db, id=device_id)
        old_value = db_obj.as_dict()
        
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
    
    def update_last_seen(self, db: Session, *, device_id: int) -> Optional[DBDevice]:
        """기기의 마지막 활동 시간을 현재 서버 시간으로 업데이트합니다."""
        db_obj = device_command_crud.get(db, id=device_id)
        if not db_obj:
            return None
        
        # 별도의 Audit 로그 없이 고속 업데이트 (성능을 위해 flush만 실행)
        db_obj.last_seen_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.flush()
        return db_obj
    
    def assign_to_unit(self, db: Session, *, device_id: int, unit_id: int, role: str) -> DBDevice:
        """
        [The Binder]
        기기를 특정 시스템 유닛에 귀속시키고 상태를 PROVISIONED로 변경합니다.
        """
        device = db.query(DBDevice).filter(DBDevice.id == device_id).first()
        if not device:
            raise NotFoundError("Device", f"ID {device_id}를 찾을 수 없습니다.")

        device.system_unit_id = unit_id
        device.status = DeviceStatusEnum.PROVISIONED  # 결합 상태로 변경
        
        if hasattr(device, 'cluster_role'):
            device.cluster_role = role
        
        db.add(device)
        db.flush()
        return device
    
    def unbind_from_unit(self, db: Session, *, device_id: int) -> DBDevice:
        """
        [The Liberator]
        기기를 유닛에서 해제하여 '무주공산' 상태로 돌려놓습니다.
        """
        device = db.query(DBDevice).filter(DBDevice.id == device_id).first()
        if not device:
            raise NotFoundError("Device", f"ID {device_id}를 찾을 수 없습니다.")

        device.system_unit_id = None
        device.status = DeviceStatusEnum.PENDING
        
        if hasattr(device, 'cluster_role'):
            device.cluster_role = None
        
        db.add(device)
        db.flush()
        return device
    
device_management_command_service = DeviceManagementCommandService()