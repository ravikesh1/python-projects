"""CLI: find nearby gas stations and rank them cheapest-first.

Examples:
    gas-tracker                          # defaults to Surrey, BC
    gas-tracker "Guildford, Surrey, BC" --fuel diesel --radius 8
    gas-tracker --lat 49.1913 --lon -122.8490 --watch 300
"""

from __future__ import annotations

import argparse
import sys
import time

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from .geo import KM_PER_MILE, GeocodeError, Place, geocode
from .prices import FUEL_KINDS, CollectApiProvider, area_prices, quote_station
from .stations import find_stations

DEFAULT_LOCATION = "Surrey, BC, Canada"
MIN_WATCH_SECONDS = 60  # be polite to the free Overpass servers


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gas-tracker",
        description="Find nearby gas stations and rank them by price.",
    )
    parser.add_argument(
        "location",
        nargs="?",
        help=f'address, neighbourhood, or postal code (default: "{DEFAULT_LOCATION}")',
    )
    parser.add_argument("--lat", type=float, help="latitude (alternative to a location string)")
    parser.add_argument("--lon", type=float, help="longitude (alternative to a location string)")
    parser.add_argument(
        "--radius",
        type=float,
        default=5.0,
        help="search radius — km in Canada, miles in the US (default 5)",
    )
    parser.add_argument("--fuel", choices=FUEL_KINDS, default="regular", help="fuel grade to rank by")
    parser.add_argument("--limit", type=int, default=20, help="max stations to show (default 20)")
    parser.add_argument(
        "--watch",
        type=int,
        metavar="SECONDS",
        help=f"refresh continuously every N seconds (min {MIN_WATCH_SECONDS})",
    )
    args = parser.parse_args(argv)
    if args.location is None and (args.lat is None or args.lon is None):
        args.location = DEFAULT_LOCATION
    return args


def resolve_place(args: argparse.Namespace) -> Place:
    if args.lat is not None and args.lon is not None:
        return Place(lat=args.lat, lon=args.lon, display_name=f"{args.lat:.4f}, {args.lon:.4f}")
    return geocode(args.location)


def is_metric(place: Place) -> bool:
    """Everywhere except the US gets km and $/L; bare coordinates default to metric."""
    return place.country_code != "us"


def build_table(place: Place, args: argparse.Namespace, provider: CollectApiProvider) -> Table:
    metric = is_metric(place)
    radius_miles = args.radius / KM_PER_MILE if metric else args.radius
    stations = find_stations(place.lat, place.lon, radius_miles=radius_miles)

    city_prices: dict[str, dict[str, float]] = {}
    try:
        city_prices = area_prices(provider, place)
    except Exception as exc:  # price feed failing shouldn't kill the station list
        Console(stderr=True).print(f"[yellow]price feed unavailable: {exc}[/yellow]")

    rows = []
    for station in stations:
        quote = quote_station(station, args.fuel, city_prices, place.city)
        rows.append((station, quote))
    # cheapest first, unpriced stations last (by distance within each group)
    rows.sort(key=lambda r: (r[1] is None, r[1].price if r[1] else 0, r[0].distance_miles))
    rows = rows[: args.limit]

    radius_unit = "km" if metric else "mi"
    table = Table(
        title=f"{args.fuel.capitalize()} near {place.display_name} "
        f"({args.radius:g} {radius_unit}, {len(stations)} stations, {time.strftime('%H:%M:%S')})"
    )
    table.add_column("#", justify="right")
    table.add_column("Station")
    table.add_column("Address")
    table.add_column("km" if metric else "Miles", justify="right")
    table.add_column("$/L" if metric else "$/gal", justify="right")
    table.add_column("Price source")

    cheapest = next((q.price for _, q in rows if q), None)
    for i, (station, quote) in enumerate(rows, 1):
        is_cheapest = quote is not None and quote.price == cheapest
        distance = station.distance_miles * KM_PER_MILE if metric else station.distance_miles
        table.add_row(
            str(i),
            station.name,
            station.address or "—",
            f"{distance:.1f}",
            f"{quote.price:.2f}" if quote else "—",
            quote.source if quote else "no data",
            style="bold green" if is_cheapest else None,
        )
    return table


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = parse_args(argv)
    console = Console()
    provider = CollectApiProvider()

    try:
        place = resolve_place(args)
    except GeocodeError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1

    if not provider.available:
        console.print(
            "[dim]No COLLECTAPI_KEY set — prices limited to stations with OSM price tags. "
            "See gas_tracker/README.md.[/dim]"
        )

    if args.watch is None:
        console.print(build_table(place, args, provider))
        return 0

    interval = max(args.watch, MIN_WATCH_SECONDS)
    if interval != args.watch:
        console.print(f"[dim]watch interval raised to {interval}s (Overpass etiquette)[/dim]")
    try:
        while True:
            console.clear()
            console.print(build_table(place, args, provider))
            console.print(f"[dim]refreshing every {interval}s — Ctrl-C to stop[/dim]")
            time.sleep(interval)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
