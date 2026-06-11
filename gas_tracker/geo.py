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


KM_PER_MILE = 1.609344


@dataclass
class Place:
    lat: float
    lon: float
    display_name: str
    city: str | None = None
    region_code: str | None = None  # state/province code, e.g. "TX" or "BC"
    country_code: str | None = None  # ISO 3166-1 alpha-2, e.g. "us", "ca"


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
    region_code = None
    iso = address.get("ISO3166-2-lvl4", "")  # e.g. "US-TX", "CA-BC"
    if "-" in iso:
        region_code = iso.split("-", 1)[1]

    return Place(
        lat=float(hit["lat"]),
        lon=float(hit["lon"]),
        display_name=hit.get("display_name", query),
        city=city,
        region_code=region_code,
        country_code=address.get("country_code"),
    )


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in miles."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))
