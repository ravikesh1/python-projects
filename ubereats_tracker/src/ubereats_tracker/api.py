"""FastAPI app: REST endpoints + a small dashboard."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from . import analytics
from .db import init_db, make_engine, make_session_factory
from .models import Order

_STATIC_DIR = Path(__file__).parent / "static"
_TEMPLATES_DIR = Path(__file__).parent / "templates"


def create_app(session_factory: Optional[sessionmaker[Session]] = None) -> FastAPI:
    app = FastAPI(title="Uber Eats Tracker", version="0.1.0")

    if session_factory is None:
        engine = make_engine()
        init_db(engine)
        session_factory = make_session_factory(engine)

    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    def get_session() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/orders")
    def list_orders(
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
        session: Session = Depends(get_session),
    ) -> dict:
        stmt = (
            select(Order)
            .order_by(Order.ordered_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = session.execute(stmt).scalars().all()
        return {
            "orders": [
                {
                    "id": o.id,
                    "external_id": o.external_id,
                    "restaurant": o.restaurant.name,
                    "ordered_at": o.ordered_at.isoformat(),
                    "total_cents": o.total_cents,
                    "currency": o.currency,
                    "status": o.status,
                    "tip_pct": round(o.tip_pct, 2),
                }
                for o in rows
            ]
        }

    @app.get("/api/orders/{order_id}")
    def get_order(order_id: int, session: Session = Depends(get_session)) -> dict:
        order = session.get(Order, order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return {
            "id": order.id,
            "external_id": order.external_id,
            "restaurant": order.restaurant.name,
            "ordered_at": order.ordered_at.isoformat(),
            "subtotal_cents": order.subtotal_cents,
            "tax_cents": order.tax_cents,
            "delivery_fee_cents": order.delivery_fee_cents,
            "service_fee_cents": order.service_fee_cents,
            "tip_cents": order.tip_cents,
            "discount_cents": order.discount_cents,
            "total_cents": order.total_cents,
            "currency": order.currency,
            "status": order.status,
            "notes": order.notes,
            "items": [
                {
                    "name": i.name,
                    "quantity": i.quantity,
                    "unit_price_cents": i.unit_price_cents,
                    "total_price_cents": i.total_price_cents,
                }
                for i in order.items
            ],
        }

    @app.get("/api/analytics/summary")
    def api_summary(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        session: Session = Depends(get_session),
    ) -> dict:
        s = analytics.summary(session, start, end)
        d = asdict(s)
        d["first_order_at"] = s.first_order_at.isoformat() if s.first_order_at else None
        d["last_order_at"] = s.last_order_at.isoformat() if s.last_order_at else None
        return d

    @app.get("/api/analytics/by-month")
    def api_by_month(session: Session = Depends(get_session)) -> dict:
        return {"buckets": [asdict(b) for b in analytics.by_month(session)]}

    @app.get("/api/analytics/top-restaurants")
    def api_top_restaurants(
        limit: int = Query(10, ge=1, le=100),
        session: Session = Depends(get_session),
    ) -> dict:
        return {
            "buckets": [
                asdict(b) for b in analytics.top_restaurants(session, limit=limit)
            ]
        }

    @app.get("/api/analytics/top-items")
    def api_top_items(
        limit: int = Query(10, ge=1, le=100),
        session: Session = Depends(get_session),
    ) -> dict:
        return {
            "buckets": [asdict(b) for b in analytics.top_items(session, limit=limit)]
        }

    @app.get("/api/analytics/by-day-of-week")
    def api_by_dow(session: Session = Depends(get_session)) -> dict:
        return {"buckets": [asdict(b) for b in analytics.by_day_of_week(session)]}

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
        s = analytics.summary(session)
        by_month = [asdict(b) for b in analytics.by_month(session)]
        top_r = [asdict(b) for b in analytics.top_restaurants(session, limit=10)]
        top_i = [asdict(b) for b in analytics.top_items(session, limit=10)]
        by_dow = [asdict(b) for b in analytics.by_day_of_week(session)]
        recent = (
            session.execute(
                select(Order).order_by(Order.ordered_at.desc()).limit(20)
            )
            .scalars()
            .all()
        )
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "summary": s,
                "by_month": by_month,
                "top_restaurants": top_r,
                "top_items": top_i,
                "by_dow": by_dow,
                "recent_orders": recent,
            },
        )

    return app


app = create_app()
