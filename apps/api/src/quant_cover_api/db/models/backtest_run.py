from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quant_cover_api.db.base import Base
from quant_cover_api.db.models.timestamps import TimestampMixin
from quant_cover_api.db.types import portable_bigint, portable_json


class BacktestRun(TimestampMixin, Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(portable_bigint, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(portable_bigint, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    strategy_id: Mapped[int] = mapped_column(portable_bigint, ForeignKey("strategies.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="queued")
    dataset_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(portable_json, default=dict)
    result_summary: Mapped[dict[str, Any] | None] = mapped_column(portable_json, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="backtest_runs")
    strategy = relationship("Strategy", back_populates="backtest_runs")
