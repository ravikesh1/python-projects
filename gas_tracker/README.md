# Gas Tracker

A CLI that finds every gas station near a location, attaches the best
available price for your fuel grade, and ranks them cheapest-first — with a
watch mode that refreshes continuously.

```
$ gas-tracker "Austin, TX" --fuel regular --radius 5

         Regular near Austin, Travis County, Texas (5 mi, 38 stations, 18:42:10)
 ┏━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━┓
 ┃ # ┃ Station     ┃ Address              ┃ Miles ┃ $/gal ┃ Price source  ┃
 ┡━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━┩
 │ 1 │ Costco      │ 4301 W William Can…  │   3.1 │  2.61 │ station (OSM) │
 │ 2 │ H-E-B Fuel  │ 2400 S Congress Ave  │   1.2 │  2.74 │ station (OSM) │
 │ 3 │ Shell       │ 1159 S Lamar Blvd    │   0.8 │  2.83 │ city avg      │
 ...
```

## Usage

```bash
uv run gas-tracker "Austin, TX"                  # city / address / zip
uv run gas-tracker 78704 --fuel diesel           # rank by diesel
uv run gas-tracker --lat 30.2672 --lon -97.7431  # exact coordinates
uv run gas-tracker "Austin, TX" --watch 300      # live: refresh every 5 min
uv run gas-tracker "Austin, TX" --radius 10 --limit 30
```

The cheapest station is highlighted in green. Stations with no price data
sort to the bottom but are still listed (you at least know they're there).

## Where the data comes from (and its limits)

| Layer | Source | Coverage |
| --- | --- | --- |
| Geocoding ("near me") | OSM Nominatim — free, no key | worldwide |
| Station locations | OSM Overpass API — free, no key | worldwide |
| Per-station prices | OSM `fuel:*:price` tags | sparse but exact |
| Area baseline prices | [CollectAPI gasPrice](https://collectapi.com/api/gasPrice) city/state averages | US, free tier, needs key |

**The honest caveat:** there is no free official API for true per-station US
gas prices. GasBuddy's data is crowd-sourced into their app only (no public
API), and commercial feeds (OPIS, etc.) are paid. So this tool shows exact
prices where OSM contributors have tagged them, and city/state averages
everywhere else — the `Price source` column tells you which you're looking
at. Station *locations* and *distances* are always real.

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
