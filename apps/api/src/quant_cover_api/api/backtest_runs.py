from fastapi import APIRouter
from fastapi import Depends
from fastapi import Path
from fastapi import Query
from sqlalchemy.orm import Session

from quant_cover_api.api.dependencies import get_db
from quant_cover_api.api.schemas.backtest_run import BacktestRunCreate
from quant_cover_api.api.schemas.backtest_run import BacktestRunResponse
from quant_cover_api.services.backtest_run_service import BacktestRunService


router = APIRouter(prefix="/backtest-runs", tags=["backtest-runs"])


@router.get("", response_model=list[BacktestRunResponse])
def list_backtest_runs(
    user_id: int = Query(gt=0),
    session: Session = Depends(get_db),
) -> list[BacktestRunResponse]:
    service = BacktestRunService(session)
    runs = service.list_backtest_runs(user_id=user_id)
    return [BacktestRunResponse.model_validate(run) for run in runs]


@router.post("", response_model=BacktestRunResponse, status_code=201)
def create_backtest_run(
    payload: BacktestRunCreate,
    session: Session = Depends(get_db),
) -> BacktestRunResponse:
    service = BacktestRunService(session)
    run = service.create_backtest_run(
        user_id=payload.user_id,
        strategy_id=payload.strategy_id,
        dataset_version=payload.dataset_version,
        parameters=payload.parameters,
    )
    return BacktestRunResponse.model_validate(run)


@router.get("/{run_id}", response_model=BacktestRunResponse)
def get_backtest_run(
    run_id: int = Path(gt=0),
    session: Session = Depends(get_db),
) -> BacktestRunResponse:
    service = BacktestRunService(session)
    run = service.get_backtest_run(run_id=run_id)
    return BacktestRunResponse.model_validate(run)
