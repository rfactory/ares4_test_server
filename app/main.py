from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from app.api.v1.api import api_router
from app.domains.mqtt.client import connect_mqtt_background, disconnect_mqtt
from app.domains.emqx_auth.endpoints import router as emqx_router  # 추가

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    print("Creating MQTT connection in the background...")
    asyncio.create_task(connect_mqtt_background())
    yield
    # On shutdown
    print("Disconnecting from MQTT broker...")
    disconnect_mqtt()

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
