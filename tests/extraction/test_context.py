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
            site_name="Spiel des Jahres",
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


def test_tags_are_sent():
    """Some sites file a review under its verdict, so the score is only here."""
    context = build_context(_item(tags=["**** solide"]))

    assert "tags: **** solide" in context


def test_several_tags_are_joined():
    assert "tags: Rezension, Kennerspiel" in build_context(_item(tags=["Rezension", "Kennerspiel"]))


def test_no_tags_means_no_tag_line():
    assert "tags:" not in build_context(_item())


def test_absent_metadata_is_omitted_not_nulled():
    """`title: None` would invite the model to treat the string as a value."""
    context = build_context(_item())

    assert "None" not in context
    assert "title:" not in context


def test_the_page_and_the_article_are_delimited():
    """A roundup's own site is emphatically not where the cited critic published."""
    context = build_context(_item(site_name="Spiel des Jahres"))

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


# --- structured fields the spider read for the model ------------------------


def _reviewed(**hint: Any) -> RawItem:
    return _item(reviews=[hint])


def test_known_critic_name_is_sent_as_the_byline():
    """A solo blog carries no per-post byline; the spider knows who wrote it."""
    assert "byline: Dan Thurot" in build_context(_item(known_critic_name="Dan Thurot"))


def test_bylines_are_sent_when_there_is_no_known_critic():
    assert "byline: Ian Howard" in build_context(_item(bylines=["Ian Howard"]))


def test_known_critic_name_wins_over_scraped_bylines():
    context = build_context(_item(known_critic_name="Dan Thurot", bylines=["webdeveloper"]))
    header = context[: context.index("</source>")]

    assert "byline: Dan Thurot" in header
    assert "webdeveloper" not in header


def test_page_medium_and_categories_are_sent():
    context = build_context(_item(medium="video", categories=["reviews"]))

    assert "medium: video" in context
    assert "categories: reviews" in context


def test_no_structured_fields_means_no_extra_lines():
    context = build_context(_item())
    header = context[: context.index("</source>")]

    assert "byline:" not in header
    assert "medium:" not in header
    assert "<review>" not in context


def test_a_review_block_lists_the_game_the_spider_read():
    context = build_context(
        _reviewed(game={"titles": ["Catan"], "designers": ["Klaus Teuber"], "year_published": 1995})
    )

    assert "<review>" in context
    assert "game: Catan" in context
    assert "designers: Klaus Teuber" in context
    assert "year: 1995" in context


def test_a_bgg_id_becomes_a_bgg_reference():
    assert "bgg: boardgame/13" in build_context(_reviewed(game={"titles": ["Catan"], "bgg_id": 13}))


def test_an_empty_review_hint_produces_no_block():
    assert "<review>" not in build_context(_reviewed())


def test_a_plain_rating_is_labelled_by_its_system():
    context = build_context(
        _reviewed(ratings=[{"system": "editorial", "value": 5, "scale_max": 6}])
    )

    assert "<review>" in context
    assert "rating editorial: 5/6" in context


def test_a_rating_is_labelled_by_its_axis():
    context = build_context(
        _reviewed(ratings=[{"system": "axis", "axis": "Spielreiz", "value": 5}])
    )

    assert "rating Spielreiz: 5" in context


def test_a_rating_without_a_number_falls_back_to_its_words():
    context = build_context(
        _reviewed(ratings=[{"system": "star_label", "label": "solide", "verbatim": "**** solide"}])
    )

    assert "rating star_label: solide" in context


def test_a_rating_value_keeps_its_half_point():
    context = build_context(
        _reviewed(ratings=[{"system": "overall", "value": "4,5", "scale_max": 6}])
    )

    assert "rating overall: 4.5/6" in context


def test_a_rank_notes_that_lower_is_better():
    context = build_context(
        _reviewed(ratings=[{"system": "rank", "value": 1, "direction": "lower_is_better"}])
    )

    assert "rating rank: 1 (lower is better)" in context


def test_a_cited_reviews_own_provenance_goes_in_its_block():
    context = build_context(
        _reviewed(
            critic_names=["Karsten Grosser"],
            outlet_name="Spielekenner",
            review_url="https://www.spielekenner.de/rezension/moon",
            game={"titles": ["Moon"]},
        )
    )

    assert "critic: Karsten Grosser" in context
    assert "outlet: Spielekenner" in context
    assert "review url: https://www.spielekenner.de/rezension/moon" in context


def test_a_listicle_gets_one_block_per_game():
    context = build_context(
        _item(
            reviews=[
                {"game": {"titles": ["Azul"]}, "ratings": [{"system": "star_label", "value": 5}]},
                {
                    "game": {"titles": ["Sagrada"]},
                    "ratings": [{"system": "star_label", "value": 4}],
                },
            ]
        )
    )

    assert context.count("<review>") == 2
    assert "game: Azul" in context
    assert "game: Sagrada" in context


def test_review_blocks_sit_between_source_and_article():
    context = build_context(_reviewed(game={"titles": ["Vantage"]}))

    assert context.index("</source>") < context.index("<review>") < context.index("<article>")
