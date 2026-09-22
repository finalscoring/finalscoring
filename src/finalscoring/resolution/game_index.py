"""An in-memory lookup over Recommend.Games' scraped BGG game data.

Reads `bgg_GameItem.jl` directly off disk (PROJECT.md, "Game data access
(D1)") rather than a shared database. Each line is a full BGG API record with
fields (`description`, `video_url`, image variants, ...) no resolver step
needs, so only the handful that matching cares about are kept per game;
everything else is dropped as the line is parsed rather than held in memory.
"""

import json
import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

_DESIGNER_SUFFIX = re.compile(r":\d+$")  # "Uwe Rosenberg:2" -> "Uwe Rosenberg"
_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")
_WHITESPACE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    """Fold a title down to a matching key: casefold, strip accents and punctuation.

    "Die Mächer" and "die maecher" typo aside, this is deliberately loose —
    candidates that collide here still get disambiguated by year and
    designer/publisher, so a slightly too-eager fold costs nothing.
    """
    decomposed = unicodedata.normalize("NFKD", title)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    folded = _NON_ALNUM.sub(" ", stripped.casefold())
    return _WHITESPACE.sub(" ", folded).strip()


def _strip_id_suffix(names: list[str]) -> list[str]:
    return [_DESIGNER_SUFFIX.sub("", name) for name in names]


@dataclass(frozen=True, slots=True)
class BggGame:
    """The subset of a `bgg_GameItem.jl` record that resolution needs."""

    bgg_id: int
    name: str
    alt_names: list[str] = field(default_factory=list)
    year_published: int | None = None
    designers: list[str] = field(default_factory=list)
    publishers: list[str] = field(default_factory=list)

    @property
    def titles(self) -> Iterator[str]:
        yield self.name
        yield from self.alt_names


def _parse_line(line: str) -> BggGame | None:
    raw = json.loads(line)
    bgg_id = raw.get("bgg_id")
    name = raw.get("name")
    if bgg_id is None or not name:
        return None
    return BggGame(
        bgg_id=bgg_id,
        name=name,
        alt_names=[n for n in raw.get("alt_name") or [] if n],
        year_published=raw.get("year"),
        designers=_strip_id_suffix(raw.get("designer") or []),
        publishers=_strip_id_suffix(raw.get("publisher") or []),
    )


@dataclass(frozen=True, slots=True)
class GameIndex:
    """Lookup by bgg_id and by normalized title (name + alt names combined)."""

    by_id: dict[int, BggGame]
    by_title: dict[str, list[int]]

    def candidates(self, title: str) -> list[BggGame]:
        return [self.by_id[bgg_id] for bgg_id in self.by_title.get(normalize_title(title), [])]

    @classmethod
    def load(cls, path: Path) -> GameIndex:
        by_id: dict[int, BggGame] = {}
        by_title: dict[str, list[int]] = {}
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                game = _parse_line(line)
                if game is None:
                    continue
                by_id[game.bgg_id] = game
                # alt_name commonly repeats name verbatim — dedupe per game so one
                # title doesn't make a single game look like two candidates.
                for normalized in dict.fromkeys(normalize_title(t) for t in game.titles):
                    by_title.setdefault(normalized, []).append(game.bgg_id)
        return cls(by_id=by_id, by_title=by_title)
