from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quant_cover_api.db.base import Base
from quant_cover_api.db.models.timestamps import TimestampMixin
from quant_cover_api.db.types import portable_bigint


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(portable_bigint, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    strategies = relationship("Strategy", back_populates="user", cascade="all, delete-orphan")
    backtest_runs = relationship("BacktestRun", back_populates="user", cascade="all, delete-orphan")
