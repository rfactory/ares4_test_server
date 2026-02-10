import json
import logging
from typing import List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status

# 프로젝트의 공통 의존성 (dependencies.py) 임포트
from app.dependencies import get_db
from app.domains.action_authorization.policies.batch_ingestion.batch_ingestion_policy import batch_ingestion_policy
from app.domains.inter_domain.batch_tracker.batch_status_query_provider import batch_status_query_provider

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def ingest_batch_data(
    *,
    db: Session = Depends(get_db),
    device_uuid: str = Form(...),
    telemetry_json: str = Form(...), 
    images: List[UploadFile] = File(...)
):
    """
    [Ares Aegis] 배치 데이터 통합 입국 게이트웨이
    - 텔레메트리 벌크 저장과 이미지 비동기 처리를 지휘관(Policy)에게 위임합니다.
    """
    try:
        # 1. 텔레메트리 파싱
        try:
            telemetry_data = json.loads(telemetry_json)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid telemetry JSON format."
            )

        # 2. 지휘관(Policy) 가동
        # 장부 개설, 텔레메트리 저장, 이미지 큐 투척을 한꺼번에 수행합니다.
        success, message, result = await batch_ingestion_policy.handle_batch(
            db=db,
            device_uuid=device_uuid,
            telemetry_data=telemetry_data,
            image_files=images
        )
        
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        return {
            "status": "accepted",
            "batch_id": result.get("batch_id"),
            "summary": {
                "telemetry_count": result.get("telemetry_processed"),
                "images_queued": result.get("images_queued")
            }
        }

    except Exception as e:
        logger.error(f"❌ [Ingestion API Error] {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")

@router.get("/batch/{batch_id}/status")
def get_batch_status(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """배치 작업의 현재 진행률 및 상태를 확인합니다."""
    progress = batch_status_query_provider.get_ingestion_progress(db, batch_id=batch_id)
    if "error" in progress:
        raise HTTPException(status_code=404, detail="Batch tracking information not found.")
    return progress

@router.get("/batch/{batch_id}/purge-check")
def check_purge_permission(
    batch_id: str,
    db: Session = Depends(get_db) # deps.get_db 오타 수정 완료
):
    """기기가 원본 데이터를 삭제(Purge)해도 되는지 최종 판결을 내립니다."""
    allowed = batch_status_query_provider.check_purge_permission(db, batch_id=batch_id)
    return {
        "batch_id": batch_id,
        "purge_allowed": allowed,
        "instruction": "DELETE_ORIGINAL" if allowed else "KEEP_ORIGINAL"
    }