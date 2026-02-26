from sqlalchemy.orm import Session
from typing import Optional
from ..crud.system_unit_query_crud import system_unit_query_crud
from ..schemas.system_unit_query import SystemUnitRead

class SystemUnitQueryService:
    def __init__(self):
        # [수정] 전역 변수로 존재하는 CRUD를 인스턴스 속성으로 등록
        # 그래야 정책에서 provider.get_service().system_unit_query_crud 로 접근 가능합니다.
        from ..crud.system_unit_query_crud import system_unit_query_crud
        self.system_unit_query_crud = system_unit_query_crud
    """
    [Domain Service] 시스템 유닛 도메인의 비즈니스 조회 로직
    """
    def get_system_unit(self, db: Session, *, id: int) -> Optional[SystemUnitRead]:
        db_obj = system_unit_query_crud.get(db, id=id)
        if not db_obj:
            return None
        return SystemUnitRead.model_validate(db_obj)

system_unit_query_service = SystemUnitQueryService()