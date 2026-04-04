from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import BigInteger, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quant_cover_api.db.base import Base
from quant_cover_api.db.models.timestamps import TimestampMixin
from quant_cover_api.db.types import portable_json


class Player(TimestampMixin, Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    league_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("leagues.id", ondelete="CASCADE"), index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(255))
    stathead_player_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    primary_position: Mapped[str | None] = mapped_column(String(32), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", portable_json, nullable=True)

    league = relationship("League", back_populates="players")
    aliases = relationship("PlayerAlias", back_populates="player", cascade="all, delete-orphan")
    player_game_stats = relationship("PlayerGameStat", back_populates="player", cascade="all, delete-orphan")
