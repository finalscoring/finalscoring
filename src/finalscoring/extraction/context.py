"""Building the message the model reads from a raw item.

The extraction step used to send `raw_text` alone, discarding the eleven other
populated fields on a `RawItem` — including the page's own title and site name,
while asking the model to name outlets.

Markup is kept rather than flattened because the tags carry the structure the
model was otherwise guessing at: `<p>` bounds one critic's passage, `<a href>`
makes a linked review visible at all, `<blockquote>` marks a quote as a quote.
None of that is specific to one source. Measured on the Spiel des Jahres
corpus, cleaning costs 1.12x the plain text — but that ratio holds because that
spider stores the article body, not a whole page. A spider that stores page
chrome should expect worse.

Where a spider has already read structured facts — the byline, a stated score,
the game's own metadata — they go in the `<source>` header and one `<review>`
block per (game, reviewer) the spider identified, so the model reads them
rather than re-deriving them from prose it may not contain.
"""

import re
from collections.abc import Iterator

from finalscoring.models import RatingDirection
from finalscoring.scraping.item import RawGameHint, RawItem, RawReviewHint, SourceRating

# Whole subtrees that carry nothing a reviewer wrote.
_DROP = re.compile(
    r"<(script|style|noscript|svg|form|nav|iframe|template)\b[^>]*>.*?</\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_TAG = re.compile(r"<([a-zA-Z0-9]+)((?:\s+[^>]*?)?)(/?)>")
_HREF = re.compile(r"""href\s*=\s*["']([^"']*)["']""", re.IGNORECASE)
_ALT = re.compile(r"""alt\s*=\s*["']([^"']*)["']""", re.IGNORECASE)
_BLANK_RUN = re.compile(r"\n{3,}")
_SPACE_RUN = re.compile(r"[ \t]{2,}")


def _strip_attributes(match: re.Match[str]) -> str:
    """Keep the tag, a link's target, and an image's alt. Class soup helps nobody."""
    tag, attrs, self_closing = match.group(1), match.group(2), match.group(3)
    name = tag.lower()
    href = _HREF.search(attrs)
    if href and name == "a":
        return f'<a href="{href.group(1)}">'
    alt = _ALT.search(attrs)
    if alt and name == "img" and alt.group(1).strip():
        return f'<img alt="{alt.group(1).strip()}">'
    return f"<{tag}{self_closing}>"


def clean_html(html: str) -> str:
    """Strip a page down to the structure and links worth spending tokens on."""
    html = _COMMENT.sub("", _DROP.sub("", html))
    html = _TAG.sub(_strip_attributes, html)
    lines = (line.strip() for line in html.split("\n"))
    return _BLANK_RUN.sub("\n\n", _SPACE_RUN.sub(" ", "\n".join(lines))).strip()


def _metadata(item: RawItem) -> Iterator[str]:
    # known_critic_name is a single-critic source's sole reviewer; bylines are
    # names the page itself credits. Either is a better answer than the masthead.
    byline = item.known_critic_name or ", ".join(item.bylines) or None
    for label, value in (
        ("url", item.url),
        ("title", item.title),
        ("site", item.site_name),
        ("byline", byline),
        ("medium", item.medium.value if item.medium else None),
        ("published", item.published_at.date().isoformat() if item.published_at else None),
        ("language", item.locale or item.language),
        ("tags", ", ".join(item.tags) or None),
        ("categories", ", ".join(item.categories) or None),
    ):
        if value:
            yield f"{label}: {value}"


def _num(value: float) -> str:
    """5.0 -> "5", 4.5 -> "4.5" — a rating reads better without the trailing zero."""
    return str(int(value)) if value == int(value) else str(value)


def _rating_line(rating: SourceRating) -> str:
    scope = rating.axis or rating.system.value
    if rating.value is not None:
        score = _num(rating.value) + (
            f"/{_num(rating.scale_max)}" if rating.scale_max is not None else ""
        )
        if rating.label:
            score = f"{score} — {rating.label}"
    else:
        score = rating.label or rating.verbatim or "(no value)"
    if rating.direction is RatingDirection.lower_is_better:
        score = f"{score} (lower is better)"
    return f"rating {scope}: {score}"


def _game_lines(game: RawGameHint) -> Iterator[str]:
    for label, value in (
        ("game", " / ".join(game.titles) or None),
        ("designers", ", ".join(game.designers) or None),
        ("publishers", ", ".join(game.publishers) or None),
        ("year", str(game.year_published) if game.year_published else None),
        ("bgg", game.bgg_url or (f"boardgame/{game.bgg_id}" if game.bgg_id else None)),
        ("complexity", game.complexity_label),
    ):
        if value:
            yield f"{label}: {value}"


def _review_lines(hint: RawReviewHint) -> Iterator[str]:
    for label, value in (
        ("critic", ", ".join(hint.critic_names) or None),
        ("outlet", hint.outlet_name),
        ("medium", hint.medium.value if hint.medium else None),
        ("published in", hint.published_in),
        ("review url", hint.review_url),
        ("published", hint.published_at.date().isoformat() if hint.published_at else None),
        ("language", hint.language),
    ):
        if value:
            yield f"{label}: {value}"
    if hint.game is not None:
        yield from _game_lines(hint.game)
    yield from (_rating_line(r) for r in hint.ratings)
    if hint.editorial_flags:
        yield f"editorial marks: {', '.join(hint.editorial_flags)}"
    if hint.note:
        yield f"note: {hint.note}"


def _reviews(item: RawItem) -> Iterator[str]:
    """One <review> block per (game, reviewer) the spider read from the page.

    Kept out of <source> because they are a list, not flat page metadata — a
    roundup states one per cited critic, a listicle one per game. For a
    meta-source the outlet, url and date here are the cited review's, not the
    page's.
    """
    for hint in item.reviews:
        if lines := list(_review_lines(hint)):
            yield "\n".join(("", "<review>", *lines, "</review>"))


def build_context(item: RawItem, *, markup: bool = True) -> str:
    """The user message for one raw item: what the page is, then what it says.

    The two are delimited because they are different kinds of claim — the
    metadata describes the page being read, which for a roundup is emphatically
    not where the cited critic published.
    """
    # Markup that cleans away to nothing was all chrome; the text is what is left.
    body = (clean_html(item.raw_html) if markup and item.raw_html else "") or item.raw_text
    return "\n".join(
        (
            "<source>",
            *_metadata(item),
            "</source>",
            *_reviews(item),
            "",
            "<article>",
            body,
            "</article>",
        )
    )
