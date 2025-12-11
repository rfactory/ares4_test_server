from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Protocol # Added Protocol

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError  # 커스텀 예외 가정

class BaseWithId(Protocol):
    id: int # More specific than Any

ModelType = TypeVar("ModelType", bound=BaseWithId) # Bounded ModelType
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        obj = db.query(self.model).filter(self.model.id == id).first()
        if not obj:
            raise NotFoundError(resource_name=self.model.__name__, resource_id=id) # Corrected NotFoundError call
        return obj

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.flush() # Flush to get ID for related objects if needed
        return db_obj

    def update(self, db: Session, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data: # only update set values
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        return db_obj

    def remove(self, db: Session, id: int) -> Optional[ModelType]:
        obj = db.query(self.model).get(id)
        if not obj:
            raise NotFoundError(resource_name=self.model.__name__, resource_id=id) # Corrected NotFoundError call
        db.delete(obj)
        return obj
