# Gas Tracker

A CLI that finds every gas station near a location (defaults to **Surrey, BC,
Canada**), attaches the best available price for your fuel grade, and ranks
them cheapest-first — with a watch mode that refreshes continuously.

```
$ gas-tracker

      Regular near Surrey, Metro Vancouver, British Columbia (5 km, 24 stations, 18:42:10)
 ┏━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━┓
 ┃ # ┃ Station      ┃ Address                ┃  km ┃  $/L ┃ Price source  ┃
 ┡━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━┩
 │ 1 │ Costco Gas   │ 7423 King George Blvd  │ 3.1 │ 1.54 │ station (OSM) │
 │ 2 │ Chevron      │ 10235 King George Blvd │ 1.2 │ 1.62 │ city avg      │
 │ 3 │ Petro-Canada │ 13565 104 Ave          │ 0.8 │ 1.62 │ city avg      │
 ...
```

## Usage

```bash
uv run gas-tracker                                  # Surrey, BC by default
uv run gas-tracker "Guildford, Surrey, BC"          # a specific neighbourhood
uv run gas-tracker "V3T 2W1"                        # postal code
uv run gas-tracker --fuel diesel --radius 8         # rank by diesel, 8 km out
uv run gas-tracker --lat 49.1913 --lon -122.8490    # exact coordinates
uv run gas-tracker --watch 300                      # live: refresh every 5 min
```

Canadian locations get km and CAD $/L automatically; US locations get miles
and $/gal. The cheapest station is highlighted in green. Stations with no
price data sort to the bottom but are still listed (you at least know
they're there).

## Where the data comes from (and its limits)

| Layer | Source | Coverage |
| --- | --- | --- |
| Geocoding ("near me") | OSM Nominatim — free, no key | worldwide |
| Station locations | OSM Overpass API — free, no key | worldwide |
| Per-station prices | OSM `fuel:*:price` tags | sparse but exact |
| Area baseline prices | [CollectAPI gasPrice](https://collectapi.com/api/gasPrice) — Canadian city averages, US city/state averages | needs key, free tier |

**The honest caveat:** there is no free official API for true per-station
gas prices in Canada or the US. GasBuddy's crowd-sourced data lives in their
app only (no public API), and commercial feeds (OPIS, Kalibrate) are paid.
So this tool shows exact prices where OSM contributors have tagged them, and
a Surrey-wide city average everywhere else — the `Price source` column tells
you which you're looking at. Station *locations* and *distances* are always
real and complete.

If you later get access to a per-station feed, `gas_tracker/prices.py` is
the seam: add a provider next to `CollectApiProvider` and prefer it in
`quote_station`.

## Setup

```bash
uv sync
cp .env.example .env   # then set COLLECTAPI_KEY for area price baselines
```

Without `COLLECTAPI_KEY` the tool still works; prices are just limited to
stations carrying OSM price tags.

## Etiquette

Nominatim and Overpass are free, community-run services. The tool geocodes
once per run, and watch mode enforces a 60-second minimum refresh interval.

## Tests

```bash
uv run pytest tests/
```

Tests are fully offline (HTTP is stubbed).
