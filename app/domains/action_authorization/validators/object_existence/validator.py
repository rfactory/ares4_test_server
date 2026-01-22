import logging
from typing import Optional, Any

from app.core.exceptions import DuplicateEntryError, NotFoundError

logger = logging.getLogger(__name__)

class ObjectExistenceValidator:
    def validate(self, *, obj: Optional[Any], obj_name: str, identifier: str, should_exist: bool):
        """
        객체의 존재 여부를 검증합니다. 순수 판단만 수행합니다.
        - obj가 None이고 should_exist가 True이면 NotFoundError 발생
        - obj가 있고 should_exist가 False이면 DuplicateEntryError 발생
        """
        if should_exist and obj is None:
            logger.warning(f"Validation failed: {obj_name} with identifier '{identifier}' does not exist when expected to.")
            raise NotFoundError(obj_name)
        
        if not should_exist and obj is not None:
            logger.warning(f"Validation failed: {obj_name} with identifier '{identifier}' already exists when expected not to.")
            # 동적인 identifier 필드명을 위해 DuplicateEntryError의 메시지를 포맷팅합니다.
            raise DuplicateEntryError(obj_name, "identifier", identifier)

object_existence_validator = ObjectExistenceValidator()