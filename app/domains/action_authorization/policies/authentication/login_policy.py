from sqlalchemy.orm import Session
from pydantic import EmailStr

from app.core.exceptions import AuthenticationError

# Providers
from ....inter_domain.validators.password.password_validator_provider import password_validator_provider
from ....inter_domain.token.token_command_provider import token_command_provider


class LoginPolicy:
    def execute(self, db: Session, *, email: EmailStr, password: str) -> dict:
        """
        이메일과 비밀번호를 검증하고, 성공 시 JWT 토큰을 발급하며,
        사용자의 컨텍스트별 권한 목록을 반환합니다.
        """
        # 1. 비밀번호 검증
        is_valid, user_or_error = password_validator_provider.validate_password(
            db, email=email, password=password
        )

        if not is_valid:
            raise AuthenticationError(str(user_or_error))

        # 2. 토큰 발급
        user = user_or_error # PasswordValidator가 성공 시 user 객체를 반환하도록 리팩토링했음
        jwt_token = token_command_provider.issue_token(db, user=user)

        # 3. 사용자 권한 정보 구성
        # plans.md의 응답 예시에 맞춰 권한 구조화
        structured_permissions = {
            "system": [],
            "organizations": {}
        }

        # user.user_organization_roles를 통해 할당된 역할과 권한 정보 가져오기
        # User 모델에 user_organization_roles relationship이 정의되어 있어야 함
        for assignment in user.user_role_assignments:
            role = assignment.role
            organization_id = assignment.organization_id # 이 할당이 조직에 속하는지
            
            # 해당 역할에 부여된 모든 권한 가져오기
            permissions_for_role = [rp.permission.name for rp in role.permissions]

            if role.scope == 'SYSTEM':
                # 시스템 레벨 권한은 'system' 리스트에 추가 (중복 방지)
                for perm_name in permissions_for_role:
                    if perm_name not in structured_permissions["system"]:
                        structured_permissions["system"].append(perm_name)
            elif role.scope == 'ORGANIZATION' and organization_id is not None:
                # 조직 레벨 권한은 organization_id를 키로 하는 딕셔너리에 추가
                org_id_str = str(organization_id)
                if org_id_str not in structured_permissions["organizations"]:
                    structured_permissions["organizations"][org_id_str] = []
                for perm_name in permissions_for_role:
                    if perm_name not in structured_permissions["organizations"][org_id_str]:
                        structured_permissions["organizations"][org_id_str].append(perm_name)

        # 4. user 객체를 딕셔너리로 변환 후 권한 정보 추가
        user_dict = user.as_dict() # User 모델에 as_dict() 메소드가 필요함
        user_dict["permissions"] = structured_permissions

        return {"user": user_dict, "token": jwt_token}

login_policy = LoginPolicy()
