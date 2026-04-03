"""add sports and leagues

Revision ID: 20260403_0002
Revises: 20260403_0001
Create Date: 2026-04-03 00:10:00

"""

from typing import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260403_0002"
down_revision: Union[str, None] = "20260403_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sports",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("stathead_domain", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sports_key", "sports", ["key"], unique=True)

    op.create_table(
        "leagues",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("sport_id", sa.BigInteger(), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("stathead_league_key", sa.String(length=64), nullable=True),
        sa.Column("odds_api_sport_key", sa.String(length=128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_leagues_key", "leagues", ["key"], unique=True)
    op.create_index("ix_leagues_sport_id", "leagues", ["sport_id"], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO sports (key, name, stathead_domain, created_at, updated_at)
            VALUES ('basketball', 'Basketball', 'stathead.com', NOW(), NOW())
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO leagues (sport_id, key, name, stathead_league_key, odds_api_sport_key, is_active, created_at, updated_at)
            SELECT id, 'nba', 'NBA', 'basketball', NULL, true, NOW(), NOW()
            FROM sports
            WHERE key = 'basketball'
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_leagues_sport_id", table_name="leagues")
    op.drop_index("ix_leagues_key", table_name="leagues")
    op.drop_table("leagues")
    op.drop_index("ix_sports_key", table_name="sports")
    op.drop_table("sports")
