import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from quant_cover_api.services.backtest_run_service import BacktestRunService
from quant_cover_api.services.strategy_service import StrategyService
from quant_cover_api.services.user_service import UserService


def test_create_backtest_run_rejects_strategy_owned_by_another_user(session: Session) -> None:
    user_service = UserService(session)
    strategy_service = StrategyService(session)
    run_service = BacktestRunService(session)

    strategy_owner = user_service.create_user(email="owner@example.com", display_name=None)
    other_user = user_service.create_user(email="other@example.com", display_name=None)
    strategy = strategy_service.create_strategy(
        user_id=strategy_owner.id,
        name="Pace filter",
        description=None,
        configuration={"min_edge": 0.03},
    )

    with pytest.raises(HTTPException, match="Strategy does not belong to user") as exc_info:
        run_service.create_backtest_run(
            user_id=other_user.id,
            strategy_id=strategy.id,
            dataset_version="nba-2024",
            parameters={},
        )

    assert exc_info.value.status_code == 400
