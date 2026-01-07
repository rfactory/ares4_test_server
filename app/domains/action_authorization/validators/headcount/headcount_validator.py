from app.core.exceptions import AppLogicError

class HeadcountValidator:
    def validate(
        self,
        *, 
        role_name: str,
        current_headcount: int, 
        max_headcount: int
    ) -> None:
        """순수하게 숫자를 비교하여 역할의 최대 인원수 제한을 확인합니다."""
        if max_headcount is not None and max_headcount != -1:
            if current_headcount >= max_headcount:
                raise AppLogicError(f"Cannot assign {role_name}. Maximum headcount of {max_headcount} already reached.")

headcount_validator = HeadcountValidator()
