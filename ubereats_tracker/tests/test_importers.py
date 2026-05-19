from ubereats_tracker.importers import import_csv, import_eml, import_json
from ubereats_tracker.importers._common import to_cents
from ubereats_tracker.models import Order, OrderItem, Restaurant


def test_to_cents_handles_various_inputs():
    assert to_cents(None) == 0
    assert to_cents("") == 0
    assert to_cents("$12.34") == 1234
    assert to_cents("12.34") == 1234
    assert to_cents("1,234.56") == 123456
    assert to_cents(12.34) == 1234
    assert to_cents(12) == 1200  # int treated as whole dollars


def test_import_csv(session, samples_dir):
    result = import_csv(session, samples_dir / "orders.csv")
    session.commit()
    assert result["created"] == 10
    assert result["updated"] == 0
    assert session.query(Order).count() == 10
    # Pizza Palace, Sushi Spot, Burger Barn, Taco Town, Thai Garden = 5
    assert session.query(Restaurant).count() == 5


def test_import_csv_is_idempotent(session, samples_dir):
    import_csv(session, samples_dir / "orders.csv")
    result2 = import_csv(session, samples_dir / "orders.csv")
    session.commit()
    assert result2["created"] == 0
    assert result2["updated"] == 10
    assert session.query(Order).count() == 10


def test_import_json_with_items(session, samples_dir):
    result = import_json(session, samples_dir / "orders.json")
    session.commit()
    assert result["created"] == 2
    ramen = session.query(Order).filter_by(external_id="ORD-2001").one()
    assert ramen.restaurant.name == "Ramen House"
    assert ramen.total_cents == 4229
    item_names = sorted(i.name for i in ramen.items)
    assert item_names == ["Gyoza", "Tonkotsu Ramen"]


def test_import_json_falls_back_to_computed_total(session, tmp_path):
    p = tmp_path / "compute.json"
    p.write_text(
        '[{"external_id": "C1", "restaurant": "X", '
        '"ordered_at": "2025-01-01T12:00:00", '
        '"amounts": {"subtotal": 10.00, "tax": 1.00, "tip": 2.00}}]'
    )
    import_json(session, p)
    session.commit()
    o = session.query(Order).filter_by(external_id="C1").one()
    assert o.total_cents == 1300


def test_import_eml(session, samples_dir):
    result = import_eml(session, samples_dir / "receipt.eml")
    session.commit()
    assert result["created"] == 1
    o = session.query(Order).one()
    assert o.external_id == "ABC123XYZ"
    assert o.restaurant.name == "Pizza Palace"
    assert o.subtotal_cents == 2900
    assert o.tax_cents == 290
    assert o.delivery_fee_cents == 299
    assert o.service_fee_cents == 350
    assert o.tip_cents == 500
    assert o.total_cents == 4339
    item_names = sorted(i.name for i in o.items)
    assert item_names == ["Garlic Knots", "Margherita Pizza", "Tiramisu"]


def test_eml_missing_order_id_raises(tmp_path, session):
    bad = tmp_path / "bad.eml"
    bad.write_text(
        "Subject: Hi\n\n<html><body>no order info here</body></html>"
    )
    import pytest

    with pytest.raises(ValueError):
        import_eml(session, bad)
