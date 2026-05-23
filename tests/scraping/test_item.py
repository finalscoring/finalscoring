"""Tests for RawItem — the spider-to-extraction contract."""

from datetime import UTC

import pytest
from pydantic import ValidationError

from finalscoring.scraping.item import RawItem


def test_minimal_valid_item():
    item = RawItem(url="https://example.com/review", source_id="acme", raw_text="Great game.")
    assert item.url == "https://example.com/review"
    assert item.source_id == "acme"
    assert item.raw_text == "Great game."
    assert item.title is None
    assert item.description is None
    assert item.published_at is None
    assert item.language is None


def test_full_item():
    from datetime import datetime

    item = RawItem(
        url="https://example.com/review",
        source_id="spiel_des_jahres",
        raw_text="Catan is excellent.",
        title="Review of Catan",
        description="A deep dive into Catan.",
        published_at=datetime(2025, 6, 1, tzinfo=UTC),
        language="de",
    )
    assert item.language == "de"
    assert item.published_at is not None


def test_scraped_at_defaults_to_utc_now():
    item = RawItem(url="https://example.com/review", source_id="acme", raw_text="Good game.")
    assert item.scraped_at.tzinfo == UTC


def test_empty_url_rejected():
    with pytest.raises(ValidationError):
        RawItem(url="   ", source_id="acme", raw_text="Good game.")


def test_empty_source_id_rejected():
    with pytest.raises(ValidationError):
        RawItem(url="https://example.com/review", source_id="", raw_text="Good game.")


def test_empty_raw_text_rejected():
    with pytest.raises(ValidationError):
        RawItem(url="https://example.com/review", source_id="acme", raw_text="  ")


def test_invalid_language_rejected():
    with pytest.raises(ValidationError):
        RawItem(
            url="https://example.com/review",
            source_id="acme",
            raw_text="Good game.",
            language="english",
        )


def test_uppercase_language_rejected():
    with pytest.raises(ValidationError):
        RawItem(
            url="https://example.com/review",
            source_id="acme",
            raw_text="Good game.",
            language="EN",
        )
