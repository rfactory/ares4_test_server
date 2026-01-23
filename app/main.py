import logging
import asyncio
from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.v1.api import api_router
from fastapi.responses import JSONResponse # JSONResponse 임포트 추가

from app.core.config import get_settings
from app.database import SessionLocal
from app.core.redis_client import get_redis_client # get_redis_client 임포트
from app.domains.application.mqtt.orchestrator import MqttLifecycleOrchestrator
from app.domains.inter_domain.governance.governance_query_provider import governance_query_provider
from app.domains.inter_domain.governance.governance_command_provider import governance_command_provider
from app.core.exceptions import ForbiddenError, AppLogicError # AppLogicError 임포트 추가
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_mqtt_orchestrator: Optional[MqttLifecycleOrchestrator] = None
_governance_task: Optional[asyncio.Task] = None
# [추가] 백그라운드 태스크의 가비지 컬렉션을 방지하기 위한 강한 참조 저장소
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
    # 내부적으로 인증서 획득, 연결 매니저 설정, 로테이션 감시 루프(Task)가 시작됩니다.
    _mqtt_orchestrator = MqttLifecycleOrchestrator(
        settings=get_settings(),
        db_session_factory=SessionLocal
    )
    # [수정] await 대신 create_task를 사용하고 세트에 보관하여 가비지 컬렉션을 방지합니다.
    # 이렇게 하면 FastAPI가 즉시 yield로 넘어가서 EMQX의 인증 요청을 받을 준비를 마칩니다.
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
        # shutdown 내에서 감시 루프 Task 취소 및 MQTT 연결 해제가 수행됩니다.
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

# AppLogicError 예외 처리기 (인원수 제한 등)
@app.exception_handler(AppLogicError)
async def app_logic_error_handler(request: Request, exc: AppLogicError):
    logger.warning(f"AppLogicError: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT, # 또는 400 Bad Request
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
    expose_headers=["DPoP-Nonce", "dpop-nonce"], # 대소문자 모두 노출
)

app.include_router(api_router, prefix="/api/v1")


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