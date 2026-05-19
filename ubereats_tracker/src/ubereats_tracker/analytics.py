"""Spend analytics over the orders table."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Order, OrderItem, Restaurant


@dataclass
class Summary:
    order_count: int
    total_cents: int
    subtotal_cents: int
    tax_cents: int
    fees_cents: int
    tip_cents: int
    discount_cents: int
    avg_order_cents: int
    avg_tip_pct: float
    first_order_at: Optional[datetime]
    last_order_at: Optional[datetime]


@dataclass
class BucketRow:
    label: str
    order_count: int
    total_cents: int


def _filter_window(stmt, start: Optional[datetime], end: Optional[datetime]):
    if start is not None:
        stmt = stmt.where(Order.ordered_at >= start)
    if end is not None:
        stmt = stmt.where(Order.ordered_at < end)
    return stmt


def summary(
    session: Session,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Summary:
    stmt = select(
        func.count(Order.id),
        func.coalesce(func.sum(Order.total_cents), 0),
        func.coalesce(func.sum(Order.subtotal_cents), 0),
        func.coalesce(func.sum(Order.tax_cents), 0),
        func.coalesce(
            func.sum(Order.delivery_fee_cents + Order.service_fee_cents), 0
        ),
        func.coalesce(func.sum(Order.tip_cents), 0),
        func.coalesce(func.sum(Order.discount_cents), 0),
        func.min(Order.ordered_at),
        func.max(Order.ordered_at),
    )
    stmt = _filter_window(stmt, start, end)
    row = session.execute(stmt).one()
    count = row[0] or 0
    total = row[1] or 0
    subtotal = row[2] or 0
    tip = row[5] or 0
    avg_order = total // count if count else 0
    avg_tip_pct = (tip / subtotal * 100) if subtotal else 0.0
    return Summary(
        order_count=count,
        total_cents=total,
        subtotal_cents=subtotal,
        tax_cents=row[3] or 0,
        fees_cents=row[4] or 0,
        tip_cents=tip,
        discount_cents=row[6] or 0,
        avg_order_cents=avg_order,
        avg_tip_pct=round(avg_tip_pct, 2),
        first_order_at=row[7],
        last_order_at=row[8],
    )


def _month_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def by_month(
    session: Session,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[BucketRow]:
    """Group orders by calendar month (driver-side aggregation for SQLite portability)."""
    stmt = select(Order.ordered_at, Order.total_cents)
    stmt = _filter_window(stmt, start, end)
    buckets: dict[str, list[int]] = {}
    for ordered_at, total in session.execute(stmt):
        key = _month_key(ordered_at)
        buckets.setdefault(key, []).append(total or 0)
    rows = [
        BucketRow(label=k, order_count=len(v), total_cents=sum(v))
        for k, v in sorted(buckets.items())
    ]
    return rows


def top_restaurants(
    session: Session,
    limit: int = 10,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[BucketRow]:
    stmt = (
        select(
            Restaurant.name,
            func.count(Order.id),
            func.coalesce(func.sum(Order.total_cents), 0),
        )
        .join(Order, Order.restaurant_id == Restaurant.id)
        .group_by(Restaurant.id)
        .order_by(func.sum(Order.total_cents).desc())
        .limit(limit)
    )
    stmt = _filter_window(stmt, start, end)
    return [
        BucketRow(label=name, order_count=count, total_cents=total)
        for name, count, total in session.execute(stmt)
    ]


def top_items(
    session: Session,
    limit: int = 10,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[BucketRow]:
    stmt = (
        select(
            OrderItem.name,
            func.coalesce(func.sum(OrderItem.quantity), 0),
            func.coalesce(func.sum(OrderItem.total_price_cents), 0),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .group_by(OrderItem.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    )
    stmt = _filter_window(stmt, start, end)
    return [
        BucketRow(label=name, order_count=int(qty), total_cents=int(total))
        for name, qty, total in session.execute(stmt)
    ]


_DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def by_day_of_week(
    session: Session,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[BucketRow]:
    stmt = select(Order.ordered_at, Order.total_cents)
    stmt = _filter_window(stmt, start, end)
    buckets: dict[int, list[int]] = {i: [] for i in range(7)}
    for ordered_at, total in session.execute(stmt):
        buckets[ordered_at.weekday()].append(total or 0)
    return [
        BucketRow(label=_DOW[i], order_count=len(v), total_cents=sum(v))
        for i, v in buckets.items()
    ]
