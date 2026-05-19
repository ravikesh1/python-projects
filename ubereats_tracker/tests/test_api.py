from fastapi.testclient import TestClient

from ubereats_tracker.api import create_app
from ubereats_tracker.importers import import_csv, import_json


def _build_client(session_factory, samples_dir):
    s = session_factory()
    try:
        import_csv(s, samples_dir / "orders.csv")
        import_json(s, samples_dir / "orders.json")
        s.commit()
    finally:
        s.close()
    app = create_app(session_factory=session_factory)
    return TestClient(app)


def test_health(session_factory):
    app = create_app(session_factory=session_factory)
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_orders(session_factory, samples_dir):
    client = _build_client(session_factory, samples_dir)
    r = client.get("/api/orders?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert len(body["orders"]) == 5
    # Sorted desc by ordered_at
    dates = [o["ordered_at"] for o in body["orders"]]
    assert dates == sorted(dates, reverse=True)


def test_get_order_not_found(session_factory):
    app = create_app(session_factory=session_factory)
    client = TestClient(app)
    r = client.get("/api/orders/9999")
    assert r.status_code == 404


def test_analytics_summary_endpoint(session_factory, samples_dir):
    client = _build_client(session_factory, samples_dir)
    r = client.get("/api/analytics/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["order_count"] == 12
    assert body["total_cents"] > 0


def test_analytics_top_restaurants(session_factory, samples_dir):
    client = _build_client(session_factory, samples_dir)
    r = client.get("/api/analytics/top-restaurants?limit=3")
    assert r.status_code == 200
    assert len(r.json()["buckets"]) == 3


def test_dashboard_renders(session_factory, samples_dir):
    client = _build_client(session_factory, samples_dir)
    r = client.get("/")
    assert r.status_code == 200
    assert "Uber Eats Tracker" in r.text
    assert "Pizza Palace" in r.text
