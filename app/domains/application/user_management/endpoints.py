from fastapi import APIRouter
from .api import endpoints_user

router = APIRouter()

router.include_router(endpoints_user.router, tags=["users"])
