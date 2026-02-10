import sys
import os

# --- [경로 설정] 도커/로컬 환경 자동 감지 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists('/app/app'):
    project_root = '/app' # Docker 환경
else:
    project_root = os.path.abspath(os.path.join(current_dir, '..')) # 로컬 환경

if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ------------------------------------------

from app.database import SessionLocal
from app.models.objects.product_line import ProductLine
from app.models.objects.hardware_blueprint import HardwareBlueprint
from app.models.objects.system_unit import SystemUnit, UnitStatus
from app.models.objects.supported_component import SupportedComponent, ControlType

def seed():
    db = SessionLocal()
    try:
        print("🌱 [통합 시딩] 인프라 및 필수 부품 기초 공사 시작...")

        # ---------------------------------------------------------
        # 1. 필수 부품 (SupportedComponent) 등록 - "SYSTEM"
        # ---------------------------------------------------------
        target_model = "SYSTEM"
        comp = db.query(SupportedComponent).filter(SupportedComponent.model_name == target_model).first()
        
        if not comp:
            comp = SupportedComponent(
                model_name=target_model,
                display_name="System Main Controller",
                manufacturer="Ares4_Core",
                category="SYSTEM_CONTROLLER",
                description="Core device metrics (CPU, RAM, Temp)",
                control_type=ControlType.NONE,
                min_value=0.0,
                max_value=100.0,
                unit="%",
                telemetry_category="system_stats",
                active_low=False
            )
            db.add(comp)
            db.flush() # ID 생성을 위해 flush
            print(f"   ✅ 부품 등록 완료: {target_model}")
        else:
            print(f"   ♻️ 부품 이미 존재: {target_model}")

        # ---------------------------------------------------------
        # 2. 제품군 (Product Line)
        # ---------------------------------------------------------
        pl = db.query(ProductLine).filter(ProductLine.name == "Ares4-Default").first()
        if not pl:
            pl = ProductLine(name="Ares4-Default", description="Default Line")
            db.add(pl)
            db.flush()
            print(f"   ✅ 제품군 생성 완료: {pl.name}")
        else:
            print(f"   ♻️ 제품군 이미 존재: {pl.name}")
        
        # ---------------------------------------------------------
        # 3. 설계도 (Blueprint)
        # ---------------------------------------------------------
        bp_name = "RPi-Standard"
        bp = db.query(HardwareBlueprint).filter(HardwareBlueprint.blueprint_name == bp_name).first()
        
        if not bp:
            bp = HardwareBlueprint(
                blueprint_name=bp_name, 
                blueprint_version="v1.0",
                product_line_id=pl.id,
                specs={"cpu": "bcm2711", "ram": "4gb"},
                description="Standard Raspberry Pi Model"
            )
            db.add(bp)
            db.flush()
            print(f"   ✅ 청사진 생성 완료: {bp.blueprint_name}")
        else:
            print(f"   ♻️ 청사진 이미 존재: {bp.blueprint_name}")
        
        # ---------------------------------------------------------
        # 4. 유닛 (System Unit - 빈 방)
        # ---------------------------------------------------------
        unit_name = "Yoonpyo-Lab-Unit"
        unit = db.query(SystemUnit).filter(SystemUnit.name == unit_name).first()
        if not unit:
            unit = SystemUnit(
                name=unit_name,
                product_line_id=pl.id,
                user_id=None, # 아직 주인 없음
                status=UnitStatus.PROVISIONING,
                description="Test Lab Unit"
            )
            db.add(unit)
            print(f"   ✅ 유닛 생성 완료: {unit.name}")
        else:
            print(f"   ♻️ 유닛 이미 존재: {unit.name}")
        
        # --- 최종 저장 ---
        db.commit()
        print("🎉 모든 기초 데이터 시딩이 완료되었습니다.")

    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()