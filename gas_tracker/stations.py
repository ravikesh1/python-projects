"""Find nearby fuel stations via the OpenStreetMap Overpass API."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import requests

from .geo import USER_AGENT, haversine_miles

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
METERS_PER_MILE = 1609.344

# OSM price tagging is sparse and unstandardised; check the variants seen in the wild.
PRICE_TAG_VARIANTS: dict[str, tuple[str, ...]] = {
    "regular": (
        "fuel:octane_87:price",
        "fuel:regular:price",
        "price:fuel:octane_87",
        "fuel:price",
    ),
    "midgrade": ("fuel:octane_89:price", "fuel:midgrade:price", "price:fuel:octane_89"),
    "premium": (
        "fuel:octane_91:price",
        "fuel:octane_93:price",
        "fuel:premium:price",
        "price:fuel:octane_91",
    ),
    "diesel": ("fuel:diesel:price", "price:fuel:diesel", "diesel:price"),
}

_PRICE_RE = re.compile(r"(\d+(?:\.\d+)?)")


@dataclass
class Station:
    osm_id: str
    name: str
    lat: float
    lon: float
    distance_miles: float
    brand: str | None = None
    address: str | None = None
    city: str | None = None
    # fuel kind -> $/gal, taken from explicit OSM tags (rare, but per-station truth)
    osm_prices: dict[str, float] = field(default_factory=dict)


def parse_price(value: str) -> float | None:
    """Extract a numeric price from tag values like '3.45', '3.45 USD', '$3.45'."""
    match = _PRICE_RE.search(value)
    return float(match.group(1)) if match else None


def _extract_prices(tags: dict[str, str]) -> dict[str, float]:
    prices: dict[str, float] = {}
    for fuel, variants in PRICE_TAG_VARIANTS.items():
        for tag in variants:
            if tag in tags:
                price = parse_price(tags[tag])
                if price is not None:
                    prices[fuel] = price
                    break
    return prices


def _build_address(tags: dict[str, str]) -> str | None:
    parts = [tags.get("addr:housenumber"), tags.get("addr:street"), tags.get("addr:city")]
    parts = [p for p in parts if p]
    return " ".join(parts[:2]) + (f", {parts[2]}" if len(parts) > 2 else "") if parts else None


def _element_to_station(element: dict, origin_lat: float, origin_lon: float) -> Station | None:
    if "center" in element:  # ways and relations come back with a computed center
        lat, lon = element["center"]["lat"], element["center"]["lon"]
    elif "lat" in element:
        lat, lon = element["lat"], element["lon"]
    else:
        return None
    tags = element.get("tags", {})
    return Station(
        osm_id=f"{element['type']}/{element['id']}",
        name=tags.get("name") or tags.get("brand") or "(unnamed station)",
        brand=tags.get("brand"),
        lat=lat,
        lon=lon,
        distance_miles=haversine_miles(origin_lat, origin_lon, lat, lon),
        address=_build_address(tags),
        city=tags.get("addr:city"),
        osm_prices=_extract_prices(tags),
    )


def find_stations(
    lat: float, lon: float, radius_miles: float = 5.0, timeout: float = 45.0
) -> list[Station]:
    """Return all OSM fuel stations within radius_miles, nearest first."""
    radius_m = int(radius_miles * METERS_PER_MILE)
    query = (
        f"[out:json][timeout:{int(timeout) - 5}];"
        f"nwr(around:{radius_m},{lat},{lon})[amenity=fuel];"
        "out center;"
    )
    resp = requests.post(
        OVERPASS_URL,
        data={"data": query},
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    resp.raise_for_status()
    elements = resp.json().get("elements", [])
    stations = [s for e in elements if (s := _element_to_station(e, lat, lon))]
    stations.sort(key=lambda s: s.distance_miles)
    return stations
