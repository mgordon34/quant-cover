from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quant_cover_api.db.base import Base
from quant_cover_api.db.models.timestamps import TimestampMixin


class Game(TimestampMixin, Base):
    __tablename__ = "games"
    __table_args__ = (
        CheckConstraint("home_team_id <> away_team_id", name="ck_games_distinct_teams"),
        CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'postponed', 'cancelled')",
            name="ck_games_status",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    league_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("leagues.id", ondelete="CASCADE"), index=True)
    season: Mapped[str | None] = mapped_column(String(32), nullable=True)
    season_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    game_date: Mapped[date] = mapped_column(Date)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    home_team_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    away_team_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_game_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    league = relationship("League", back_populates="games")
    home_team = relationship("Team", back_populates="home_games", foreign_keys=[home_team_id])
    away_team = relationship("Team", back_populates="away_games", foreign_keys=[away_team_id])
    player_game_stats = relationship("PlayerGameStat", back_populates="game", cascade="all, delete-orphan")
