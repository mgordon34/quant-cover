from fastapi import APIRouter
from fastapi import Depends
from fastapi import Path
from sqlalchemy.orm import Session

from quant_cover_api.api.dependencies import get_db
from quant_cover_api.api.schemas.user import UserCreate
from quant_cover_api.api.schemas.user import UserResponse
from quant_cover_api.services.user_service import UserService


router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    payload: UserCreate,
    session: Session = Depends(get_db),
) -> UserResponse:
    service = UserService(session)
    user = service.create_user(email=payload.email, display_name=payload.display_name)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int = Path(gt=0),
    session: Session = Depends(get_db),
) -> UserResponse:
    service = UserService(session)
    user = service.get_user(user_id=user_id)
    return UserResponse.model_validate(user)
