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
"""

import re
from collections.abc import Iterator

from finalscoring.scraping.item import RawItem

# Whole subtrees that carry nothing a reviewer wrote.
_DROP = re.compile(
    r"<(script|style|noscript|svg|form|nav|iframe|template)\b[^>]*>.*?</\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_TAG = re.compile(r"<([a-zA-Z0-9]+)((?:\s+[^>]*?)?)(/?)>")
_HREF = re.compile(r"""href\s*=\s*["']([^"']*)["']""", re.IGNORECASE)
_BLANK_RUN = re.compile(r"\n{3,}")
_SPACE_RUN = re.compile(r"[ \t]{2,}")


def _strip_attributes(match: re.Match[str]) -> str:
    """Keep the tag and, on a link, its target. Class soup helps nobody."""
    tag, attrs, self_closing = match.group(1), match.group(2), match.group(3)
    href = _HREF.search(attrs)
    if href and tag.lower() == "a":
        return f'<a href="{href.group(1)}">'
    return f"<{tag}{self_closing}>"


def clean_html(html: str) -> str:
    """Strip a page down to the structure and links worth spending tokens on."""
    html = _COMMENT.sub("", _DROP.sub("", html))
    html = _TAG.sub(_strip_attributes, html)
    lines = (line.strip() for line in html.split("\n"))
    return _BLANK_RUN.sub("\n\n", _SPACE_RUN.sub(" ", "\n".join(lines))).strip()


def _metadata(item: RawItem) -> Iterator[str]:
    for label, value in (
        ("url", item.url),
        ("title", item.title),
        ("site", item.og_site_name),
        ("published", item.published_at.date().isoformat() if item.published_at else None),
        ("language", item.locale or item.language),
    ):
        if value:
            yield f"{label}: {value}"


def build_context(item: RawItem, *, markup: bool = True) -> str:
    """The user message for one raw item: what the page is, then what it says.

    The two are delimited because they are different kinds of claim — the
    metadata describes the page being read, which for a roundup is emphatically
    not where the cited critic published.
    """
    # Markup that cleans away to nothing was all chrome; the text is what is left.
    body = (clean_html(item.raw_html) if markup and item.raw_html else "") or item.raw_text
    return "\n".join(
        ("<source>", *_metadata(item), "</source>", "", "<article>", body, "</article>")
    )
