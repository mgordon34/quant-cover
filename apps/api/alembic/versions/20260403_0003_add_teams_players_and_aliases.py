"""add teams players and aliases

Revision ID: 20260403_0003
Revises: 20260403_0002
Create Date: 2026-04-03 00:20:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260403_0003"
down_revision: Union[str, None] = "20260403_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

portable_json = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("league_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("abbreviation", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_teams_league_id", "teams", ["league_id"], unique=False)
    op.create_index("ix_teams_league_id_abbreviation", "teams", ["league_id", "abbreviation"], unique=True)

    op.create_table(
        "players",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("league_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("stathead_player_id", sa.String(length=64), nullable=True),
        sa.Column("primary_position", sa.String(length=32), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("metadata", portable_json, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_players_league_id", "players", ["league_id"], unique=False)
    op.create_index("ix_players_league_id_full_name", "players", ["league_id", "full_name"], unique=False)
    op.create_index(
        "ix_players_league_id_stathead_player_id",
        "players",
        ["league_id", "stathead_player_id"],
        unique=True,
        postgresql_where=sa.text("stathead_player_id IS NOT NULL"),
    )

    op.create_table(
        "player_aliases",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("player_id", sa.BigInteger(), nullable=False),
        sa.Column("stathead_source", sa.String(length=64), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("normalized_alias", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_player_aliases_player_id", "player_aliases", ["player_id"], unique=False)
    op.create_index("ix_player_aliases_normalized_alias", "player_aliases", ["normalized_alias"], unique=False)
    op.create_index(
        "ix_player_aliases_stathead_source_normalized_alias",
        "player_aliases",
        ["stathead_source", "normalized_alias"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_player_aliases_stathead_source_normalized_alias", table_name="player_aliases")
    op.drop_index("ix_player_aliases_normalized_alias", table_name="player_aliases")
    op.drop_index("ix_player_aliases_player_id", table_name="player_aliases")
    op.drop_table("player_aliases")
    op.drop_index("ix_players_league_id_stathead_player_id", table_name="players")
    op.drop_index("ix_players_league_id_full_name", table_name="players")
    op.drop_index("ix_players_league_id", table_name="players")
    op.drop_table("players")
    op.drop_index("ix_teams_league_id_abbreviation", table_name="teams")
    op.drop_index("ix_teams_league_id", table_name="teams")
    op.drop_table("teams")
