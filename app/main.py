import logging
from fastapi import FastAPI, status
from contextlib import asynccontextmanager
from app.api.v1.api import api_router

from app.core.config import get_settings
from app.database import SessionLocal
from app.domains.application.mqtt.orchestrator import MqttLifecycleOrchestrator
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_mqtt_orchestrator: Optional[MqttLifecycleOrchestrator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    
    global _mqtt_orchestrator
    _mqtt_orchestrator = MqttLifecycleOrchestrator(
        settings=get_settings(),
        db_session_factory=SessionLocal
    )
    await _mqtt_orchestrator.startup()

    yield

    logger.info("Application shutting down...")
    if _mqtt_orchestrator:
        await _mqtt_orchestrator.shutdown()

app = FastAPI(
    title="Ares4 Server v2",
    lifespan=lifespan
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
