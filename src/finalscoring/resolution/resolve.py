"""Title-plus-metadata -> BGG id resolution (D1).

A cascade, each step tried only when the previous one didn't produce a
confident answer:

1. `bgg_url`, when the extractor found one — `ExtractedGame.bgg_url_or_nothing`
   already rejected anything not hosted on boardgamegeek.com, so a bgg_id
   parsed out of it settles the match outright (the docstring on
   `ExtractedGame` says as much). Trusted even when the id isn't in the
   local `GameIndex` snapshot — a stale/incomplete `bgg_GameItem.jl` should
   not downgrade a good match to unresolved. Confirmed with the maintainer
   2026-09-22; D2 will need to handle a resolved bgg_id with no local
   metadata to build a `Game` row from.
2. Normalized-title lookup against `GameIndex` (name + alt names). A single
   candidate resolves.
3. Multiple candidates: narrow by exact `year_published`, then by
   designer/publisher name overlap. Only an unambiguous winner resolves.

Anything the cascade can't settle comes back `UNRESOLVED_NO_CANDIDATES` or
`UNRESOLVED_AMBIGUOUS` rather than a guess — a manual override path for these
misses is deliberately out of scope here; it needs its own decision about
storage format (see DECISIONS_OPEN.md) and is a separate, smaller chunk once
real miss data exists.
"""

import re
from dataclasses import dataclass
from enum import Enum

from finalscoring.extraction.schema import ExtractedGame
from finalscoring.resolution.game_index import BggGame, GameIndex, normalize_title

_BGG_URL_ID = re.compile(r"/boardgame(?:expansion)?/(\d+)")


class ResolutionReason(Enum):
    bgg_url = "bgg_url"
    unique_title = "unique_title"
    disambiguated_by_year = "disambiguated_by_year"
    disambiguated_by_credits = "disambiguated_by_credits"
    unresolved_no_candidates = "unresolved_no_candidates"
    unresolved_ambiguous = "unresolved_ambiguous"


@dataclass(frozen=True, slots=True)
class Resolution:
    """The outcome of resolving one `ExtractedGame`. `bgg_id` is set iff resolved."""

    bgg_id: int | None
    reason: ResolutionReason
    candidate_count: int = 0


def _bgg_id_from_url(url: str) -> int | None:
    match = _BGG_URL_ID.search(url)
    return int(match.group(1)) if match else None


def _by_year(extracted: ExtractedGame, candidates: list[BggGame]) -> list[BggGame]:
    if extracted.year_published is None:
        return candidates
    matches = [c for c in candidates if c.year_published == extracted.year_published]
    return matches or candidates


def _by_credits(extracted: ExtractedGame, candidates: list[BggGame]) -> list[BggGame]:
    wanted = {normalize_title(n) for n in (*extracted.designers, *extracted.publishers)}
    if not wanted:
        return candidates
    scored = [
        (c, len(wanted & {normalize_title(n) for n in (*c.designers, *c.publishers)}))
        for c in candidates
    ]
    best_score = max(score for _, score in scored)
    if best_score == 0:
        return candidates
    return [c for c, score in scored if score == best_score]


def resolve_game(extracted: ExtractedGame, index: GameIndex) -> Resolution:
    """Resolve one extracted game mention to a canonical BGG id, or explain why not."""
    if extracted.bgg_url is not None:
        bgg_id = _bgg_id_from_url(extracted.bgg_url)
        if bgg_id is not None:
            return Resolution(bgg_id=bgg_id, reason=ResolutionReason.bgg_url)

    candidates = index.candidates(extracted.title)
    if not candidates:
        return Resolution(bgg_id=None, reason=ResolutionReason.unresolved_no_candidates)
    if len(candidates) == 1:
        return Resolution(bgg_id=candidates[0].bgg_id, reason=ResolutionReason.unique_title)

    by_year = _by_year(extracted, candidates)
    if len(by_year) == 1:
        return Resolution(bgg_id=by_year[0].bgg_id, reason=ResolutionReason.disambiguated_by_year)

    by_credits = _by_credits(extracted, by_year)
    if len(by_credits) == 1:
        return Resolution(
            bgg_id=by_credits[0].bgg_id, reason=ResolutionReason.disambiguated_by_credits
        )

    return Resolution(
        bgg_id=None,
        reason=ResolutionReason.unresolved_ambiguous,
        candidate_count=len(by_credits),
    )
