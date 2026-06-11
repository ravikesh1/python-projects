"""Price sources and the logic that attaches a price to each station.

There is no free official feed of per-station US gas prices (GasBuddy has no
public API; OPIS-style feeds are paid). This module layers what *is* freely
available:

1. Explicit OSM ``fuel:*:price`` tags on the station itself (rare, but exact).
2. CollectAPI city/state averages as an area baseline (free tier, needs a key).

Each quoted price carries its source so the table can show how trustworthy it
is. A paid per-station feed can be added later as another provider.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from statistics import mean

import requests

from .stations import Station

COLLECTAPI_URL = "https://api.collectapi.com/gasPrice"

FUEL_KINDS = ("regular", "midgrade", "premium", "diesel")

# CollectAPI response field -> our fuel kind
_COLLECTAPI_FIELDS = {
    "regular": "gasoline",
    "midgrade": "midGrade",
    "premium": "premium",
    "diesel": "diesel",
}


@dataclass
class Quote:
    price: float  # $/gal
    source: str  # "station (OSM)", "city avg", "state avg"


class CollectApiProvider:
    """City- and state-level US average prices from collectapi.com (free tier)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("COLLECTAPI_KEY")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def state_prices(self, state_code: str, timeout: float = 20.0) -> dict[str, dict[str, float]]:
        """Return {city name (lowercased) -> {fuel kind -> $/gal}} for a state."""
        resp = requests.get(
            f"{COLLECTAPI_URL}/stateUsaPrice",
            params={"state": state_code},
            headers={
                "authorization": f"apikey {self.api_key}",
                "content-type": "application/json",
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
        cities: dict[str, dict[str, float]] = {}
        for entry in payload.get("result", {}).get("cities", []):
            prices = {}
            for fuel, api_field in _COLLECTAPI_FIELDS.items():
                try:
                    prices[fuel] = float(entry[api_field])
                except (KeyError, TypeError, ValueError):
                    continue
            if prices:
                cities[entry.get("name", "").strip().lower()] = prices
        return cities


def quote_station(
    station: Station,
    fuel: str,
    city_prices: dict[str, dict[str, float]],
    search_city: str | None,
) -> Quote | None:
    """Best available price for one station: own OSM tag, else city avg, else state avg."""
    if fuel in station.osm_prices:
        return Quote(station.osm_prices[fuel], "station (OSM)")

    for city in (station.city, search_city):
        if city and city.strip().lower() in city_prices:
            price = city_prices[city.strip().lower()].get(fuel)
            if price is not None:
                return Quote(price, "city avg")

    state_wide = [p[fuel] for p in city_prices.values() if fuel in p]
    if state_wide:
        return Quote(mean(state_wide), "state avg")
    return None
