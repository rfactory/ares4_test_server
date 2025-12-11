import os
import sys
import asyncio
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text

# Add project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.core.security import get_password_hash

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

async def create_system_user():
    """
    Ensures the system user with ID=1 exists in the database.
    This uses credentials from .env to match MQTT configuration.
    """
    db: Session = SessionLocal()
    try:
        # 1. 환경 변수에서 MQTT 계정 정보 가져오기
        mqtt_username = os.getenv("MQTT_USERNAME", "system")
        mqtt_password = os.getenv("MQTT_PASSWORD", "a_very_secure_and_unpredictable_password")
        
        print(f"Checking for system user (Target Username: {mqtt_username})...")

        # Check if user with id=1 already exists
        result = db.execute(text("SELECT id, username FROM users WHERE id = 1")).first()
        
        if result:
            print(f"System user with id=1 already exists (Username: {result.username}).")
            # [선택 사항] 만약 기존 유저 이름이 .env와 다르면 업데이트하는 로직을 넣을 수도 있지만,
            # 지금은 헷갈리지 않게 '초기화(down -v)'를 권장합니다.
            return

        print(f"System user not found. Creating user '{mqtt_username}' with ID=1...")

        # Hash the password from .env
        hashed_password = get_password_hash(mqtt_password)
        
        # Use raw SQL to insert the user
        db.execute(
            text(
                "INSERT INTO users (id, email, username, password_hash, is_active, is_staff, is_superuser, is_two_factor_enabled, last_login) "
                "VALUES (1, 'system@ares.com', :username, :password_hash, true, true, true, false, now())"
            ),
            {
                "username": mqtt_username,
                "password_hash": hashed_password
            }
        )
        db.commit()
        print(f"Successfully created system user '{mqtt_username}' with id=1.")

    except Exception as e:
        print(f"Error creating system user: {e}")
        # 오류 발생 시 롤백 (안전장치)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_system_user())