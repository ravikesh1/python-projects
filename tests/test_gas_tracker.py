"""Offline tests for gas_tracker: HTTP is stubbed, no network required."""

import json
from unittest.mock import patch

import pytest

from gas_tracker import geo, prices, stations
from gas_tracker.cli import DEFAULT_LOCATION, is_metric, parse_args
from gas_tracker.geo import Place
from gas_tracker.prices import CollectApiProvider, area_prices, quote_station
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
            "lat": "49.1913",
            "lon": "-122.8490",
            "display_name": "Surrey, Metro Vancouver, British Columbia, Canada",
            "address": {
                "city": "Surrey",
                "ISO3166-2-lvl4": "CA-BC",
                "country_code": "ca",
            },
        }
    ]
    with patch.object(geo.requests, "get", return_value=FakeResponse(payload)):
        place = geo.geocode("Surrey, BC, Canada")
    assert place.lat == pytest.approx(49.1913)
    assert place.city == "Surrey"
    assert place.region_code == "BC"
    assert place.country_code == "ca"


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


def test_collectapi_canada_city_prices_converts_cents_per_litre():
    payload = {
        "success": True,
        "result": {"name": "Surrey", "gasoline": "162.9", "diesel": "1.71", "premium": "n/a"},
    }
    provider = CollectApiProvider(api_key="test-key")
    with patch.object(prices.requests, "get", return_value=FakeResponse(payload)):
        result = provider.canada_city_prices("Surrey")

    assert result["regular"] == pytest.approx(1.629)  # cents/L normalised to $/L
    assert result["diesel"] == 1.71  # already $/L, left alone
    assert "premium" not in result


def test_collectapi_canada_handles_list_response():
    payload = {
        "success": True,
        "result": [
            {"name": "Vancouver", "gasoline": "1.75"},
            {"name": "Surrey", "gasoline": "1.62"},
        ],
    }
    provider = CollectApiProvider(api_key="test-key")
    with patch.object(prices.requests, "get", return_value=FakeResponse(payload)):
        result = provider.canada_city_prices("surrey")
    assert result["regular"] == 1.62


def test_area_prices_dispatches_by_country():
    provider = CollectApiProvider(api_key="test-key")
    surrey = Place(49.19, -122.85, "Surrey", city="Surrey", region_code="BC", country_code="ca")
    austin = Place(30.27, -97.74, "Austin", city="Austin", region_code="TX", country_code="us")

    with patch.object(
        CollectApiProvider, "canada_city_prices", return_value={"regular": 1.62}
    ) as ca_mock:
        assert area_prices(provider, surrey) == {"surrey": {"regular": 1.62}}
        ca_mock.assert_called_once_with("Surrey")

    with patch.object(
        CollectApiProvider, "state_prices", return_value={"austin": {"regular": 2.83}}
    ) as us_mock:
        assert area_prices(provider, austin) == {"austin": {"regular": 2.83}}
        us_mock.assert_called_once_with("TX")

    assert area_prices(CollectApiProvider(api_key=None), surrey) == {}


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


def test_quote_falls_back_to_city_then_area_avg():
    city_prices = {"surrey": {"regular": 1.62}, "vancouver": {"regular": 1.75}}

    by_city = quote_station(_station(city="Vancouver"), "regular", city_prices, "Surrey")
    assert (by_city.price, by_city.source) == (1.75, "city avg")

    by_search_city = quote_station(_station(), "regular", city_prices, "Surrey")
    assert (by_search_city.price, by_search_city.source) == (1.62, "city avg")

    by_area = quote_station(_station(), "regular", city_prices, "Burnaby")
    assert by_area.source == "area avg"
    assert by_area.price == pytest.approx(1.685)


def test_quote_none_without_any_data():
    assert quote_station(_station(), "regular", {}, None) is None


def test_cli_defaults_to_surrey():
    args = parse_args([])
    assert args.location == DEFAULT_LOCATION
    assert "Surrey" in args.location
    assert parse_args(["Guildford, Surrey, BC"]).location == "Guildford, Surrey, BC"
    coords = parse_args(["--lat", "49.19", "--lon", "-122.85", "--fuel", "diesel"])
    assert coords.location is None
    assert coords.fuel == "diesel"


def test_is_metric_outside_us():
    assert is_metric(Place(49.19, -122.85, "Surrey", country_code="ca"))
    assert not is_metric(Place(30.27, -97.74, "Austin", country_code="us"))
    assert is_metric(Place(49.19, -122.85, "49.19, -122.85"))  # bare coords -> metric
