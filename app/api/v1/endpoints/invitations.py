from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user
from app.models.objects.user import User

router = APIRouter()

class InvitationCreate(BaseModel):
    user_id_to_invite: int
    role_id_to_assign: int

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_invitation(
    *, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    invitation_in: InvitationCreate
):
    """
    관리자가 사용자를 특정 역할로 초대합니다.
    """
    # TODO: create_invitation_policy_provider.execute() 호출 구현
    return {"message": "Invitation sent successfully."}
