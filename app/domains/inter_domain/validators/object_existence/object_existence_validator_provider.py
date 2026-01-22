from typing import Optional, Any
from app.domains.action_authorization.validators.object_existence.validator import object_existence_validator

class ObjectExistenceValidatorProvider:
    def validate(self, *, obj: Optional[Any], obj_name: str, identifier: str, should_exist: bool):
        """범용 ObjectExistenceValidator를 호출하여 객체의 존재 유효성을 검사합니다."""
        return object_existence_validator.validate(
            obj=obj, 
            obj_name=obj_name, 
            identifier=identifier, 
            should_exist=should_exist
        )

object_existence_validator_provider = ObjectExistenceValidatorProvider()