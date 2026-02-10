import logging
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db

# [수정됨] 다니엘님의 실제 파일 경로에 맞춰 import 경로를 수정했습니다.
from app.domains.application.ingestion.ingestion_policy import ingestion_policy


logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    device_uuid: str = Form(...),
    snapshot_id: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        file_bytes = await file.read()
        payload = {"snapshot_id": snapshot_id, "filename": file.filename}

        # [Ares Aegis] 정책 호출. commit 로직은 ImageIngestionPolicy 내부로 이미 들어갔습니다.
        success, error_msg = ingestion_policy.handle_image_upload(
            db=db,
            device_uuid_str=device_uuid,
            payload=payload,
            file_data=file_bytes
        )

        if not success:
            raise HTTPException(status_code=400, detail=error_msg)

        return {"status": "success"}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Upload Endpoint Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")