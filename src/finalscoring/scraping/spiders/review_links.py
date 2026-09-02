"""Spider that fetches review URLs listed in a data file and extracts each generically.

Every other spider knows one site. This one knows none. It reads a column of
review URLs out of a `.jl` or `.csv` file - the shape sites like luding.org and
the Recommend.Games scrape publish - fetches each URL, and runs trafilatura over
whatever comes back. One page's markup is nothing like the next's, so there is no
structural parsing here: stripping boilerplate and guessing the main text is the
extractor's job, and turning that text into a score is the LLM step's.

`raw_html` is trafilatura's reconstruction of the article - the main content with
the nav, sidebar, footer, and comments removed - not the page as fetched. Storing
the whole page would be an order of magnitude more bytes for markup nobody reads
back.

A meta-source in the Spiel des Jahres sense - `outlet_slug` stays unset, because
the outlet is whoever runs the page at the far end of the link, not something
this spider fetched. The far-end host and the file row that pointed here go into
`extra` for the load step to resolve; for the ~95% of links with no `bgg_id`,
that row is the only signal for which game the review is about, so its game name
is also folded into `tags`, where the model sees it.

Not runnable on its own: it has no `files` to read. A source subclasses it,
setting `files`, `url_column`, and which row fields to carry.
"""

import csv
import json
from collections.abc import AsyncIterator, Iterator
from glob import glob
from os.path import expanduser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from scrapy import Request, Spider
from scrapy.http.response import Response
from scrapy.http.response.text import TextResponse
from scrapy.utils.misc import arg_to_iter
from trafilatura import bare_extraction
from trafilatura.htmlprocessing import build_html_output
from trafilatura.settings import Document
from twisted.python.failure import Failure

from finalscoring.scraping.item import RawItem, language_from_locale
from finalscoring.scraping.spider import ReviewSpider
from finalscoring.scraping.timestamps import as_utc

_JSONL_SUFFIXES = (".jl", ".jsonl", ".ndjson")


def covered_domains() -> frozenset[str]:
    """Hosts a dedicated spider already handles: the union of every registered
    spider's `allowed_domains`. Derived rather than hand-listed so a new spider
    cannot leave a generic pass silently shadowing it with a lower-fidelity copy.
    Delegating such links to the dedicated parser instead of skipping them is
    possible later - the per-page parsers take a bare Response - but out of scope.
    """
    from finalscoring.scraping import spiders

    return frozenset(
        domain
        for obj in vars(spiders).values()
        if isinstance(obj, type)
        and issubclass(obj, Spider)
        and not issubclass(obj, ReviewLinksSpider)
        for domain in (getattr(obj, "allowed_domains", None) or ())
    )


def has_dedicated_spider(netloc: str, covered: frozenset[str] | None = None) -> bool:
    """True when `netloc` is, or is a subdomain of, a host a dedicated spider covers."""
    domains = covered_domains() if covered is None else covered
    host = netloc.lower().split(":", 1)[0]
    return any(host == d or host.endswith(f".{d}") for d in domains)


def iter_rows(path: Path) -> Iterator[dict[str, Any]]:
    """Yield each record of a `.jl`/`.jsonl`/`.ndjson` or `.csv` file as a dict."""
    suffix = path.suffix.lower()
    if suffix in _JSONL_SUFFIXES:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if stripped := line.strip():
                    yield json.loads(stripped)
    elif suffix == ".csv":
        with path.open(encoding="utf-8", newline="") as handle:
            yield from csv.DictReader(handle)
    else:
        raise ValueError(f"unsupported file type {path.suffix!r}: {path}")


def iter_urls(value: Any) -> Iterator[str]:
    """A column cell is one URL or a list of them; keep the http(s) ones, sans fragment."""
    for item in arg_to_iter(value):
        if isinstance(item, str) and (stripped := item.strip()).startswith(("http://", "https://")):
            yield stripped.split("#", 1)[0]


