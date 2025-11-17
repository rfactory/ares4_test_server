from fastapi import APIRouter
from app.domains.data.endpoints_telemetry import router as telemetry_router

router = APIRouter()

router.include_router(telemetry_router, tags=["data"])
