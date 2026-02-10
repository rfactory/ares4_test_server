import logging
import asyncio
from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse 
from typing import Optional

from app.core.config import get_settings
from app.database import SessionLocal
from app.core.redis_client import get_redis_client 
from app.core.exceptions import ForbiddenError, AppLogicError

# --- Domain Modules ---
from app.domains.application.mqtt.orchestrator import MqttLifecycleOrchestrator
from app.domains.inter_domain.governance.governance_query_provider import governance_query_provider
from app.domains.inter_domain.governance.governance_command_provider import governance_command_provider

# --- Routers ---
from app.api.v1.api import api_router
# [NEW] 방금 만든 업로드용 라우터
from app.domains.application.upload.endpoints import router as upload_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_mqtt_orchestrator: Optional[MqttLifecycleOrchestrator] = None
_governance_task: Optional[asyncio.Task] = None
_background_tasks = set()

async def _periodic_governance_check():
    """Periodically checks governance status, like emergency mode."""
    while True:
        try:
            with SessionLocal() as db:
                prime_admin_count = governance_query_provider.get_prime_admin_count(db)
                governance_command_provider.update_emergency_mode(prime_admin_count=prime_admin_count)
        except Exception as e:
            logger.error(f"Error during periodic governance check: {e}")
        await asyncio.sleep(600) # 10 minutes

@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버의 시작과 종료 시 모든 핵심 인프라를 지휘합니다."""
    logger.info("🚀Application starting up...")
    
    global _mqtt_orchestrator, _governance_task, _background_tasks
    
    # 1. MQTT Orchestrator 초기화 및 기동
    _mqtt_orchestrator = MqttLifecycleOrchestrator(
        settings=get_settings(),
        db_session_factory=SessionLocal
    )
    mqtt_startup_task = asyncio.create_task(_mqtt_orchestrator.startup())
    _background_tasks.add(mqtt_startup_task)
    mqtt_startup_task.add_done_callback(_background_tasks.discard)

    # 2. 주기적 거버넌스 체크 백그라운드 태스크 시작
    _governance_task = asyncio.create_task(_periodic_governance_check())
    
    logger.info("✅ All background tasks and MQTT infrastructure are operational.")
    yield # 서버가 요청을 처리하는 시점

    logger.info("🛑Application shutting down...")
    
    # 3. 자원 정리 (Graceful Shutdown)
    if _governance_task:
        _governance_task.cancel()
        logger.info("Governance task cancelled.")
        
    if _mqtt_orchestrator:
        await _mqtt_orchestrator.shutdown()
        logger.info("MQTT Orchestrator shut down successfully.")

app = FastAPI(
    title="Ares4 Server v2",
    lifespan=lifespan,
    redirect_slashes=False
)

# ForbiddenError 예외 처리기
@app.exception_handler(ForbiddenError)
async def forbidden_error_handler(request: Request, exc: ForbiddenError):
    logger.warning(f"ForbiddenError: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.message}
    )

# AppLogicError 예외 처리기
@app.exception_handler(AppLogicError)
async def app_logic_error_handler(request: Request, exc: AppLogicError):
    logger.warning(f"AppLogicError: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message}
    )

# CORS Middleware 설정
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["DPoP-Nonce", "dpop-nonce"], 
)

# 1. 기본 API 라우터 등록
app.include_router(api_router, prefix="/api/v1")

# [NEW] 2. 이미지 업로드 라우터 등록 (별도 태그로 관리)
# 최종 주소: /api/v1/upload/image
app.include_router(upload_router, prefix="/api/v1/upload", tags=["Upload"])


@app.get("/")
async def read_root():
    return {"message": "Welcome to Ares4 Server v2"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/health/mqtt", status_code=status.HTTP_200_OK)
async def mqtt_health_check():
    global _mqtt_orchestrator
    if _mqtt_orchestrator and _mqtt_orchestrator.is_publisher_connected():
        return {"status": "mqtt_connected"}
    else:
        return {"status": "mqtt_disconnected"}, status.HTTP_503_SERVICE_UNAVAILABLE