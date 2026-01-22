#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from fastapi import Request # Request 임포트

from app.domains.action_authorization.policies.authentication.initiate_registration_policy import initiate_registration_policy
from app.domains.action_authorization.policies.authentication.complete_registration_policy import complete_registration_policy
from app.domains.inter_domain.user_identity.schemas.user_identity_command import UserCreate, CompleteRegistration
from app.domains.inter_domain.user_identity.schemas.user_identity_query import UserWithToken

class RegistrationPolicyProvider:
    """
    Registration Policy들에 대한 공개 인터페이스입니다.
    """
    async def initiate_registration(self, db: Session, *, user_in: UserCreate) -> dict:
        return await initiate_registration_policy.execute(db, user_in=user_in)

    async def complete_registration(self, db: Session, *, email: str, verification_code: str, request: Request) -> UserWithToken:
        return await complete_registration_policy.execute(db, email=email, verification_code=verification_code, request=request)

registration_policy_provider = RegistrationPolicyProvider()
