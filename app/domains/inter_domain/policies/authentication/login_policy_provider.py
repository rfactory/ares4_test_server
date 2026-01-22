#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from fastapi import Request

from app.domains.action_authorization.policies.authentication.login_policy import login_policy
from app.domains.inter_domain.user_identity.schemas.user_identity_query import UserWithToken

class LoginPolicyProvider:
    """
    Login Policy에 대한 공개 인터페이스입니다.
    """
    async def login(self, db: Session, *, email: str, password: str, request: Request) -> UserWithToken:
        return await login_policy.execute(db, email=email, password=password, request=request)

login_policy_provider = LoginPolicyProvider()
