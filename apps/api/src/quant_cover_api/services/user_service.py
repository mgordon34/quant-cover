from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from quant_cover_api.db.models.user import User


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_user(self, *, email: str, display_name: str | None) -> User:
        normalized_email = email.strip().lower()
        existing_user = self.session.scalar(select(User).where(User.email == normalized_email))
        if existing_user is not None:
            raise HTTPException(status_code=409, detail="User already exists")

        user = User(email=normalized_email, display_name=display_name)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_user(self, *, user_id: int) -> User:
        user = self.session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
