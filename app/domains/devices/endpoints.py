from fastapi import APIRouter
from . import endpoints_device_management
from . import endpoints_component_management

router = APIRouter()

router.include_router(endpoints_device_management.router, tags=["device_management"])
router.include_router(endpoints_component_management.router, prefix="/components", tags=["component_management"])
