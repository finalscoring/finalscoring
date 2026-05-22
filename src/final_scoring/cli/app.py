"""``fs`` command-line interface.

Sub-commands:

* ``fs db init``        — materialize an empty schema.
* ``fs scrape <name>``  — run a single spider.
* ``fs build``          — run a full build end-to-end.
* ``fs serve``          — serve the built database (placeholder).
"""

from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from final_scoring import __version__
from final_scoring.build import run_build
from final_scoring.config import get_settings
from final_scoring.schema.init_db import init_db

console = Console()

app = typer.Typer(
    help="Final Scoring — board game critic index. See `fs <command> --help`.",
    add_completion=False,
    no_args_is_help=True,
)
db_app = typer.Typer(help="Database management.", no_args_is_help=True)
app.add_typer(db_app, name="db")


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )


# ─────────────────────────────────────────────────────────────────────────
# Top-level
# ─────────────────────────────────────────────────────────────────────────


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable debug logging."
    ),
) -> None:
    """Root callback. Sets up logging for all subcommands."""

    _setup_logging(verbose)


@app.command()
def version() -> None:
    """Print the package version."""

    console.print(f"final_scoring {__version__}")


# ─────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────


@db_app.command("init")
def db_init(
    path: Path = typer.Option(
        None,
        "--path",
        help="SQLite path. Defaults to FS_DB_PATH from env.",
    ),
    drop_existing: bool = typer.Option(
        False,
        "--drop-existing",
        help="Delete the file first if it exists.",
    ),
) -> None:
    """Materialize the Final Scoring schema."""

    target = path or get_settings().build.db_path
    init_db(target, drop_existing=drop_existing)
    console.print(f"[green]Schema initialized at[/green] {target}")


# ─────────────────────────────────────────────────────────────────────────
# Scrape
# ─────────────────────────────────────────────────────────────────────────


@app.command()
def scrape(
    name: str = typer.Argument(..., help="Spider name (e.g. 'sdj')."),
    limit: int | None = typer.Option(
        None,
        "--limit",
        help="Stop after this many items. Useful for development runs.",
    ),
) -> None:
    """Run one spider.

    Dispatches to the Scrapy ``CrawlerProcess`` so that the same code
    path serves dev runs and CI rebuilds.
    """

    # Local import — Scrapy is heavy and shouldn't load on every CLI invocation.
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    from final_scoring.scraping.spiders import spiel_des_jahres  # noqa: F401

    spider_classes = _discover_spiders()
    if name not in spider_classes:
        available = ", ".join(sorted(spider_classes)) or "<none registered>"
        raise typer.BadParameter(
            f"Unknown spider '{name}'. Available: {available}"
        )

    spider_cls = spider_classes[name]
    settings = get_project_settings()
    if limit is not None:
        settings.set("CLOSESPIDER_ITEMCOUNT", limit, priority="cmdline")

    process = CrawlerProcess(settings=settings)
    process.crawl(spider_cls)
    process.start()


def _discover_spiders() -> dict[str, type]:
    """Find Spider subclasses with a ``name`` attribute under spiders/.

    Cheap reflective lookup — no plugin system, no entry points. Add a
    new spider by importing its module in
    ``final_scoring/scraping/spiders/__init__.py`` or directly above.
    """

    from final_scoring.scraping.spiders import spiel_des_jahres

    return {
        spiel_des_jahres.SpielDesJahresSpider.name: spiel_des_jahres.SpielDesJahresSpider,
    }


# ─────────────────────────────────────────────────────────────────────────
# Build
# ─────────────────────────────────────────────────────────────────────────


@app.command()
def build(
    db_path: Path | None = typer.Option(
        None, "--db-path", help="Override the configured DB path."
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Treat any build-time warning as fatal. Used in CI/Docker.",
    ),
) -> None:
    """Run a full build: schema → import → load → score → vacuum."""

    report = run_build(db_path=db_path, strict=strict)

    table = Table(title="Build report", show_header=False)
    table.add_row("Database", str(report.db_path))
    table.add_row("Games imported", str(report.games_imported))
    table.add_row("Critics loaded", str(report.critics_loaded))
    table.add_row("Reviews loaded", str(report.reviews_loaded))
    table.add_row("Aggregates written", str(report.aggregates_written))
    table.add_row("Warnings", str(len(report.warnings)))
    console.print(table)

    if report.warnings:
        console.print("[yellow]Warnings:[/yellow]")
        for w in report.warnings:
            console.print(f"  • {w}")


# ─────────────────────────────────────────────────────────────────────────
# Serve (placeholder — real implementation lands with the frontend)
# ─────────────────────────────────────────────────────────────────────────


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
) -> None:
    """Serve the built database. Placeholder until the frontend exists."""

    console.print(
        f"[yellow]serve is not yet implemented.[/yellow] "
        f"Would listen on {host}:{port}."
    )
    raise typer.Exit(code=1)
