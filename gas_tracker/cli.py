"""CLI: find nearby gas stations and rank them cheapest-first.

Examples:
    gas-tracker "Austin, TX"
    gas-tracker 78704 --fuel diesel --radius 8
    gas-tracker --lat 30.2672 --lon -97.7431 --watch 300
"""

from __future__ import annotations

import argparse
import sys
import time

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from .geo import GeocodeError, Place, geocode
from .prices import FUEL_KINDS, CollectApiProvider, quote_station
from .stations import find_stations

MIN_WATCH_SECONDS = 60  # be polite to the free Overpass servers


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gas-tracker",
        description="Find nearby gas stations and rank them by price.",
    )
    parser.add_argument("location", nargs="?", help='address, city, or zip (e.g. "Austin, TX")')
    parser.add_argument("--lat", type=float, help="latitude (alternative to a location string)")
    parser.add_argument("--lon", type=float, help="longitude (alternative to a location string)")
    parser.add_argument("--radius", type=float, default=5.0, help="search radius in miles (default 5)")
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
        parser.error("provide a location string, or both --lat and --lon")
    return args


def resolve_place(args: argparse.Namespace) -> Place:
    if args.lat is not None and args.lon is not None:
        return Place(lat=args.lat, lon=args.lon, display_name=f"{args.lat:.4f}, {args.lon:.4f}")
    return geocode(args.location)


def build_table(place: Place, args: argparse.Namespace, provider: CollectApiProvider) -> Table:
    stations = find_stations(place.lat, place.lon, radius_miles=args.radius)

    city_prices: dict[str, dict[str, float]] = {}
    if provider.available and place.state_code:
        try:
            city_prices = provider.state_prices(place.state_code)
        except Exception as exc:  # price feed failing shouldn't kill the station list
            Console(stderr=True).print(f"[yellow]price feed unavailable: {exc}[/yellow]")

    rows = []
    for station in stations:
        quote = quote_station(station, args.fuel, city_prices, place.city)
        rows.append((station, quote))
    # cheapest first, unpriced stations last (by distance within each group)
    rows.sort(key=lambda r: (r[1] is None, r[1].price if r[1] else 0, r[0].distance_miles))
    rows = rows[: args.limit]

    table = Table(
        title=f"{args.fuel.capitalize()} near {place.display_name} "
        f"({args.radius:g} mi, {len(stations)} stations, {time.strftime('%H:%M:%S')})"
    )
    table.add_column("#", justify="right")
    table.add_column("Station")
    table.add_column("Address")
    table.add_column("Miles", justify="right")
    table.add_column("$/gal", justify="right")
    table.add_column("Price source")

    cheapest = next((q.price for _, q in rows if q), None)
    for i, (station, quote) in enumerate(rows, 1):
        is_cheapest = quote is not None and quote.price == cheapest
        table.add_row(
            str(i),
            station.name,
            station.address or "—",
            f"{station.distance_miles:.1f}",
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
