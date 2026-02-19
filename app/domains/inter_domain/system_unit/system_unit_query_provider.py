from sqlalchemy.orm import Session
from typing import Optional
from app.domains.services.system_unit.services.system_unit_query_service import system_unit_query_service
from app.domains.services.system_unit.schemas.system_unit_query import SystemUnitRead

class SystemUnitQueryProvider:
    """
    [Inter-Domain Provider] 
    Policy나 다른 도메인에서 시스템 유닛 정보를 조회할 때 사용하는 공식 통로
    """
    def get_by_id(self, db: Session, *, unit_id: int) -> Optional[SystemUnitRead]:
        return system_unit_query_service.get_system_unit(db, id=unit_id)

system_unit_query_provider = SystemUnitQueryProvider()