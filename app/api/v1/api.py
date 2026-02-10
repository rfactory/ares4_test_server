from fastapi import APIRouter
from app.domains.application.emqx_webhooks import endpoints as emqx_webhook_endpoints
from app.api.v1.endpoints import abac, admin, auth, common, factory, ingestion, internal, organization_types, organizations, permissions, requests, roles, system, users
api_router = APIRouter(redirect_slashes=False)


api_router.include_router(emqx_webhook_endpoints.router, prefix="/mqtt", tags=["EMQX Webhooks"])

api_router.include_router(abac.router, prefix="/abac", tags=["ABAC"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(common.router, tags=["Common"])
api_router.include_router(factory.router, prefix="/factory", tags=["Factory"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Batch Ingestion"])
api_router.include_router(internal.router, prefix="/internal", tags=["Internal"])
api_router.include_router(organization_types.router, prefix="/organization-types", tags=["Organization Types"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])
api_router.include_router(requests.router, prefix="/requests", tags=["Requests"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(system.router, prefix="/system", tags=["System"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
