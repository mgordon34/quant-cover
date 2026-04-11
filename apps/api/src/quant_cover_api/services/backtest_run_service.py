from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from quant_cover_api.db.models.backtest_run import BacktestRun
from quant_cover_api.db.models.strategy import Strategy
from quant_cover_api.db.models.user import User


class BacktestRunService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_backtest_runs(self, user_id: int) -> list[BacktestRun]:
        self._get_user(user_id)
        statement = select(BacktestRun).where(BacktestRun.user_id == user_id).order_by(BacktestRun.created_at.desc())
        return list(self.session.scalars(statement))

    def create_backtest_run(
        self,
        *,
        user_id: int,
        strategy_id: int,
        dataset_version: str | None,
        parameters: dict[str, Any],
    ) -> BacktestRun:
        self._get_user(user_id)
        strategy = self._get_strategy(strategy_id)

        if strategy.user_id != user_id:
            raise HTTPException(status_code=400, detail="Strategy does not belong to user")

        run = BacktestRun(
            user_id=user_id,
            strategy_id=strategy_id,
            status="queued",
            dataset_version=dataset_version,
            parameters=parameters,
        )
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def get_backtest_run(self, run_id: int) -> BacktestRun:
        run = self.session.get(BacktestRun, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Backtest run not found")
        return run

    def _get_user(self, user_id: int) -> User:
        user = self.session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def _get_strategy(self, strategy_id: int) -> Strategy:
        strategy = self.session.get(Strategy, strategy_id)
        if strategy is None:
            raise HTTPException(status_code=404, detail="Strategy not found")
        return strategy
