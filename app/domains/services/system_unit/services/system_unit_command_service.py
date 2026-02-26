from sqlalchemy.orm import Session
from typing import List, Optional

# --- [1] Model Imports (타입 추론을 위해 필수) ---
from app.models.objects.user import User
from app.models.objects.system_unit import SystemUnit, UnitStatus
from app.models.objects.product_line import ProductLine # [확인] required_block_count 참조용
from app.models.objects.device import Device

# --- [2] Schema & CRUD Imports ---
from ..crud.system_unit_command_crud import system_unit_command_crud
from ..schemas.system_unit_command import SystemUnitUpdate

class SystemUnitCommandService:
    def update_unit_status(
        self, 
        db: Session, 
        *, 
        unit_id: int, 
        status: UnitStatus, # str 대신 Enum 타입을 사용하여 엄밀함 확보
        actor_user: Optional[User] = None
    ) -> Optional[SystemUnit]:
        """단일 유닛 상태 업데이트 및 감사 로그 기록"""
        obj_in = SystemUnitUpdate(status=status)
        
        db_obj = system_unit_command_crud.update(db, id=unit_id, obj_in=obj_in)
        
        if db_obj and actor_user:
            from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
            audit_command_provider.log_event(
                db=db,
                actor_user=actor_user,
                event_type="UNIT_STATUS_UPDATED",
                description=f"System Unit {unit_id} status changed to {status}",
                details={"unit_id": unit_id, "new_status": str(status)}
            )
        return db_obj
    
    def sync_activation_status(self, db: Session, *, unit_id: int, actor_user: User) -> None:
        """
        [Smart Command] 
        가구의 물리적 규격(required_block_count)과 현재 결합된 기기 대수를 대조하여 
        ACTIVE 또는 PROVISIONING 상태로 자동 동기화합니다.
        """
        # 1. 유닛 정보 확보 및 타입 명시 (IDE 자동 완성 활성화)
        unit: Optional[SystemUnit] = db.query(SystemUnit).filter(SystemUnit.id == unit_id).first()
        
        if not unit or not unit.product_line:
            return

        # 2. 규격(DNA) 확인 - 이제 .required_block_count에 색상이 들어옵니다.
        line_spec: ProductLine = unit.product_line
        required_count: int = line_spec.required_block_count

        # 3. 현재 결합된 유효 기기 카운트
        # 관계인 unit.devices를 직접 사용하면 IDE가 타입을 추론합니다.
        current_count: int = len([d for d in unit.devices if d.system_unit_id == unit_id])
        
        # 4. 상태 결정 (엄밀한 일치 조건)
        new_status = UnitStatus.ACTIVE if current_count == required_count else UnitStatus.PROVISIONING

        # 5. 상태가 변할 때만 업데이트 집행
        if unit.status != new_status:
            self.update_unit_status(
                db, 
                unit_id=unit_id, 
                status=new_status, 
                actor_user=actor_user
            )

system_unit_command_service = SystemUnitCommandService()