"""Offline tests for gas_tracker: HTTP is stubbed, no network required."""

import json
from unittest.mock import patch

import pytest

from gas_tracker import geo, prices, stations
from gas_tracker.cli import parse_args
from gas_tracker.prices import CollectApiProvider, quote_station
from gas_tracker.stations import Station, parse_price


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_haversine_known_distance():
    # Austin -> Houston is ~146 miles
    dist = geo.haversine_miles(30.2672, -97.7431, 29.7604, -95.3698)
    assert 140 < dist < 152


def test_haversine_zero():
    assert geo.haversine_miles(30.0, -97.0, 30.0, -97.0) == 0


def test_geocode_parses_nominatim_result():
    payload = [
        {
            "lat": "30.2672",
            "lon": "-97.7431",
            "display_name": "Austin, Travis County, Texas",
            "address": {"city": "Austin", "ISO3166-2-lvl4": "US-TX"},
        }
    ]
    with patch.object(geo.requests, "get", return_value=FakeResponse(payload)):
        place = geo.geocode("Austin, TX")
    assert place.lat == pytest.approx(30.2672)
    assert place.city == "Austin"
    assert place.state_code == "TX"


def test_geocode_no_match_raises():
    with patch.object(geo.requests, "get", return_value=FakeResponse([])):
        with pytest.raises(geo.GeocodeError):
            geo.geocode("nowhere at all")


@pytest.mark.parametrize(
    "raw,expected",
    [("3.45", 3.45), ("3.45 USD", 3.45), ("$3.459", 3.459), ("USD 3", 3.0), ("cheap", None)],
)
def test_parse_price(raw, expected):
    assert parse_price(raw) == expected


def test_find_stations_parses_nodes_and_ways():
    payload = {
        "elements": [
            {
                "type": "node",
                "id": 1,
                "lat": 30.27,
                "lon": -97.74,
                "tags": {
                    "amenity": "fuel",
                    "name": "Cheapo Gas",
                    "brand": "Cheapo",
                    "addr:housenumber": "100",
                    "addr:street": "Main St",
                    "addr:city": "Austin",
                    "fuel:octane_87:price": "2.89 USD",
                },
            },
            {
                "type": "way",
                "id": 2,
                "center": {"lat": 30.30, "lon": -97.70},
                "tags": {"amenity": "fuel", "brand": "Shell"},
            },
            {"type": "relation", "id": 3, "tags": {}},  # no coordinates -> skipped
        ]
    }
    with patch.object(stations.requests, "post", return_value=FakeResponse(payload)):
        result = stations.find_stations(30.2672, -97.7431, radius_miles=5)

    assert len(result) == 2
    assert result[0].name == "Cheapo Gas"  # nearest first
    assert result[0].address == "100 Main St, Austin"
    assert result[0].osm_prices == {"regular": 2.89}
    assert result[1].name == "Shell"  # falls back to brand for unnamed ways
    assert result[0].distance_miles < result[1].distance_miles


def test_collectapi_state_prices():
    payload = {
        "success": True,
        "result": {
            "state": "TX",
            "cities": [
                {"name": "Austin", "gasoline": "2.83", "midGrade": "3.19",
                 "premium": "3.49", "diesel": "3.05"},
                {"name": "Houston", "gasoline": "2.75", "midGrade": "n/a",
                 "premium": "3.40", "diesel": "2.99"},
            ],
        },
    }
    provider = CollectApiProvider(api_key="test-key")
    with patch.object(prices.requests, "get", return_value=FakeResponse(payload)):
        result = provider.state_prices("TX")

    assert result["austin"]["regular"] == 2.83
    assert "midgrade" not in result["houston"]  # unparseable values are dropped
    assert result["houston"]["diesel"] == 2.99


def test_provider_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("COLLECTAPI_KEY", raising=False)
    assert not CollectApiProvider().available
    assert CollectApiProvider(api_key="k").available


def _station(**overrides):
    base = dict(
        osm_id="node/1", name="S", lat=30.0, lon=-97.0, distance_miles=1.0,
    )
    base.update(overrides)
    return Station(**base)


def test_quote_prefers_osm_tag():
    station = _station(osm_prices={"regular": 2.59}, city="Austin")
    city_prices = {"austin": {"regular": 2.83}}
    quote = quote_station(station, "regular", city_prices, "Austin")
    assert quote.price == 2.59
    assert quote.source == "station (OSM)"


def test_quote_falls_back_to_city_then_state_avg():
    city_prices = {"austin": {"regular": 2.83}, "houston": {"regular": 2.75}}

    by_city = quote_station(_station(city="Houston"), "regular", city_prices, "Austin")
    assert (by_city.price, by_city.source) == (2.75, "city avg")

    by_search_city = quote_station(_station(), "regular", city_prices, "Austin")
    assert (by_search_city.price, by_search_city.source) == (2.83, "city avg")

    by_state = quote_station(_station(), "regular", city_prices, "Dallas")
    assert by_state.source == "state avg"
    assert by_state.price == pytest.approx(2.79)


def test_quote_none_without_any_data():
    assert quote_station(_station(), "regular", {}, None) is None


def test_cli_requires_location_or_coords(capsys):
    with pytest.raises(SystemExit):
        parse_args([])
    assert parse_args(["Austin, TX"]).fuel == "regular"
    assert parse_args(["--lat", "30.1", "--lon", "-97.5", "--fuel", "diesel"]).fuel == "diesel"
