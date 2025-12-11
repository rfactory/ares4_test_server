# app/core/id_generator.py
import uuid

def generate_device_id() -> uuid.UUID:
    """
    장치를 위한 새로운 고유 식별자(ID)를 생성합니다.
    현재 전략은 UUIDv4를 사용합니다.
    향후 ID 생성 정책이 변경될 경우, 이 함수만 수정하면 됩니다.
    """
    return uuid.uuid4()
