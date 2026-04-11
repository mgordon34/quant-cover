"""add games and player game stats

Revision ID: 20260403_0004
Revises: 20260403_0003
Create Date: 2026-04-03 00:30:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260403_0004"
down_revision: Union[str, None] = "20260403_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

portable_json = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "games",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("league_id", sa.BigInteger(), nullable=False),
        sa.Column("season", sa.String(length=32), nullable=True),
        sa.Column("season_type", sa.String(length=32), nullable=True),
        sa.Column("game_date", sa.Date(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("home_team_id", sa.BigInteger(), nullable=False),
        sa.Column("away_team_id", sa.BigInteger(), nullable=False),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("source_game_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("home_team_id <> away_team_id", name="ck_games_distinct_teams"),
        sa.CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'postponed', 'cancelled')",
            name="ck_games_status",
        ),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["away_team_id"], ["teams.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_games_league_id_game_date", "games", ["league_id", "game_date"], unique=False)
    op.create_index("ix_games_home_team_id", "games", ["home_team_id"], unique=False)
    op.create_index("ix_games_away_team_id", "games", ["away_team_id"], unique=False)
    op.create_index(
        "ix_games_league_id_source_game_id",
        "games",
        ["league_id", "source_game_id"],
        unique=True,
        postgresql_where=sa.text("source_game_id IS NOT NULL"),
    )

    op.create_table(
        "player_game_stats",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("player_id", sa.BigInteger(), nullable=False),
        sa.Column("game_id", sa.BigInteger(), nullable=False),
        sa.Column("team_id", sa.BigInteger(), nullable=False),
        sa.Column("opponent_team_id", sa.BigInteger(), nullable=False),
        sa.Column("started", sa.Boolean(), nullable=True),
        sa.Column("minutes", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("points", sa.Integer(), nullable=True),
        sa.Column("rebounds", sa.Integer(), nullable=True),
        sa.Column("assists", sa.Integer(), nullable=True),
        sa.Column("threes_made", sa.Integer(), nullable=True),
        sa.Column("steals", sa.Integer(), nullable=True),
        sa.Column("blocks", sa.Integer(), nullable=True),
        sa.Column("turnovers", sa.Integer(), nullable=True),
        sa.Column("offensive_rating", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("defensive_rating", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("source_row_id", sa.String(length=64), nullable=True),
        sa.Column("metadata", portable_json, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["opponent_team_id"], ["teams.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_player_game_stats_game_id", "player_game_stats", ["game_id"], unique=False)
    op.create_index("ix_player_game_stats_team_id", "player_game_stats", ["team_id"], unique=False)
    op.create_index("ix_player_game_stats_opponent_team_id", "player_game_stats", ["opponent_team_id"], unique=False)
    op.create_index(
        "ix_player_game_stats_player_id_game_id",
        "player_game_stats",
        ["player_id", "game_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_player_game_stats_player_id_game_id", table_name="player_game_stats")
    op.drop_index("ix_player_game_stats_opponent_team_id", table_name="player_game_stats")
    op.drop_index("ix_player_game_stats_team_id", table_name="player_game_stats")
    op.drop_index("ix_player_game_stats_game_id", table_name="player_game_stats")
    op.drop_table("player_game_stats")
    op.drop_index("ix_games_league_id_source_game_id", table_name="games")
    op.drop_index("ix_games_away_team_id", table_name="games")
    op.drop_index("ix_games_home_team_id", table_name="games")
    op.drop_index("ix_games_league_id_game_date", table_name="games")
    op.drop_table("games")
