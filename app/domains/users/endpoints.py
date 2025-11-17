from fastapi import APIRouter
from . import endpoints_auth
from . import endpoints_user

router = APIRouter()

router.include_router(endpoints_auth.router, tags=["auth"])
router.include_router(endpoints_user.router, tags=["users"])
