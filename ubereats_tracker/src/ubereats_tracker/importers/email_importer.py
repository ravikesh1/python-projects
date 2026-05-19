"""Best-effort .eml receipt importer.

Uber Eats receipt HTML changes over time and varies by region, so this parser
is intentionally tolerant: it strips HTML to text and looks for well-known
labels (``Subtotal``, ``Tax``, ``Delivery Fee``, ``Service Fee``,
``Tip``, ``Total``) followed by a currency amount. Line items are picked up
from ``N x Item Name ... $X.XX`` patterns.

If the parser cannot find an order id or restaurant name, it raises
``ValueError`` — caller should fall back to manual JSON/CSV import.
"""

from __future__ import annotations

import email
import email.policy
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup
from dateutil import parser as dtparser
from sqlalchemy.orm import Session

from ._common import OrderInput, OrderItemInput, persist_orders, to_cents

_AMOUNT = r"\$?\s*(-?\d+(?:,\d{3})*(?:\.\d{2})?)"

_LABELS = {
    "subtotal": re.compile(rf"\bSubtotal\b[^$\d-]*{_AMOUNT}", re.IGNORECASE),
    "tax": re.compile(rf"\b(?:Tax(?:es)?|GST|HST|VAT)\b[^$\d-]*{_AMOUNT}", re.IGNORECASE),
    "delivery": re.compile(rf"\bDelivery\s*Fee\b[^$\d-]*{_AMOUNT}", re.IGNORECASE),
    "service": re.compile(rf"\bService\s*Fee\b[^$\d-]*{_AMOUNT}", re.IGNORECASE),
    "tip": re.compile(rf"\b(?:Tip|Gratuity)\b[^$\d-]*{_AMOUNT}", re.IGNORECASE),
    "discount": re.compile(rf"\b(?:Discount|Promotion)\b[^$\d-]*-?{_AMOUNT}", re.IGNORECASE),
    "total": re.compile(rf"\bTotal\b[^$\d-]*{_AMOUNT}", re.IGNORECASE),
}

_ORDER_ID = re.compile(r"Order\s*(?:ID|#|Number)[:\s#]*([A-Za-z0-9-]{6,})", re.IGNORECASE)
_ITEM_LINE = re.compile(rf"^\s*(\d+)\s*[x×]\s*(.+?)\s+{_AMOUNT}\s*$", re.MULTILINE)


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n")
    return re.sub(r"[ \t]+", " ", text)


def _extract_text(msg: email.message.EmailMessage) -> str:
    html_part = msg.get_body(preferencelist=("html",))
    if html_part is not None:
        return _html_to_text(html_part.get_content())
    text_part = msg.get_body(preferencelist=("plain",))
    if text_part is not None:
        return text_part.get_content()
    return ""


def _find_amount(pattern: re.Pattern[str], text: str) -> int:
    m = pattern.search(text)
    if not m:
        return 0
    return to_cents(m.group(1))


def _find_restaurant(text: str, subject: str) -> Optional[str]:
    m = re.search(r"(?:Your order from|order from)\s+(.+?)(?:[\n\r]|on |has been)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip().strip(".")
    m = re.search(r"order from\s+(.+)", subject, re.IGNORECASE)
    if m:
        return m.group(1).strip().strip(".")
    return None


def _find_ordered_at(msg: email.message.EmailMessage, text: str) -> datetime:
    date_header = msg.get("Date")
    if date_header:
        try:
            return dtparser.parse(date_header)
        except (ValueError, TypeError):
            pass
    m = re.search(
        r"(\w+ \d{1,2},?\s*\d{4}(?:[, ]+\d{1,2}:\d{2}\s*(?:AM|PM)?)?)",
        text,
    )
    if m:
        try:
            return dtparser.parse(m.group(1))
        except (ValueError, TypeError):
            pass
    return datetime.now()


def _find_items(text: str) -> List[OrderItemInput]:
    items: List[OrderItemInput] = []
    for match in _ITEM_LINE.finditer(text):
        qty = int(match.group(1))
        name = match.group(2).strip()
        price_cents = to_cents(match.group(3))
        if name.lower() in {"subtotal", "tax", "total", "tip"}:
            continue
        items.append(
            OrderItemInput(
                name=name,
                quantity=qty,
                unit_price_cents=price_cents // qty if qty else price_cents,
                total_price_cents=price_cents,
            )
        )
    return items


def parse_eml(path: Path | str) -> OrderInput:
    msg = email.message_from_bytes(
        Path(path).read_bytes(), policy=email.policy.default
    )
    subject = str(msg.get("Subject", ""))
    text = _extract_text(msg)

    order_id_match = _ORDER_ID.search(text) or _ORDER_ID.search(subject)
    if not order_id_match:
        raise ValueError(f"Could not find order id in {path}")
    external_id = order_id_match.group(1)

    restaurant = _find_restaurant(text, subject)
    if not restaurant:
        raise ValueError(f"Could not find restaurant name in {path}")

    return OrderInput(
        external_id=external_id,
        restaurant_name=restaurant,
        ordered_at=_find_ordered_at(msg, text),
        subtotal_cents=_find_amount(_LABELS["subtotal"], text),
        tax_cents=_find_amount(_LABELS["tax"], text),
        delivery_fee_cents=_find_amount(_LABELS["delivery"], text),
        service_fee_cents=_find_amount(_LABELS["service"], text),
        tip_cents=_find_amount(_LABELS["tip"], text),
        discount_cents=_find_amount(_LABELS["discount"], text),
        total_cents=_find_amount(_LABELS["total"], text),
        items=_find_items(text),
    )


def import_eml(session: Session, path: Path | str) -> dict[str, int]:
    return persist_orders(session, [parse_eml(path)])
