from __future__ import annotations

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from quant_cover_api.db.base import Base
from quant_cover_api.db.models.timestamps import TimestampMixin


class Team(TimestampMixin, Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("league_id", "abbreviation", name="uq_teams_league_id_abbreviation"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    league_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("leagues.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    abbreviation: Mapped[str] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    league = relationship("League", back_populates="teams")
    home_games = relationship("Game", back_populates="home_team", foreign_keys="Game.home_team_id")
    away_games = relationship("Game", back_populates="away_team", foreign_keys="Game.away_team_id")
    player_game_stats = relationship("PlayerGameStat", back_populates="team", foreign_keys="PlayerGameStat.team_id")
    opponent_player_game_stats = relationship(
        "PlayerGameStat",
        back_populates="opponent_team",
        foreign_keys="PlayerGameStat.opponent_team_id",
    )
