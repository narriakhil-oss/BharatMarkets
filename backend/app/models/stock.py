"""Stock database model."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.exchange import Exchange
    from app.models.price import OHLCVDaily, OHLCVIntraday, StockSnapshot
    from app.models.fundamental import Fundamental
    from app.models.corporate_action import CorporateAction
    from app.models.index_model import IndexConstituent


class Stock(BaseModel):
    """Represents a listed equity security."""

    __tablename__ = "stocks"

    symbol: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    exchange_id: Mapped[int] = mapped_column(ForeignKey("exchanges.id"), nullable=False, index=True)
    isin: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True, nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    lot_size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tick_size: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.05"),
        nullable=False,
    )
    circuit_limit_pct: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    listed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    exchange: Mapped["Exchange"] = relationship("Exchange", back_populates="stocks", lazy="raise")
    snapshot: Mapped[Optional["StockSnapshot"]] = relationship(
        "StockSnapshot",
        back_populates="stock",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="raise",
    )
    fundamental: Mapped[Optional["Fundamental"]] = relationship(
        "Fundamental",
        back_populates="stock",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="raise",
    )
    daily_prices: Mapped[List["OHLCVDaily"]] = relationship(
        "OHLCVDaily",
        back_populates="stock",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    intraday_prices: Mapped[List["OHLCVIntraday"]] = relationship(
        "OHLCVIntraday",
        back_populates="stock",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    corporate_actions: Mapped[List["CorporateAction"]] = relationship(
        "CorporateAction",
        back_populates="stock",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    index_constituents: Mapped[List["IndexConstituent"]] = relationship(
        "IndexConstituent",
        back_populates="stock",
        cascade="all, delete-orphan",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"<Stock(symbol={self.symbol}, name={self.name})>"
