from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.domains.accounts.schemas import User, UserCreate
from app.domains.accounts.crud import user_crud
from app.models.objects.user import User as DBUser

router = APIRouter()

@router.post("/", response_model=User, summary="Create a new user")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user_by_email = user_crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user_by_username = user_crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    return user_crud.create_user(db=db, user=user)

@router.get("/{username}", response_model=User, summary="Get a user by username")
def read_user(username: str, db: Session = Depends(get_db)):
    db_user = user_crud.get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/me/toggle-2fa", response_model=User, summary="Toggle 2FA for the current user")
async def toggle_two_factor_authentication(
    db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)
):
    # Re-fetch the user in the current session to avoid session conflicts
    user_in_db = db.query(DBUser).filter(DBUser.id == current_user.id).first()
    if not user_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_in_db.is_two_factor_enabled = not user_in_db.is_two_factor_enabled
    db.commit()
    db.refresh(user_in_db)
    return user_in_db
