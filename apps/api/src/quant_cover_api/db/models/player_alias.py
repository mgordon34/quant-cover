from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quant_cover_api.db.base import Base
from quant_cover_api.db.models.timestamps import TimestampMixin


class PlayerAlias(TimestampMixin, Base):
    __tablename__ = "player_aliases"
    __table_args__ = (UniqueConstraint("source", "normalized_alias", name="uq_player_aliases_source_normalized_alias"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("players.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(64))
    alias: Mapped[str] = mapped_column(String(255))
    normalized_alias: Mapped[str] = mapped_column(String(255), index=True)

    player = relationship("Player", back_populates="aliases")
