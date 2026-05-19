from datetime import datetime

from ubereats_tracker import analytics
from ubereats_tracker.importers import import_csv, import_json


def _seed(session, samples_dir):
    import_csv(session, samples_dir / "orders.csv")
    import_json(session, samples_dir / "orders.json")
    session.commit()


def test_summary(session, samples_dir):
    _seed(session, samples_dir)
    s = analytics.summary(session)
    assert s.order_count == 12
    assert s.total_cents > 0
    assert s.avg_order_cents == s.total_cents // s.order_count
    assert 0 < s.avg_tip_pct < 30


def test_summary_window(session, samples_dir):
    _seed(session, samples_dir)
    s = analytics.summary(
        session,
        start=datetime(2025, 1, 1),
        end=datetime(2025, 2, 1),
    )
    assert s.order_count == 3  # Jan orders only


def test_by_month_buckets(session, samples_dir):
    _seed(session, samples_dir)
    rows = analytics.by_month(session)
    labels = [r.label for r in rows]
    assert labels == ["2025-01", "2025-02", "2025-03", "2025-04"]
    by_label = {r.label: r for r in rows}
    assert by_label["2025-01"].order_count == 3
    assert by_label["2025-04"].order_count == 3  # 1 csv + 2 json


def test_top_restaurants(session, samples_dir):
    _seed(session, samples_dir)
    rows = analytics.top_restaurants(session, limit=3)
    assert len(rows) == 3
    totals = [r.total_cents for r in rows]
    assert totals == sorted(totals, reverse=True)


def test_top_items(session, samples_dir):
    _seed(session, samples_dir)
    rows = analytics.top_items(session, limit=5)
    assert len(rows) >= 1
    qtys = [r.order_count for r in rows]
    assert qtys == sorted(qtys, reverse=True)


def test_by_day_of_week_has_seven_buckets(session, samples_dir):
    _seed(session, samples_dir)
    rows = analytics.by_day_of_week(session)
    assert len(rows) == 7
    assert {r.label for r in rows} == {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
