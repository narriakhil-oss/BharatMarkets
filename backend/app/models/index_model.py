"""Index and IndexConstituent models representing benchmark indices."""

from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.exchange import Exchange
    from app.models.stock import Stock


class Index(BaseModel):
    """Represents a benchmark or sectoral market index (e.g. NIFTY 50, SENSEX)."""

    __tablename__ = "indices"

    symbol: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    exchange_id: Mapped[int] = mapped_column(ForeignKey("exchanges.id"), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    exchange: Mapped["Exchange"] = relationship("Exchange", back_populates="indices", lazy="raise")
    constituents: Mapped[List["IndexConstituent"]] = relationship(
        "IndexConstituent",
        back_populates="index",
        cascade="all, delete-orphan",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"<Index(symbol={self.symbol}, display_name={self.display_name})>"


class IndexConstituent(BaseModel):
    """Constituent stocks belonging to a market index and their weights."""

    __tablename__ = "index_constituents"
    __table_args__ = (
        UniqueConstraint("index_id", "stock_id", name="uq_index_constituent"),
    )

    index_id: Mapped[int] = mapped_column(ForeignKey("indices.id"), nullable=False, index=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False, index=True)
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)

    # Relationships
    index: Mapped["Index"] = relationship("Index", back_populates="constituents", lazy="raise")
    stock: Mapped["Stock"] = relationship("Stock", back_populates="index_constituents", lazy="raise")

    def __repr__(self) -> str:
        return f"<IndexConstituent(index_id={self.index_id}, stock_id={self.stock_id}, weight={self.weight})>"
