"""Tests for the message the model reads."""

from typing import Any

import pytest

from finalscoring.extraction.context import build_context, clean_html
from finalscoring.scraping.item import RawItem

ARTICLE = (
    '<p class="wp-block-paragraph">Für <strong>Michaela Poignée</strong> läuft es gut.'
    '<sup><a href="#fn1">1</a></sup></p>'
)


def _item(**kwargs: Any) -> RawItem:
    return RawItem.model_validate(
        {
            "url": "https://example.com/roundup",
            "spider_slug": "spiel-des-jahres",
            "raw_text": "Für Michaela Poignée läuft es gut.[1]",
            "raw_html": ARTICLE,
        }
        | kwargs
    )


def test_structure_and_links_survive():
    """The tags are the point: <p> bounds a passage, <a href> is the only link."""
    cleaned = clean_html(ARTICLE)

    assert "<p>" in cleaned
    assert "<strong>" in cleaned
    assert '<a href="#fn1">' in cleaned


def test_attributes_other_than_href_are_dropped():
    assert "wp-block-paragraph" not in clean_html(ARTICLE)


@pytest.mark.parametrize("tag", ["script", "style", "svg", "form", "nav", "iframe"])
def test_noise_subtrees_are_dropped(tag: str):
    html = f"<p>keep</p><{tag} class='x'>drop me</{tag}><p>keep too</p>"

    cleaned = clean_html(html)

    assert "drop me" not in cleaned
    assert cleaned.count("keep") == 2


def test_comments_are_dropped():
    assert "secret" not in clean_html("<p>a</p><!-- secret --><p>b</p>")


def test_a_self_closing_tag_survives():
    assert "<br/>" in clean_html('<br class="x"/>')


def test_href_is_kept_only_on_links():
    """A stray href on a non-anchor is not a link and not worth the tokens."""
    assert clean_html('<div href="https://example.com/x">a</div>') == "<div>a</div>"


def test_the_metadata_header_names_the_page():
    context = build_context(
        _item(
            title="Kritikenrundschau: Dewan",
            og_site_name="Spiel des Jahres",
            published_at="2026-04-20T08:00:00Z",
            locale="de-DE",
        )
    )

    assert "<source>" in context
    assert "url: https://example.com/roundup" in context
    assert "title: Kritikenrundschau: Dewan" in context
    assert "site: Spiel des Jahres" in context
    assert "published: 2026-04-20" in context
    assert "language: de-DE" in context


def test_absent_metadata_is_omitted_not_nulled():
    """`title: None` would invite the model to treat the string as a value."""
    context = build_context(_item())

    assert "None" not in context
    assert "title:" not in context


def test_the_page_and_the_article_are_delimited():
    """A roundup's own site is emphatically not where the cited critic published."""
    context = build_context(_item(og_site_name="Spiel des Jahres"))

    source = context.index("<source>")
    assert source < context.index("</source>") < context.index("<article>")
    assert "Spiel des Jahres" in context[source : context.index("</source>")]


def test_markup_mode_sends_the_html():
    assert "<strong>" in build_context(_item(), markup=True)


def test_text_mode_sends_the_flattened_text():
    context = build_context(_item(), markup=False)

    assert "<strong>" not in context
    assert "Für Michaela Poignée läuft es gut.[1]" in context


def test_an_item_without_html_falls_back_to_text():
    """Not every source is a web page; a transcript has no markup to keep."""
    context = build_context(_item(raw_html=None), markup=True)

    assert "Für Michaela Poignée läuft es gut.[1]" in context


@pytest.mark.parametrize("html", ["", "<script>tracking()</script>", "   "])
def test_html_that_cleans_away_to_nothing_falls_back_to_text(html: str):
    """Losing the article to an all-chrome page would be a silent empty extraction."""
    context = build_context(_item(raw_html=html), markup=True)

    assert "Für Michaela Poignée läuft es gut.[1]" in context


def test_the_locale_is_preferred_over_the_bare_language():
    """de-AT and de-DE review differently; the regional variant is the better hint."""
    context = build_context(_item(language="de", locale="de-AT"))

    assert "language: de-AT" in context


def test_the_bare_language_is_used_when_there_is_no_locale():
    assert "language: de" in build_context(_item(language="de"))
