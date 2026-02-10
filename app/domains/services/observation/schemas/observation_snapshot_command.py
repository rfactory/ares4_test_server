from pydantic import BaseModel, Field

class ObservationSnapshotCreate(BaseModel):
    id: str = Field(..., description="기기가 생성한 스냅샷 ID")
    system_unit_id: int = Field(..., description="관측된 시스템 유닛 ID")
    observation_type: str = Field("ROUTINE", description="관측 유형 (ROUTINE, EVENT 등)")

class ObservationSnapshotUpdate(BaseModel):
    # 현재는 스냅샷 수정 로직이 거의 없으나 확장성을 위해 정의
    observation_type: str