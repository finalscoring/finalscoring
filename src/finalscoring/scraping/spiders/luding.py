"""Spider for the review links in the Recommend.Games scrape of luding.org.

luding.org is a board-game database that, for ~21,500 of its ~37,000 games,
lists links to third-party reviews - about 68,000 links across ~190 hosts, most
of them small German fan sites with no spider of their own. Recommend.Games
scrapes luding into `luding_GameItem.jl`; this spider reads the `review_url`
column of that file and hands each link to `ReviewLinksSpider` for generic
extraction.

The game a link sits next to - name, year, designers, publishers, and a
`bgg_id` for the ~5% that have one - becomes a `RawGameHint` on a review hint
via `row_game`. A `bgg_id` there settles the game match outright; the rest is
match evidence for the resolution step. The raw row still rides along in
`extra["source_rows"]`. One link can be listed by several games (a base game
and its expansion), so one page can carry several hints.

`files` is deliberately unset. Where the luding scrape lives is a
Recommend.Games integration question the project has not settled, so the path is
given at run time: `-a files=<path/to/luding_GameItem.jl>`. JOBDIR remembers
every fetched URL, so a re-run picks up only links luding has added since - and
equally does not retry a link that was dead the first time.
"""

from datetime import date
from typing import Any

from finalscoring.scraping.item import RawGameHint
from finalscoring.scraping.spiders.review_links import ReviewLinksSpider


def _names(value: Any) -> list[str]:
    """A luding row field is a list, a scalar, or None."""
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return [text for v in values if (text := str(v).strip())]


class LudingSpider(ReviewLinksSpider):
    name = "luding"

    url_column = "review_url"
    context_fields = (
        "name",
        "year",
        "designer",
        "publisher",
        "artist",
        "game_type",
        "bgg_id",
        "luding_id",
        "url",
    )

    def row_game(self, row: dict[str, Any]) -> RawGameHint | None:
        name = str(row["name"]).strip() if row.get("name") else None
        designers = _names(row.get("designer"))
        publishers = _names(row.get("publisher"))
        bgg_id = row["bgg_id"] if isinstance(row.get("bgg_id"), int) else None
        if not (name or designers or publishers or bgg_id):
            return None

        year = row.get("year")
        year = year if isinstance(year, int) and 1900 <= year <= date.today().year + 2 else None
        external_ids: dict[str, str] = {}
        if row.get("luding_id") is not None:
            external_ids["luding_id"] = str(row["luding_id"])
        if row.get("url"):
            external_ids["luding_url"] = str(row["url"])

        return RawGameHint(
            titles=[name] if name else [],
            designers=designers,
            publishers=publishers,
            artists=_names(row.get("artist")),
            categories=_names(row.get("game_type")),
            year_published=year,
            bgg_id=bgg_id,
            external_ids=external_ids,
            source="luding row",
        )
