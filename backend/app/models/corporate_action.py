"""Corporate action database model."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.stock import Stock


class CorporateAction(BaseModel):
    """Corporate actions including dividends, stock splits, bonuses, and rights issues."""

    __tablename__ = "corporate_actions"

    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)  # SPLIT, BONUS, DIVIDEND, RIGHTS
    ex_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    record_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ratio_from: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ratio_to: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    stock: Mapped["Stock"] = relationship("Stock", back_populates="corporate_actions", lazy="raise")

    def __repr__(self) -> str:
        return f"<CorporateAction(stock_id={self.stock_id}, type={self.action_type}, ex_date={self.ex_date})>"
