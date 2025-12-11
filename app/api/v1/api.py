from fastapi import APIRouter
from app.domains.application.emqx_webhooks import endpoints as emqx_webhook_endpoints
from app.api.v1.endpoints import internal

api_router = APIRouter()

api_router.include_router(emqx_webhook_endpoints.router, prefix="/mqtt", tags=["EMQX Webhooks"])
api_router.include_router(internal.router, prefix="/internal", tags=["internal"])
