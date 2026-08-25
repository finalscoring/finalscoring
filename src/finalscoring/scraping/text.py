"""Turning article HTML into the plain text the extraction step reads."""

import re

from w3lib.html import remove_tags, replace_entities

# Without these breaks one critic's passage runs into the next.
_BLOCK_END = re.compile(
    r"</(?:p|div|li|ol|ul|h[1-6]|blockquote|section|article|figcaption)\s*>|<br\s*/?>",
    re.IGNORECASE,
)
_BLANK_RUN = re.compile(r"\n{3,}")


def html_to_text(html: str) -> str:
    """Extract readable text, preserving the breaks between blocks."""
    text = replace_entities(remove_tags(_BLOCK_END.sub("\n", html)))
    lines = [line.strip() for line in text.split("\n")]
    return _BLANK_RUN.sub("\n\n", "\n".join(lines)).strip()
