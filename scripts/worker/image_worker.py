import time
import json
import logging
import redis
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.domains.inter_domain.observation.observation_snapshot_command_provider import observation_snapshot_command_provider
# --- 이전에 만들었던 이미지 처리 로직들 재사용 ---
# image_ingestion_provider 내부의 실제 가공 로직만 호출합니다.
from app.domains.inter_domain.policies.image_ingestion.image_ingestion_provider import image_ingestion_policy_provider

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ImageWorker")

# Redis 연결 설정 (환경 변수에서 가져오는 것을 권장)
REDIS_URL = "redis://localhost:6379/0"
IMAGE_QUEUE_NAME = "ares4_image_jobs"

client = redis.from_url(REDIS_URL)

def process_image_job():
    """Redis 큐에서 일감을 하나 꺼내서 처리합니다."""
    # 1. 큐에서 데이터 하나 팝 (Blocking Pop: 일감이 올 때까지 대기)
    job_data = client.blpop(IMAGE_QUEUE_NAME, timeout=30)
    
    if not job_data:
        return

    _, message = job_data
    try:
        job = json.loads(message)
        device_uuid = job.get("device_uuid")
        temp_file_path = job.get("temp_file_path")
        payload = job.get("payload")
        
        logger.info(f"🚀 [Job Received] Processing image for device: {device_uuid}")

        # 2. DB 세션 생성
        db = SessionLocal()
        try:
            # 3. [핵심] 기존 이미지 정책의 가공 로직 호출
            # 이 메서드는 내부적으로 S3 업로드, 썸네일 생성, DB 기록을 수행해야 함
            success, error = image_ingestion_policy_provider.process_async_job(
                db=db,
                device_uuid=device_uuid,
                temp_file_path=temp_file_path,
                payload=payload
            )

            if success:
                logger.info(f"✅ [Job Success] Device: {device_uuid} | Path: {temp_file_path}")
                # 작업 완료 후 임시 파일 삭제 로직 추가 가능
            else:
                logger.error(f"❌ [Job Failed] Reason: {error}")
                # 실패 시 재시도 큐로 던지거나 에러 로그 기록

        finally:
            db.close()

    except Exception as e:
        logger.error(f"🔥 [Critical Error] Worker crashed during job: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("🤖 Ares4 Image Worker is standing by...")
    while True:
        process_image_job()