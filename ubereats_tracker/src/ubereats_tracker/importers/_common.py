"""Shared types and persistence helpers used by all importers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Iterable, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Order, OrderItem, Restaurant


@dataclass
class OrderItemInput:
    name: str
    quantity: int = 1
    unit_price_cents: int = 0
    total_price_cents: int = 0


@dataclass
class OrderInput:
    external_id: str
    restaurant_name: str
    ordered_at: datetime
    subtotal_cents: int = 0
    tax_cents: int = 0
    delivery_fee_cents: int = 0
    service_fee_cents: int = 0
    tip_cents: int = 0
    discount_cents: int = 0
    total_cents: int = 0
    currency: str = "USD"
    status: str = "delivered"
    cuisine: str | None = None
    notes: str | None = None
    items: List[OrderItemInput] = field(default_factory=list)


def to_cents(value: str | float | int | Decimal | None) -> int:
    """Convert a dollar-denominated value to integer cents.

    Accepts ``"$12.34"``, ``"12.34"``, ``12.34``, ``Decimal('12.34')``, or a
    bare ``int`` of whole dollars. If you already have cents, pass them
    directly; do not route them through here.
    """
    if value is None or value == "":
        return 0
    if isinstance(value, int) and not isinstance(value, bool):
        return value * 100
    s = str(value).strip().replace("$", "").replace(",", "")
    if not s:
        return 0
    return int(round(Decimal(s) * 100))


def _get_or_create_restaurant(
    session: Session, name: str, cuisine: str | None
) -> Restaurant:
    stmt = select(Restaurant).where(Restaurant.name == name)
    existing = session.execute(stmt).scalar_one_or_none()
    if existing:
        if cuisine and not existing.cuisine:
            existing.cuisine = cuisine
        return existing
    r = Restaurant(name=name, cuisine=cuisine)
    session.add(r)
    session.flush()
    return r


def persist_orders(session: Session, orders: Iterable[OrderInput]) -> dict[str, int]:
    """Upsert orders by ``external_id``. Returns ``{created, updated}`` counts."""
    created = 0
    updated = 0
    for inp in orders:
        restaurant = _get_or_create_restaurant(session, inp.restaurant_name, inp.cuisine)
        existing = session.execute(
            select(Order).where(Order.external_id == inp.external_id)
        ).scalar_one_or_none()

        if existing is None:
            order = Order(external_id=inp.external_id, restaurant_id=restaurant.id)
            session.add(order)
            created += 1
        else:
            order = existing
            order.items.clear()
            updated += 1

        order.restaurant_id = restaurant.id
        order.ordered_at = inp.ordered_at
        order.subtotal_cents = inp.subtotal_cents
        order.tax_cents = inp.tax_cents
        order.delivery_fee_cents = inp.delivery_fee_cents
        order.service_fee_cents = inp.service_fee_cents
        order.tip_cents = inp.tip_cents
        order.discount_cents = inp.discount_cents
        order.total_cents = inp.total_cents or (
            inp.subtotal_cents
            + inp.tax_cents
            + inp.delivery_fee_cents
            + inp.service_fee_cents
            + inp.tip_cents
            - inp.discount_cents
        )
        order.currency = inp.currency
        order.status = inp.status
        order.notes = inp.notes

        session.flush()
        for item in inp.items:
            session.add(
                OrderItem(
                    order_id=order.id,
                    name=item.name,
                    quantity=item.quantity,
                    unit_price_cents=item.unit_price_cents,
                    total_price_cents=item.total_price_cents
                    or item.unit_price_cents * item.quantity,
                )
            )

    return {"created": created, "updated": updated}
