import sys
import os
import logging

# [경로 설정]
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists('/app/app'):
    project_root = '/app'
else:
    project_root = os.path.abspath(os.path.join(current_dir, '../'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.database import SessionLocal
from app.models.objects.user import User
from app.core.security import get_password_hash
from app.core.config import settings 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_password_field_name(model_class):
    """모델의 컬럼 목록을 뒤져서 비밀번호 필드명을 찾아냅니다."""
    columns = model_class.__table__.columns.keys()
    
    # 1. 우선순위 후보군
    candidates = ['hashed_password', 'password_hash', 'password', 'encrypted_password', 'pw_hash']
    for candidate in candidates:
        if candidate in columns:
            return candidate
            
    # 2. 'password'가 포함된 아무 컬럼이나 찾기
    for col in columns:
        if 'password' in col:
            return col
            
    return None

def create_system_user():
    db = SessionLocal()
    try:
        target_username = settings.MQTT_USERNAME or "ares_user"
        target_password = settings.MQTT_PASSWORD or "ares_password"

        print(f"🔧 타겟 유저: {target_username}")

        # 1. 비밀번호 필드명 자동 탐지
        pw_field = get_password_field_name(User)
        if not pw_field:
            logger.error(f"❌ User 모델에서 비밀번호 관련 컬럼을 찾을 수 없습니다! (컬럼 목록: {User.__table__.columns.keys()})")
            return
            
        logger.info(f"🔍 감지된 비밀번호 필드명: '{pw_field}'")

        # 2. DB 확인
        user = db.query(User).filter(User.username == target_username).first()

        if user:
            logger.info(f"🔄 기존 유저 '{target_username}' 업데이트 중...")
            # 동적으로 속성 설정 (setattr)
            setattr(user, pw_field, get_password_hash(target_password))
            db.commit()
            logger.info("✅ 비밀번호 업데이트 완료")
        else:
            logger.info(f"👤 유저 '{target_username}' 생성 중...")
            
            # 동적으로 딕셔너리 생성 후 언패킹 (**kwargs)
            user_data = {
                "username": target_username,
                "email": "system@ares.internal",
                "is_active": True,
                "is_superuser": True
            }
            # 비밀번호 필드 추가
            user_data[pw_field] = get_password_hash(target_password)
            
            system_user = User(**user_data)
            db.add(system_user)
            db.commit()
            logger.info("✅ 생성 완료")

    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_system_user()