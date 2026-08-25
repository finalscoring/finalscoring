"""Tests for RawItem — the spider-to-extraction contract."""

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from finalscoring.scraping.item import RawItem


def _item(**kwargs: Any) -> RawItem:
    return RawItem.model_validate(
        {"url": "https://example.com/review", "spider_slug": "acme", "raw_text": "Great game."}
        | kwargs
    )


def test_minimal_valid_item():
    item = _item()
    assert item.url == "https://example.com/review"
    assert item.spider_slug == "acme"
    assert item.raw_text == "Great game."
    assert item.raw_html is None
    assert item.title is None
    assert item.description is None
    assert item.published_at is None
    assert item.language is None
    assert item.image_url is None
    assert item.tags == []
    assert item.duration_seconds is None
    assert item.outlet_slug is None
    assert item.og_site_name is None
    assert item.oembed is None
    assert item.schema_org == []
    assert item.extra == {}


def test_full_item():
    item = _item(
        spider_slug="spiel_des_jahres",
        raw_text="Catan is excellent.",
        raw_html="<article>Catan is excellent.</article>",
        title="Review of Catan",
        description="A deep dive into Catan.",
        published_at=datetime(2025, 6, 1, tzinfo=UTC),
        language="de",
        image_url="https://example.com/image.jpg",
        tags=["strategy", "family"],
        duration_seconds=480,
        outlet_slug="spielbox",
        og_site_name="Spielbox",
        oembed={"type": "rich", "title": "Review of Catan"},
        schema_org=[{"@type": "Review", "name": "Catan"}],
        extra={"wp_json": {"id": 42}},
    )
    assert item.raw_html == "<article>Catan is excellent.</article>"
    assert item.language == "de"
    assert item.tags == ["strategy", "family"]
    assert item.duration_seconds == 480
    assert item.outlet_slug == "spielbox"
    assert item.oembed == {"type": "rich", "title": "Review of Catan"}
    assert item.schema_org == [{"@type": "Review", "name": "Catan"}]
    assert item.extra == {"wp_json": {"id": 42}}


def test_scraped_at_defaults_to_utc_now():
    assert _item().scraped_at.tzinfo == UTC


def test_empty_url_rejected():
    with pytest.raises(ValidationError):
        _item(url="   ")


def test_empty_spider_slug_rejected():
    with pytest.raises(ValidationError):
        _item(spider_slug="")


def test_empty_raw_text_rejected():
    with pytest.raises(ValidationError):
        _item(raw_text="  ")


def test_invalid_language_rejected():
    with pytest.raises(ValidationError):
        _item(language="english")


def test_uppercase_language_rejected():
    with pytest.raises(ValidationError):
        _item(language="EN")


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("de_DE", "de-DE"),
        ("de-DE", "de-DE"),
        ("DE_de", "de-DE"),
        ("de", "de"),
        ("  en_GB  ", "en-GB"),
    ],
)
def test_locale_is_normalised_to_bcp_47(given: str, expected: str):
    """Open Graph writes de_DE, html lang writes de-DE; both mean the same thing."""
    assert _item(locale=given).locale == expected


def test_locale_keeps_the_region_language_discards():
    """de-AT and de-CH are different outlets, so the region has to survive."""
    item = _item(language="de", locale="de-AT")

    assert item.language == "de"
    assert item.locale == "de-AT"


def test_invalid_locale_rejected():
    with pytest.raises(ValidationError):
        _item(locale="Deutschland")
