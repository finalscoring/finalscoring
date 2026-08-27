"""Run extraction by hand: `uv run python -m finalscoring.extraction INPUT.jl...`.

Reads the `RawItem` JSON Lines a spider produced, asks the model what reviews
each one contains, and appends one `ExtractionRecord` line per item.

At roughly a minute per item against a local model a full pass runs for hours,
so it will get interrupted. Every record is flushed as it lands and sources
already present in the output directory are skipped, which makes re-running the
same command resume rather than restart.
"""

import argparse
import json
import logging
import sys
import time
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime
from itertools import islice
from pathlib import Path
from typing import TextIO

from pydantic import ValidationError

from finalscoring.extraction.llm import ExtractionFailed, ReviewExtractor
from finalscoring.scraping.item import RawItem
from finalscoring.settings import Settings, load_settings

LOGGER = logging.getLogger(__name__)


def default_output(settings: Settings) -> Path:
    """A fresh file per run, in its own directory under the results dir.

    Deliberately not alongside the raw items: the load step finds those by
    globbing, and an extraction record is not a raw item.
    """
    stamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace(":", "-")
    return settings.results_dir / "extraction" / f"extraction-{stamp}.jl"


def _source_url(line: str) -> str | None:
    """One output line's `source_url`, or None if it isn't one.

    Not model_validate_json: a later schema change must not make older output
    unreadable and so restart a finished run.
    """
    try:
        return json.loads(line).get("source_url")
    except json.JSONDecodeError, AttributeError:
        return None


def _lines(paths: Iterable[Path]) -> Iterator[str]:
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            yield from handle


def extracted_sources(directory: Path) -> set[str]:
    """Source URLs covered by the extraction files already in `directory`."""
    return {
        source_url
        for line in _lines(sorted(directory.glob("*.jl")))
        if (source_url := _source_url(line))
    }


def read_items(paths: Iterable[Path]) -> Iterator[RawItem]:
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    yield RawItem.model_validate_json(line)
                except ValidationError as exc:
                    LOGGER.warning("%s:%d is not a raw item, skipping: %s", path, number, exc)


def pending_items(items: Iterable[RawItem], done: Iterable[str]) -> Iterator[RawItem]:
    """The items still to extract, each source only once.

    Globbing two crawls of one spider yields the same URLs twice, which would
    otherwise double a multi-hour run.
    """
    seen = set(done)
    for item in items:
        if item.url not in seen:
            seen.add(item.url)
            yield item


def run(
    inputs: Iterable[Path],
    output: Path,
    extractor: ReviewExtractor,
    limit: int | None = None,
    force: bool = False,
) -> int:
    """Extract every raw item not already done. Returns the number of failures."""
    output.parent.mkdir(parents=True, exist_ok=True)
    done = set() if force else extracted_sources(output.parent)

    # Materialised for the progress denominator; the work itself is the slow part.
    pending = list(islice(pending_items(read_items(inputs), done), limit))

    LOGGER.info(
        "%d item(s) to extract, %d already extracted -> %s", len(pending), len(done), output
    )

    failures = 0
    handle: TextIO | None = None
    try:
        for index, item in enumerate(pending, start=1):
            started = time.monotonic()
            try:
                record = extractor.extract(item)
            except ExtractionFailed as exc:
                # One unextractable page must not cost the other ninety-two.
                failures += 1
                LOGGER.error("[%d/%d] %s: %s", index, len(pending), item.url, exc)
                continue

            if handle is None:
                handle = output.open("a", encoding="utf-8")
            handle.write(record.model_dump_json() + "\n")
            handle.flush()  # an interrupted run has to keep what it finished

            LOGGER.info(
                "[%d/%d] %s: %d review(s) in %.1fs",
                index,
                len(pending),
                item.url,
                len(record.result.reviews),
                time.monotonic() - started,
            )
    finally:
        if handle is not None:
            handle.close()

    if failures:
        LOGGER.error("%d of %d item(s) failed", failures, len(pending))
    return failures


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m finalscoring.extraction",
        description="Extract reviews from scraped raw items with the configured model.",
    )
    parser.add_argument(
        "inputs", nargs="+", type=Path, metavar="INPUT.jl", help="JSON Lines of raw items"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="file to append records to (default: a fresh one under FS_RESULTS_DIR/extraction)",
    )
    parser.add_argument("-n", "--limit", type=int, help="stop after this many new extractions")
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-extract sources already covered by the output directory",
    )
    args = parser.parse_args(argv)

    missing = [str(path) for path in args.inputs if not path.is_file()]
    if missing:
        parser.error(f"no such file: {', '.join(missing)}")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    settings = load_settings()
    output = args.output if args.output is not None else default_output(settings)
    failures = run(
        args.inputs,
        output,
        ReviewExtractor(settings),
        limit=args.limit,
        force=args.force,
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
