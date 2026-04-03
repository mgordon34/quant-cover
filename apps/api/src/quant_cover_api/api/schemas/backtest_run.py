from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class BacktestRunCreate(BaseModel):
    user_id: int = Field(gt=0)
    strategy_id: int = Field(gt=0)
    dataset_version: str | None = Field(default=None, max_length=64)
    parameters: dict[str, Any] = Field(default_factory=dict)


class BacktestRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    strategy_id: int
    status: str
    dataset_version: str | None
    parameters: dict[str, Any]
    result_summary: dict[str, Any] | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
