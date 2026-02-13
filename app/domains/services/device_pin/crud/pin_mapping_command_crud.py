from sqlalchemy.orm import Session # 타입 힌트용 추가
from app.core.crud_base import CRUDBase
from app.models.relationships.device_component_pin_mapping import DeviceComponentPinMapping
from ..schemas.pin_mapping_command import PinMappingCreate, PinMappingUpdate

class CRUDPinMappingCommand(CRUDBase[DeviceComponentPinMapping, PinMappingCreate, PinMappingUpdate]):
    def create_multiple(self, db: Session, *, obj_in_list: list[PinMappingCreate]):
        """[Laborer] 여러 개의 핀 매핑을 한꺼번에 생성합니다."""
        # model_dump()를 사용하여 Pydantic 객체를 dict로 변환 후 모델 생성
        db_objs = [
            DeviceComponentPinMapping(**obj.model_dump()) 
            for obj in obj_in_list
        ]
        
        # db: Session으로 타입을 지정하면 add_all이 제 색을 찾을 겁니다.
        db.add_all(db_objs)
        
        # ID를 즉시 확인해야 하는 경우를 대비해 flush 수행 (필요 시)
        # db.flush() 
        
        return db_objs

pin_mapping_crud_command = CRUDPinMappingCommand(DeviceComponentPinMapping)