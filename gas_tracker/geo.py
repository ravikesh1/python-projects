"""Geocoding and distance helpers built on OpenStreetMap's Nominatim."""

from __future__ import annotations

import math
from dataclasses import dataclass

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "gas-tracker/0.1 (github.com/ravikesh1/python-projects)"
EARTH_RADIUS_MILES = 3958.8


class GeocodeError(RuntimeError):
    """Raised when a location string cannot be resolved to coordinates."""


@dataclass
class Place:
    lat: float
    lon: float
    display_name: str
    city: str | None = None
    state_code: str | None = None  # two-letter US state code, if resolvable


def geocode(query: str, timeout: float = 15.0) -> Place:
    """Resolve a free-form location ("Austin, TX", a zip code, ...) to a Place."""
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": query, "format": "json", "limit": 1, "addressdetails": 1},
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise GeocodeError(f"No match for location: {query!r}")
    hit = results[0]
    address = hit.get("address", {})

    city = address.get("city") or address.get("town") or address.get("village")
    state_code = None
    iso = address.get("ISO3166-2-lvl4", "")  # e.g. "US-TX"
    if iso.startswith("US-"):
        state_code = iso[3:]

    return Place(
        lat=float(hit["lat"]),
        lon=float(hit["lon"]),
        display_name=hit.get("display_name", query),
        city=city,
        state_code=state_code,
    )


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in miles."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))
