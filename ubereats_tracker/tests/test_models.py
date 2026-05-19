from datetime import datetime

from ubereats_tracker.models import Order, OrderItem, Restaurant


def test_order_total_dollars_and_tip_pct(session):
    r = Restaurant(name="Test Spot", cuisine="Test")
    session.add(r)
    session.flush()
    o = Order(
        external_id="X1",
        restaurant_id=r.id,
        ordered_at=datetime(2025, 1, 1, 12, 0),
        subtotal_cents=2000,
        tip_cents=400,
        total_cents=2400,
    )
    session.add(o)
    session.flush()

    assert o.total_dollars == 24.0
    assert o.tip_pct == 20.0


def test_order_tip_pct_zero_when_no_subtotal(session):
    r = Restaurant(name="Free Spot")
    session.add(r)
    session.flush()
    o = Order(
        external_id="X2",
        restaurant_id=r.id,
        ordered_at=datetime(2025, 1, 1),
    )
    session.add(o)
    session.flush()
    assert o.tip_pct == 0.0


def test_order_items_cascade_delete(session):
    r = Restaurant(name="Cascade Spot")
    session.add(r)
    session.flush()
    o = Order(external_id="X3", restaurant_id=r.id, ordered_at=datetime(2025, 1, 1))
    o.items.append(OrderItem(name="A", quantity=1, unit_price_cents=500, total_price_cents=500))
    session.add(o)
    session.flush()

    session.delete(o)
    session.flush()
    assert session.query(OrderItem).count() == 0
