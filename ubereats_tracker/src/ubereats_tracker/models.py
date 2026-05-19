"""SQLAlchemy ORM models.

Money is stored in integer minor units (cents) to avoid float drift.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    cuisine: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    orders: Mapped[List["Order"]] = relationship(back_populates="restaurant")

    def __repr__(self) -> str:
        return f"Restaurant(id={self.id!r}, name={self.name!r})"


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("external_id", name="uq_orders_external_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(64), index=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    ordered_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    subtotal_cents: Mapped[int] = mapped_column(Integer, default=0)
    tax_cents: Mapped[int] = mapped_column(Integer, default=0)
    delivery_fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    service_fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    tip_cents: Mapped[int] = mapped_column(Integer, default=0)
    discount_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_cents: Mapped[int] = mapped_column(Integer, default=0)

    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(20), default="delivered")
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    restaurant: Mapped[Restaurant] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    @property
    def total_dollars(self) -> float:
        return self.total_cents / 100

    @property
    def tip_pct(self) -> float:
        if self.subtotal_cents <= 0:
            return 0.0
        return self.tip_cents / self.subtotal_cents * 100

    def __repr__(self) -> str:
        return (
            f"Order(id={self.id!r}, external_id={self.external_id!r}, "
            f"total_cents={self.total_cents!r})"
        )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    name: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_price_cents: Mapped[int] = mapped_column(Integer, default=0)

    order: Mapped[Order] = relationship(back_populates="items")
