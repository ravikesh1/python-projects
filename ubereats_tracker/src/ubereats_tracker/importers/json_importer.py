"""JSON importer.

Accepts either a list of order objects or a single object. Each order:

    {
      "external_id": "abc-123",
      "restaurant": "Pizza Place",
      "cuisine": "Italian",
      "ordered_at": "2025-01-15T19:42:00",
      "currency": "USD",
      "status": "delivered",
      "amounts": {                  # dollars (number or string)
        "subtotal": 18.50,
        "tax": 1.85,
        "delivery_fee": 3.99,
        "service_fee": 2.00,
        "tip": 4.00,
        "discount": 0,
        "total": 30.34
      },
      "items": [
        { "name": "Margherita", "quantity": 1,
          "unit_price": 14.50, "total_price": 14.50 },
        { "name": "Coke", "quantity": 2, "unit_price": 2.00 }
      ],
      "notes": "Optional"
    }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from dateutil import parser as dtparser
from sqlalchemy.orm import Session

from ._common import OrderInput, OrderItemInput, persist_orders, to_cents


def _parse_order(obj: dict[str, Any]) -> OrderInput:
    amounts = obj.get("amounts") or {}
    items_raw = obj.get("items") or []
    items = [
        OrderItemInput(
            name=str(i["name"]),
            quantity=int(i.get("quantity", 1)),
            unit_price_cents=to_cents(i.get("unit_price")),
            total_price_cents=to_cents(i.get("total_price")),
        )
        for i in items_raw
        if i.get("name")
    ]
    return OrderInput(
        external_id=str(obj["external_id"]),
        restaurant_name=str(obj["restaurant"]),
        ordered_at=dtparser.parse(obj["ordered_at"]),
        subtotal_cents=to_cents(amounts.get("subtotal")),
        tax_cents=to_cents(amounts.get("tax")),
        delivery_fee_cents=to_cents(amounts.get("delivery_fee")),
        service_fee_cents=to_cents(amounts.get("service_fee")),
        tip_cents=to_cents(amounts.get("tip")),
        discount_cents=to_cents(amounts.get("discount")),
        total_cents=to_cents(amounts.get("total")),
        currency=obj.get("currency", "USD"),
        status=obj.get("status", "delivered"),
        cuisine=obj.get("cuisine"),
        notes=obj.get("notes"),
        items=items,
    )


def parse_json(path: Path | str) -> List[OrderInput]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        raise ValueError("JSON root must be an object or list of objects")
    return [_parse_order(o) for o in raw]


def import_json(session: Session, path: Path | str) -> dict[str, int]:
    return persist_orders(session, parse_json(path))
