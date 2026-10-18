"""Price models for daily history, intraday intervals, and real-time market snapshots."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.stock import Stock


class OHLCVDaily(BaseModel):
    """Daily historical price bar for a stock."""

    __tablename__ = "ohlcv_daily"
    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stock_daily_date"),
    )

    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    open: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    adj_close: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    stock: Mapped["Stock"] = relationship("Stock", back_populates="daily_prices", lazy="raise")

    def __repr__(self) -> str:
        return f"<OHLCVDaily(stock_id={self.stock_id}, date={self.date}, close={self.close})>"


class OHLCVIntraday(BaseModel):
    """Intraday historical price bar for a stock at specific time intervals (e.g., 1m, 5m, 15m, 1h)."""

    __tablename__ = "ohlcv_intraday"
    __table_args__ = (
        UniqueConstraint("stock_id", "timestamp", "interval", name="uq_stock_intraday_interval"),
    )

    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    interval: Mapped[str] = mapped_column(String(5), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    stock: Mapped["Stock"] = relationship("Stock", back_populates="intraday_prices", lazy="raise")

    def __repr__(self) -> str:
        return f"<OHLCVIntraday(stock_id={self.stock_id}, ts={self.timestamp}, interval={self.interval}, close={self.close})>"


class StockSnapshot(BaseModel):
    """Latest real-time trading snapshot for a stock."""

    __tablename__ = "stock_snapshots"

    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), unique=True, nullable=False, index=True)
    ltp: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    prev_close: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    change: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    change_pct: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    high_52w: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    low_52w: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    day_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    day_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Relationships
    stock: Mapped["Stock"] = relationship("Stock", back_populates="snapshot", lazy="raise")

    def __repr__(self) -> str:
        return f"<StockSnapshot(stock_id={self.stock_id}, ltp={self.ltp}, change_pct={self.change_pct}%)>"
