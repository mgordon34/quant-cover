from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class StrategyCreate(BaseModel):
    user_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)


class StrategyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    description: str | None
    configuration: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
