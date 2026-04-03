from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quant_cover_api.db.base import Base
from quant_cover_api.db.models.timestamps import TimestampMixin


class PlayerGameStat(TimestampMixin, Base):
    __tablename__ = "player_game_stats"
    __table_args__ = (UniqueConstraint("player_id", "game_id", name="uq_player_game_stats_player_id_game_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("players.id", ondelete="CASCADE"), index=True)
    game_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("games.id", ondelete="CASCADE"), index=True)
    team_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    opponent_team_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    started: Mapped[bool | None] = mapped_column(nullable=True)
    minutes: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rebounds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assists: Mapped[int | None] = mapped_column(Integer, nullable=True)
    threes_made: Mapped[int | None] = mapped_column(Integer, nullable=True)
    steals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blocks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    turnovers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    offensive_rating: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    defensive_rating: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    stathead_row_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)

    player = relationship("Player", back_populates="player_game_stats")
    game = relationship("Game", back_populates="player_game_stats")
    team = relationship("Team", back_populates="player_game_stats", foreign_keys=[team_id])
    opponent_team = relationship("Team", back_populates="opponent_player_game_stats", foreign_keys=[opponent_team_id])
