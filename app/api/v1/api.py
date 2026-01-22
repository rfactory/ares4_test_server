from fastapi import APIRouter
from app.domains.application.emqx_webhooks import endpoints as emqx_webhook_endpoints
from app.api.v1.endpoints import internal, organizations, common, organization_types, roles, permissions, users, requests, auth, system, abac # abac 임포트 추가

api_router = APIRouter(redirect_slashes=False)

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(emqx_webhook_endpoints.router, prefix="/mqtt", tags=["EMQX Webhooks"])
api_router.include_router(internal.router, prefix="/internal", tags=["Internal"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(organization_types.router, prefix="/organization-types", tags=["Organization Types"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(requests.router, prefix="/requests", tags=["Requests"])
api_router.include_router(system.router, prefix="/system", tags=["System"])
api_router.include_router(abac.router, prefix="/abac", tags=["ABAC"]) # abac 라우터 추가
api_router.include_router(common.router, tags=["Common"])