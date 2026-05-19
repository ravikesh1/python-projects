# Uber Eats Tracker

A personal Uber Eats order tracker and spend dashboard.

> **Scope note.** This tool does **not** interact with Uber Eats' systems
> in any way. It is a personal database that you populate manually — by
> exporting your order history (CSV/JSON), or by feeding it your receipt
> emails (`.eml`). Uber Eats' Terms of Service prohibit automated/bot
> access to the consumer app, so live integration is out of scope.

## Features

- **Schema**: restaurants, orders, line items (SQLite by default).
- **Importers**:
  - **CSV** — flat rows, one order per row.
  - **JSON** — full structure including items.
  - **`.eml`** — best-effort receipt email parsing (regex on a normalized
    text view). Tolerant of formatting changes; raises on missing
    order id / restaurant.
- **Analytics**: monthly spend, top restaurants, top items, day-of-week
  breakdown, avg order, avg tip %, fees & tax totals.
- **Web dashboard**: FastAPI + Jinja2 + Chart.js (single-page, no JS build).
- **CLI**: `import`, `list`, `stats`, `serve` via Typer.
- **Tests**: pytest, in-memory SQLite.

## Quick start

```bash
cd ubereats_tracker
uv sync --extra dev
uv run ubereats-tracker import samples/orders.csv
uv run ubereats-tracker import samples/orders.json
uv run ubereats-tracker import samples/receipt.eml
uv run ubereats-tracker stats
uv run ubereats-tracker serve   # http://127.0.0.1:8000
```

By default the DB lives at `~/.ubereats_tracker/orders.db`. Override with
`UBEREATS_DB_URL`:

```bash
export UBEREATS_DB_URL="sqlite:////tmp/orders.db"
# or postgres:
export UBEREATS_DB_URL="postgresql+psycopg://user:pass@host/db"
```

## CSV format

Header row required (case-insensitive). Money columns are dollars.

```
external_id, restaurant, ordered_at, subtotal, tax, delivery_fee,
service_fee, tip, discount, total, currency, status, cuisine, notes
```

See `samples/orders.csv`.

## JSON format

List of order objects; see `samples/orders.json`. Each order may include
`items: [{ name, quantity, unit_price, total_price }]`.

## .eml receipts

Drop in receipt emails as `.eml` (most clients export this). The parser
looks for `Order ID`, `Subtotal`, `Tax`, `Delivery Fee`, `Service Fee`,
`Tip`, `Total`, and `N x Item ... $X.XX` lines. If the email layout
differs too much, the parser raises `ValueError` — fall back to JSON.

## API

| Endpoint | Description |
| --- | --- |
| `GET /` | HTML dashboard |
| `GET /api/health` | Liveness check |
| `GET /api/orders?limit=&offset=` | List orders |
| `GET /api/orders/{id}` | Single order with items |
| `GET /api/analytics/summary?start=&end=` | Totals + averages |
| `GET /api/analytics/by-month` | Spend per month |
| `GET /api/analytics/top-restaurants?limit=` | |
| `GET /api/analytics/top-items?limit=` | |
| `GET /api/analytics/by-day-of-week` | |

## Tests

```bash
uv run --extra dev pytest
```

## Layout

```
ubereats_tracker/
├── pyproject.toml
├── README.md
├── samples/                # demo CSV/JSON/EML
├── src/ubereats_tracker/
│   ├── models.py           # SQLAlchemy schema
│   ├── db.py               # engine / session
│   ├── importers/          # csv, json, eml
│   ├── analytics.py        # spend rollups
│   ├── api.py              # FastAPI app + dashboard
│   ├── cli.py              # Typer entry point
│   ├── templates/dashboard.html
│   └── static/style.css
└── tests/
```
