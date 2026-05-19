"""Typer CLI for importing orders and viewing stats."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from . import analytics
from .db import init_db, make_engine, make_session_factory, session_scope
from .importers import import_csv, import_eml, import_json

app = typer.Typer(help="Personal Uber Eats order tracker.")
console = Console()


def _open_session(db_url: Optional[str]):
    engine = make_engine(db_url)
    init_db(engine)
    return make_session_factory(engine)


@app.command(name="import")
def import_cmd(
    path: Path = typer.Argument(..., exists=True, readable=True),
    fmt: str = typer.Option(
        "auto", "--format", "-f", help="csv, json, eml, or auto (by extension)"
    ),
    db_url: Optional[str] = typer.Option(None, "--db-url", envvar="UBEREATS_DB_URL"),
) -> None:
    """Import orders from a CSV, JSON, or .eml file."""
    factory = _open_session(db_url)
    if fmt == "auto":
        suffix = path.suffix.lower().lstrip(".")
        fmt = {"csv": "csv", "json": "json", "eml": "eml"}.get(suffix, "")
        if not fmt:
            raise typer.BadParameter(f"Cannot infer format from {path.suffix}")
    importer = {"csv": import_csv, "json": import_json, "eml": import_eml}[fmt]
    with session_scope(factory) as session:
        result = importer(session, path)
    console.print(
        f"[green]Imported[/green] from {path.name}: "
        f"created={result['created']}, updated={result['updated']}"
    )


@app.command(name="list")
def list_cmd(
    limit: int = typer.Option(20, "--limit", "-n"),
    db_url: Optional[str] = typer.Option(None, "--db-url", envvar="UBEREATS_DB_URL"),
) -> None:
    """List recent orders."""
    from sqlalchemy import select

    from .models import Order

    factory = _open_session(db_url)
    table = Table(title="Recent orders")
    table.add_column("Date")
    table.add_column("Restaurant")
    table.add_column("Status")
    table.add_column("Total", justify="right")
    table.add_column("Tip %", justify="right")
    with session_scope(factory) as session:
        rows = (
            session.execute(
                select(Order).order_by(Order.ordered_at.desc()).limit(limit)
            )
            .scalars()
            .all()
        )
        for o in rows:
            table.add_row(
                o.ordered_at.strftime("%Y-%m-%d %H:%M"),
                o.restaurant.name,
                o.status,
                f"${o.total_cents / 100:.2f}",
                f"{o.tip_pct:.1f}%",
            )
    console.print(table)


@app.command(name="stats")
def stats_cmd(
    db_url: Optional[str] = typer.Option(None, "--db-url", envvar="UBEREATS_DB_URL"),
) -> None:
    """Show summary stats."""
    factory = _open_session(db_url)
    with session_scope(factory) as session:
        s = analytics.summary(session)
        top_r = analytics.top_restaurants(session, limit=5)
        top_i = analytics.top_items(session, limit=5)

    console.print(f"[bold]Orders:[/bold] {s.order_count}")
    console.print(f"[bold]Total spend:[/bold] ${s.total_cents / 100:.2f}")
    console.print(f"[bold]Avg order:[/bold] ${s.avg_order_cents / 100:.2f}")
    console.print(f"[bold]Avg tip:[/bold] {s.avg_tip_pct:.1f}%")
    console.print(f"[bold]Fees paid:[/bold] ${s.fees_cents / 100:.2f}")
    console.print(f"[bold]Tax paid:[/bold] ${s.tax_cents / 100:.2f}")

    if top_r:
        t = Table(title="Top restaurants")
        t.add_column("Restaurant")
        t.add_column("Orders", justify="right")
        t.add_column("Spend", justify="right")
        for r in top_r:
            t.add_row(r.label, str(r.order_count), f"${r.total_cents / 100:.2f}")
        console.print(t)

    if top_i:
        t = Table(title="Top items")
        t.add_column("Item")
        t.add_column("Qty", justify="right")
        t.add_column("Spend", justify="right")
        for i in top_i:
            t.add_row(i.label, str(i.order_count), f"${i.total_cents / 100:.2f}")
        console.print(t)


@app.command(name="serve")
def serve_cmd(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
    db_url: Optional[str] = typer.Option(None, "--db-url", envvar="UBEREATS_DB_URL"),
) -> None:
    """Run the dashboard web server."""
    import uvicorn

    if db_url:
        import os

        os.environ["UBEREATS_DB_URL"] = db_url
    uvicorn.run("ubereats_tracker.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
