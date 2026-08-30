"""Spider for the review links in the Recommend.Games scrape of luding.org.

luding.org is a board-game database that, for ~21,500 of its ~37,000 games,
lists links to third-party reviews - about 68,000 links across ~190 hosts, most
of them small German fan sites with no spider of their own. Recommend.Games
scrapes luding into `luding_GameItem.jl`; this spider reads the `review_url`
column of that file and hands each link to `ReviewLinksSpider` for generic
extraction.

The game a link sits next to - name, year, designers, publishers, and a
`bgg_id` for the ~5% that have one - rides along in `extra["source_rows"]`, and
the name also into `tags`: for a review with no `bgg_id` that row is the only
thing tying the page to a game.

`files` is deliberately unset. Where the luding scrape lives is a
Recommend.Games integration question the project has not settled, so the path is
given at run time: `-a files=<path/to/luding_GameItem.jl>`. JOBDIR remembers
every fetched URL, so a re-run picks up only links luding has added since - and
equally does not retry a link that was dead the first time.
"""

from finalscoring.scraping.spiders.review_links import ReviewLinksSpider


class LudingSpider(ReviewLinksSpider):
    name = "luding"

    url_column = "review_url"
    tag_fields = ("name",)
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
