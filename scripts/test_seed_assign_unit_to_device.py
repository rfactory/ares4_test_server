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
from app.models.objects.system_unit import SystemUnit, UnitStatus
from app.models.objects.hardware_blueprint import HardwareBlueprint

def deploy():
    db = SessionLocal()
    try:
        print("🚀 3단계: 유닛 배치 및 활성화 중...")

        user_id = 2
        device_id = 1
        
        # 1. 유닛과 청사진 찾기
        unit = db.query(SystemUnit).filter(SystemUnit.name == "Yoonpyo-Lab-Unit").first()
        bp = db.query(HardwareBlueprint).filter(HardwareBlueprint.blueprint_name == "RPi-Standard").first()

        if not unit or not bp:
            print("❌ 유닛이나 청사진이 없습니다. 1단계 스크립트를 먼저 실행하세요.")
            return

        # 2. 유닛 소유권 확정 (입주)
        unit.user_id = user_id
        unit.status = UnitStatus.ACTIVE
        print(f"   ✅ 유닛 활성화: {unit.name} (Owner: User {user_id})")

        # 3. 기기 배치 (핵심)
        device = db.query(Device).get(device_id)
        device.system_unit_id = unit.id
        device.hardware_blueprint_id = bp.id # 이제 청사진 매핑!
        device.status = DeviceStatusEnum.ONLINE # 최종 활성화
        
        db.commit()
        print(f"🎉 모든 설정 완료! 기기({device.cpu_serial})가 ONLINE 상태입니다.")

    except Exception as e:
        db.rollback(); print(f"❌ 오류: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    deploy()