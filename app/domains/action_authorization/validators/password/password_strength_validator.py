from typing import Tuple

def validate_password_strength_policy(password: str) -> Tuple[bool, str]:
    """
    제공된 비밀번호의 강도를 사전 정의된 기준에 따라 검증합니다.
    유효하면 (True, "Password is strong enough.")를 반환하고,
    그렇지 않으면 (False, "실패 사유.")를 반환합니다.
    이 유효성 검사기는 비밀번호 강도 정책만을 확인합니다.
    """
    min_length = 8
    # 비밀번호에 대문자가 포함되어 있는지 확인
    has_uppercase = any(char.isupper() for char in password)
    # 비밀번호에 소문자가 포함되어 있는지 확인
    has_lowercase = any(char.islower() for char in password)
    # 비밀번호에 숫자가 포함되어 있는지 확인
    has_digit = any(char.isdigit() for char in password)
    # 비밀번호에 특수 문자가 포함되어 있는지 확인
    has_special = any(not char.isalnum() for char in password)

    # 최소 길이 조건 검사
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long."
    # 대문자 포함 조건 검사
    if not has_uppercase:
        return False, "Password must contain at least one uppercase letter."
    # 소문자 포함 조건 검사
    if not has_lowercase:
        return False, "Password must contain at least one lowercase letter."
    # 숫자 포함 조건 검사
    if not has_digit:
        return False, "Password must contain at least one digit."
    # 특수 문자 포함 조건 검사
    if not has_special:
        return False, "Password must contain at least one special character."

    # 모든 조건을 만족하면 성공
    return True, "Password is strong enough."
