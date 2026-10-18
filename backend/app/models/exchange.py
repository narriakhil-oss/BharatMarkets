"""Exchange database model representing stock exchanges (e.g. NSE, BSE)."""

from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.stock import Stock
    from app.models.index_model import Index


class Exchange(BaseModel):
    """Represents a stock exchange platform."""

    __tablename__ = "exchanges"

    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    stocks: Mapped[List["Stock"]] = relationship(
        "Stock",
        back_populates="exchange",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    indices: Mapped[List["Index"]] = relationship(
        "Index",
        back_populates="exchange",
        cascade="all, delete-orphan",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"<Exchange(code={self.code}, name={self.name})>"
