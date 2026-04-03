from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from quant_cover_api.db.models.strategy import Strategy
from quant_cover_api.db.models.user import User


class StrategyService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_strategies(self, user_id: int) -> list[Strategy]:
        self._get_user(user_id)
        statement = select(Strategy).where(Strategy.user_id == user_id).order_by(Strategy.created_at.desc())
        return list(self.session.scalars(statement))

    def create_strategy(
        self,
        *,
        user_id: int,
        name: str,
        description: str | None,
        configuration: dict[str, Any],
    ) -> Strategy:
        self._get_user(user_id)

        strategy = Strategy(
            user_id=user_id,
            name=name,
            description=description,
            configuration=configuration,
        )
        self.session.add(strategy)
        self.session.commit()
        self.session.refresh(strategy)
        return strategy

    def _get_user(self, user_id: int) -> User:
        statement = select(User).where(User.id == user_id)
        user = self.session.scalar(statement)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
