import sys
import os

# --- [경로 설정] ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..')) 

if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ------------------------------------------

from app.database import SessionLocal
from app.models.objects.device import Device, DeviceStatusEnum
from app.models.objects.system_unit import SystemUnit, UnitStatus
from app.models.objects.hardware_blueprint import HardwareBlueprint
from app.models.objects.supported_component import SupportedComponent
from app.models.relationships.device_component_instance import DeviceComponentInstance

def deploy():
    db = SessionLocal()
    try:
        print("🚀 3단계: 유닛 배치 및 설계도 기반 부품 '자동 복제' 시작...")

        # 1. 대상 조회
        device_id = 1
        unit_name = "Yoonpyo-Lab-Unit"
        blueprint_name = "RPi-Standard"
        
        # [수정] SQLAlchemy 2.0 스타일로 변경 (Warning 해결)
        device = db.get(Device, device_id)
        unit = db.query(SystemUnit).filter(SystemUnit.name == unit_name).first()
        bp = db.query(HardwareBlueprint).filter(HardwareBlueprint.blueprint_name == blueprint_name).first()

        if not device:
            print(f"❌ 기기(ID: {device_id})가 없습니다. 부트로더를 먼저 실행하세요.")
            return
        if not unit or not bp:
            print("❌ 기초 데이터(Unit/Blueprint) 부족. 1단계를 확인하세요.")
            return

        # 2. 기기 배치 (Unit & Blueprint 할당)
        device.system_unit_id = unit.id
        device.hardware_blueprint_id = bp.id
        device.status = DeviceStatusEnum.ONLINE
        unit.status = UnitStatus.ACTIVE
        print(f"   ✅ 기기({device.cpu_serial}) -> 유닛({unit.name}) 배치 완료")

        # 3. [핵심 자동화] 설계도(Blueprint) 기반 부품 등록
        blueprint_bom = [
            {"instance_name": "main_board", "model_name": "SYSTEM"}
        ]

        for item in blueprint_bom:
            comp_type = db.query(SupportedComponent).filter(
                SupportedComponent.model_name == item["model_name"]
            ).first()

            if not comp_type:
                print(f"   ⚠️ 경고: 부품 타입 '{item['model_name']}'을 찾을 수 없습니다.")
                continue

            exists = db.query(DeviceComponentInstance).filter_by(
                device_id=device.id, 
                instance_name=item["instance_name"]
            ).first()

            if not exists:
                # [수정] 모델에 없는 'is_active' 필드 제거
                new_inst = DeviceComponentInstance(
                    device_id=device.id,
                    supported_component_id=comp_type.id,
                    instance_name=item["instance_name"]
                )
                db.add(new_inst)
                print(f"   ✅ [자동 등록] 설계도에 정의된 '{item['instance_name']}' 부품을 기기에 장착했습니다.")
            else:
                print(f"   ♻️ 부품 '{item['instance_name']}'은 이미 등록되어 있습니다.")

        db.commit()
        print(f"🎉 모든 설정 완료! 이제 MQTT 텔레메트리 전송을 시도해 보세요.")

    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    deploy()