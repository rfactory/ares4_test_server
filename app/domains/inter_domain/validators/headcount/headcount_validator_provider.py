from typing import List, Optional

from app.domains.action_authorization.validators.headcount.headcount_validator import headcount_validator

class HeadcountValidatorProvider:
    def validate(
        self,
        *, 
        role_name: str,
        current_headcount: int, 
        max_headcount: int
    ) -> None:
        return headcount_validator.validate(
            role_name=role_name,
            current_headcount=current_headcount,
            max_headcount=max_headcount
        )

headcount_validator_provider = HeadcountValidatorProvider()
