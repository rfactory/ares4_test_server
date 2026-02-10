import sys
import os

# --- [경로 수정] 도커/로컬 환경 자동 감지 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists('/app/app'):
    project_root = '/app' # Docker 환경
else:
    project_root = os.path.abspath(os.path.join(current_dir, '../../')) # 로컬 환경

if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ------------------------------------------

from app.database import SessionLocal
from app.models.objects.user import User
from app.models.objects.device import Device, DeviceStatusEnum
from app.models.relationships.user_device import UserDevice

def provision():
    db = SessionLocal()
    try:
        print("🔗 2단계: 유저 소유권 연결 중...")
        
        # 확인된 데이터 기반 조회 (DB 조회 결과 반영)
        user_id = 2  # ypkim
        device_id = 1 # serial ...be2e

        # 중복 체크
        exists = db.query(UserDevice).filter_by(user_id=user_id, device_id=device_id).first()
        if not exists:
            ud = UserDevice(user_id=user_id, device_id=device_id, role="owner")
            db.add(ud)
            print(f"   ✅ User({user_id}) <-> Device({device_id}) 연결됨")
        else:
            print(f"   ♻️ 이미 연결되어 있음")
        
        # 상태 변경 (PENDING -> PROVISIONED)
        device = db.query(Device).get(device_id)
        if device.status == DeviceStatusEnum.PENDING:
            device.status = DeviceStatusEnum.PROVISIONED
            print("   ✅ 기기 상태 변경: PROVISIONED")
        else:
            print(f"   ℹ️ 기기 현재 상태: {device.status}")

        db.commit()

    except Exception as e:
        db.rollback(); print(f"❌ 오류: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    provision()