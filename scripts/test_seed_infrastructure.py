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
from app.models.objects.product_line import ProductLine
from app.models.objects.hardware_blueprint import HardwareBlueprint
from app.models.objects.system_unit import SystemUnit, UnitStatus

def seed():
    db = SessionLocal()
    try:
        print("🌱 1단계: 인프라 기초 공사 중...")

        # 1. Product Line
        pl = db.query(ProductLine).filter(ProductLine.name == "Ares4-Default").first()
        if not pl:
            pl = ProductLine(name="Ares4-Default", description="Default Line")
            db.add(pl); db.flush()
        
        # 2. Blueprint (수정됨: specifications -> specs)
        bp_name = "RPi-Standard"
        bp = db.query(HardwareBlueprint).filter(HardwareBlueprint.blueprint_name == bp_name).first()
        
        if not bp:
            bp = HardwareBlueprint(
                blueprint_name=bp_name, 
                blueprint_version="v1.0",
                product_line_id=pl.id,
                # [수정] DB 컬럼명에 맞춰 specs로 변경
                specs={"cpu": "bcm2711", "ram": "4gb"},
                description="Standard Raspberry Pi Model"
            )
            db.add(bp); db.flush()
            print(f"   ✅ 청사진 생성 완료: {bp.blueprint_name}")
        else:
            print(f"   ♻️ 청사진 이미 존재: {bp.blueprint_name}")
        
        # 3. Unit (빈 방)
        unit = db.query(SystemUnit).filter(SystemUnit.name == "Yoonpyo-Lab-Unit").first()
        if not unit:
            unit = SystemUnit(
                name="Yoonpyo-Lab-Unit",
                product_line_id=pl.id,
                user_id=None, # 아직 주인 없음
                status=UnitStatus.PROVISIONING,
                description="Test Lab Unit"
            )
            db.add(unit)
            print(f"   ✅ 유닛 생성 완료: {unit.name}")
        else:
            print(f"   ♻️ 유닛 이미 존재: {unit.name}")
        
        db.commit()

    except Exception as e:
        db.rollback(); print(f"❌ 오류: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()