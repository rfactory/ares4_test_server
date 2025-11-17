from fastapi import APIRouter
from app.domains.users import endpoints as users_endpoints # users 라우터 임포트
from app.domains.devices import endpoints as devices_endpoints
from app.domains.data import endpoints as data_endpoints # data 라우터 임포트
from app.domains.emqx_auth import endpoints as emqx_auth_endpoints # EMQX Auth 라우터 임포트

api_router = APIRouter()

api_router.include_router(users_endpoints.router, prefix="/users", tags=["users"])
api_router.include_router(devices_endpoints.router, prefix="/devices", tags=["devices"])
api_router.include_router(data_endpoints.router, prefix="/data", tags=["data"]) # data 라우터 포함
api_router.include_router(emqx_auth_endpoints.router, prefix="/mqtt", tags=["mqtt"]) # EMQX Auth 라우터 포함
