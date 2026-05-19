"""CSV importer.

Expected columns (header row required, case-insensitive):

    external_id, restaurant, ordered_at, subtotal, tax, delivery_fee,
    service_fee, tip, discount, total, currency, status, cuisine, notes

Monetary columns are dollars (e.g. ``"12.34"`` or ``"$12.34"``).
``ordered_at`` is ISO-8601 (``2025-01-15T19:42:00``) or any format
``dateutil`` can parse.

Items are not supported by the CSV importer — use JSON or .eml for those.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from dateutil import parser as dtparser
from sqlalchemy.orm import Session

from ._common import OrderInput, persist_orders, to_cents


def _normalize_headers(row: dict[str, str]) -> dict[str, str]:
    return {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}


def parse_csv(path: Path | str) -> List[OrderInput]:
    path = Path(path)
    orders: List[OrderInput] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = _normalize_headers(raw)
            if not row.get("external_id") or not row.get("restaurant"):
                continue
            orders.append(
                OrderInput(
                    external_id=row["external_id"],
                    restaurant_name=row["restaurant"],
                    ordered_at=dtparser.parse(row["ordered_at"]),
                    subtotal_cents=to_cents(row.get("subtotal")),
                    tax_cents=to_cents(row.get("tax")),
                    delivery_fee_cents=to_cents(row.get("delivery_fee")),
                    service_fee_cents=to_cents(row.get("service_fee")),
                    tip_cents=to_cents(row.get("tip")),
                    discount_cents=to_cents(row.get("discount")),
                    total_cents=to_cents(row.get("total")),
                    currency=row.get("currency") or "USD",
                    status=row.get("status") or "delivered",
                    cuisine=row.get("cuisine") or None,
                    notes=row.get("notes") or None,
                )
            )
    return orders


def import_csv(session: Session, path: Path | str) -> dict[str, int]:
    return persist_orders(session, parse_csv(path))
