from sqlalchemy.orm import Session
from typing import List, Dict

# 모델 임포트
from app.models.objects.device import Device
from app.models.internal.internal_blueprint_component import InternalBlueprintComponent
from app.models.relationships.blueprint_pin_mapping import BlueprintPinMapping
from app.models.relationships.device_component_instance import DeviceComponentInstance
from app.models.relationships.device_component_pin_mapping import PinStatusEnum

# CRUD 및 스키마
from ..crud.pin_mapping_command_crud import pin_mapping_crud_command
from ..schemas.pin_mapping_command import PinMappingCreate

class PinMappingCommandService:
    def clone_from_blueprint(self, db: Session, *, device_id: int) -> int:
        """[P3.4] 설계도 기반 부품 인스턴스 및 핀(ACTIVE) 통합 복제"""
        
        # 1. 기기 정보 확인
        device = db.get(Device, device_id)
        if not device or not device.hardware_blueprint_id:
            return 0

        # 2. 설계도에 정의된 부품 리스트(BOM) 조회
        # InternalBlueprintComponent에는 name이 없고 asset_definition에 이름이 있습니다.
        blueprint_components: List[InternalBlueprintComponent] = db.query(InternalBlueprintComponent).filter(
            InternalBlueprintComponent.hardware_blueprint_id == device.hardware_blueprint_id
        ).all()
        
        instance_map: Dict[int, int] = {} # {asset_definition_id: new_instance_id}
        
        for bc in blueprint_components:
            component_name = bc.asset_definition.name if bc.asset_definition else f"Component_{bc.id}"
            
            new_instance = DeviceComponentInstance(
                device_id=device_id,
                component_type_id=bc.asset_definition_id, 
                instance_name=component_name,
                is_active=True
            )
            db.add(new_instance)
            db.flush()
            
            # 핀 매핑 시 찾기 위해 asset_definition_id를 키로 저장
            instance_map[bc.asset_definition_id] = new_instance.id

        # 3. 설계도 핀 매핑 정보를 실제 테이블로 복제
        blueprint_pins: List[BlueprintPinMapping] = db.query(BlueprintPinMapping).filter(
            BlueprintPinMapping.hardware_blueprint_id == device.hardware_blueprint_id
        ).all()

        create_list = []
        for bp in blueprint_pins:
            create_list.append(PinMappingCreate(
                pin_name=bp.pin_name,
                pin_number=bp.pin_number if bp.pin_number is not None else 0, # Null 처리
                pin_mode=bp.pin_mode or "INPUT",
                device_id=device_id,
                device_component_instance_id=instance_map.get(bp.supported_component_id),
                status=PinStatusEnum.ACTIVE
            ))

        if not create_list:
            return 0

        new_mappings = pin_mapping_crud_command.create_multiple(db, obj_in_list=create_list)
        db.commit()
        return len(new_mappings)
    
    def update_pin(self, db: Session, *, mapping_id: int, new_pin: int) -> bool:
        """[P4.2] 사용자가 수정한 실제 핀 번호를 DB에 반영합니다."""
        # CRUD를 통해 해당 핀 매핑 정보 조회
        mapping = pin_mapping_crud_command.get(db, id=mapping_id)
        
        if not mapping:
            return False
        
        # 고장(FAULTY) 상태인 핀은 설정을 변경할 수 없게 차단
        if mapping.status == PinStatusEnum.FAULTY:
            # 여기서는 로직 에러를 던지거나 False를 반환합니다.
            return False
        
        # 핀 번호 업데이트
        pin_mapping_crud_command.update(
            db, 
            db_obj=mapping, 
            obj_in={"pin_number": new_pin}
        )
        return True

pin_mapping_command_service = PinMappingCommandService()