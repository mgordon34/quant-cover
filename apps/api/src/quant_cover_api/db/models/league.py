from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quant_cover_api.db.base import Base
from quant_cover_api.db.models.timestamps import TimestampMixin


class League(TimestampMixin, Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sport_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sports.id", ondelete="CASCADE"), index=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    stathead_league_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    odds_api_sport_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    sport = relationship("Sport", back_populates="leagues")
    teams = relationship("Team", back_populates="league", cascade="all, delete-orphan")
    players = relationship("Player", back_populates="league", cascade="all, delete-orphan")
    games = relationship("Game", back_populates="league", cascade="all, delete-orphan")
