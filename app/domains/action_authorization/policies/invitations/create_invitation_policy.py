from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.api.v1.endpoints.invitations import InvitationCreate

class CreateInvitationPolicy:
    def execute(self, db: Session, *, invitation_in: InvitationCreate, actor_user: User):
        """
        사용자 초대 워크플로우를 조율합니다.
        """
        # TODO: 1. 초대 대상 사용자 및 역할 조회
        # TODO: 2. 초대 권한 검증 (Validator 호출)
        # TODO: 3. 초대 객체 생성 및 인증 코드 발급 (Service 호출)
        # TODO: 4. 이메일 발송 (Provider 호출)
        # TODO: 5. 트랜잭션 커밋
        pass

create_invitation_policy = CreateInvitationPolicy()
