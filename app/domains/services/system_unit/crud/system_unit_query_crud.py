from sqlalchemy.orm import Session
from typing import Optional
from app.models.objects.system_unit import SystemUnit

class SystemUnitQueryCRUD:
    """
    [Pure Query CRUD] system_units 테이블에 대한 읽기 전용 작업
    """
    def get(self, db: Session, id: int) -> Optional[SystemUnit]:
        return db.query(SystemUnit).filter(SystemUnit.id == id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[SystemUnit]:
        return db.query(SystemUnit).filter(SystemUnit.name == name).first()

system_unit_query_crud = SystemUnitQueryCRUD()