class ReviewLinksSpider(ReviewSpider):
    name = "review-links"

    # No allowed_domains: the links point anywhere, and OffsiteMiddleware would
    # otherwise drop every request this spider makes.

    files: tuple[str, ...] | str = ()
    url_column: str = "review_url"
    # Row fields kept in extra["source_rows"]; None keeps every field but url_column.
    context_fields: tuple[str, ...] | None = None
    # Row fields whose values are folded into RawItem.tags (the game name, so the
    # model can match a review with no bgg_id to a game).
    tag_fields: tuple[str, ...] = ()

    async def start(self) -> AsyncIterator[Request]:
        targets = self._collect()
        self.logger.info(
            "%d distinct review URL(s) from %d file row(s); %d skipped as covered by a dedicated spider",
            len(targets),
            self._rows_read,
            len(self._covered),
        )
        for url, rows in targets.items():
            yield Request(
                url,
                callback=self.parse_review,
                cb_kwargs={"rows": rows},
                errback=self.fetch_failed,
            )

    def _files(self) -> Iterator[Path]:
        spec = self.files.split(",") if isinstance(self.files, str) else self.files
        if not spec:
            self.logger.error("%s has no files to read - pass -a files=<path>", self.name)
        for entry in spec:
            if not (cleaned := str(entry).strip()):
                continue
            matches = sorted(glob(expanduser(cleaned)))
            if not matches:
                self.logger.warning("no file matches %r", cleaned)
            for match in matches:
                yield Path(match)

    def _collect(self) -> dict[str, list[dict[str, Any]]]:
        targets: dict[str, list[dict[str, Any]]] = {}
        self._rows_read = 0
        self._covered: set[str] = set()
        covered = covered_domains()
        for path in self._files():
            for row in iter_rows(path):
                self._rows_read += 1
                context = self._context(row)
                for url in iter_urls(row.get(self.url_column)):
                    if has_dedicated_spider(urlparse(url).netloc, covered):
                        self._covered.add(url)
                    else:
                        targets.setdefault(url, []).append(context)
        return targets

    def _context(self, row: dict[str, Any]) -> dict[str, Any]:
        if self.context_fields is None:
            return {key: value for key, value in row.items() if key != self.url_column}
        keep = set(self.context_fields) | set(self.tag_fields)
        return {key: row[key] for key in keep if key in row}

    def _tags(self, rows: list[dict[str, Any]]) -> list[str]:
        tags: list[str] = []
        for row in rows:
            for field in self.tag_fields:
                for value in arg_to_iter(row.get(field)):
                    if (text := str(value).strip()) and text not in tags:
                        tags.append(text)
        return tags

    def parse_review(
        self,
        response: Response,
        rows: list[dict[str, Any]],
    ) -> tuple[RawItem] | None:
        if not isinstance(response, TextResponse):
            self.logger.error("non-text response from %s", response.url)
            return None

        try:
            document = bare_extraction(
                response.text,
                url=response.url,
                include_comments=False,  # reader comments and ratings are not critic opinion
                include_tables=True,
                include_formatting=True,  # keeps headings - a "Fazit"/"Verdict" section is a cue
                with_metadata=True,
            )
        except Exception:
            self.logger.exception("extraction raised for %s", response.url)
            return None

        if not isinstance(document, Document) or not (raw_text := (document.text or "").strip()):
            self.logger.warning("no article text extracted from %s", response.url)
            return None

        locale = (
            response.xpath("//html/@lang").get()
            or response.xpath("//meta[@property='og:locale']/@content").get()
        )

        return (
            RawItem(
                url=response.url,
                spider_slug=self.name,
                raw_text=raw_text,
                raw_html=build_html_output(document, with_metadata=False),
                # outlet_slug left unset: the outlet is the host, resolved downstream.
                title=document.title or None,
                description=document.description or None,
                # htmldate hands back a bare day-string; read it as UTC.
                published_at=as_utc(document.date),
                language=language_from_locale(locale),
                locale=locale,
                image_url=document.image or None,
                tags=self._tags(rows),
                og_site_name=document.sitename or None,
                extra={
                    "host": urlparse(response.url).netloc,
                    "source_rows": rows,
                    "trafilatura": {
                        "author": document.author,
                        "date": document.date,
                        "sitename": document.sitename,
                        "categories": document.categories or [],
                        "tags": document.tags or [],
                    },
                },
            ),
        )

    def fetch_failed(self, failure: Failure) -> None:
        request = failure.request  # ty: ignore[unresolved-attribute]
        self.logger.warning("fetch failed for %s: %s", request.url, failure.value)
