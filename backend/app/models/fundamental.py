"""Fundamental analysis database model."""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    ForeignKey,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.stock import Stock


class Fundamental(BaseModel):
    """Fundamental financial metrics and ratios for a company."""

    __tablename__ = "fundamentals"

    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), unique=True, nullable=False, index=True)
    market_cap: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    pe_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    pb_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    eps: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    roe: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    dividend_yield: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    face_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    book_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)

    # Relationships
    stock: Mapped["Stock"] = relationship("Stock", back_populates="fundamental", lazy="raise")

    def __repr__(self) -> str:
        return f"<Fundamental(stock_id={self.stock_id}, pe={self.pe_ratio}, pb={self.pb_ratio})>"
