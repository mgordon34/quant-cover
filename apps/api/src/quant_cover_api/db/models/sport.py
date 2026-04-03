from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quant_cover_api.db.base import Base
from quant_cover_api.db.models.timestamps import TimestampMixin


class Sport(TimestampMixin, Base):
    __tablename__ = "sports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    stathead_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)

    leagues = relationship("League", back_populates="sport", cascade="all, delete-orphan")
