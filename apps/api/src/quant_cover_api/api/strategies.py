from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from quant_cover_api.api.dependencies import get_db
from quant_cover_api.api.schemas.strategy import StrategyCreate, StrategyResponse
from quant_cover_api.services.strategy_service import StrategyService

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("", response_model=list[StrategyResponse])
def list_strategies(
    user_id: int = Query(gt=0),
    session: Session = Depends(get_db),
) -> list[StrategyResponse]:
    service = StrategyService(session)
    strategies = service.list_strategies(user_id=user_id)
    return [StrategyResponse.model_validate(strategy) for strategy in strategies]


@router.post("", response_model=StrategyResponse, status_code=201)
def create_strategy(
    payload: StrategyCreate,
    session: Session = Depends(get_db),
) -> StrategyResponse:
    service = StrategyService(session)
    strategy = service.create_strategy(
        user_id=payload.user_id,
        name=payload.name,
        description=payload.description,
        configuration=payload.configuration,
    )
    return StrategyResponse.model_validate(strategy)
