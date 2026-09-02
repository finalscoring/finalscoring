"""Tests for the custom spider contracts."""

import pytest
from scrapy.exceptions import ContractFail

from finalscoring.scraping.contracts import PopulatedContract, RawItemContract
from finalscoring.scraping.item import RawItem
from finalscoring.scraping.spiders import SpielDesJahresSpider


def _populated(*fields: str) -> PopulatedContract:
    return PopulatedContract(SpielDesJahresSpider().parse_roundup, *fields)


def test_populated_passes_when_every_field_is_truthy():
    item = RawItem(url="u", spider_slug="s", raw_text="t", tags=["x"])

    _populated("url", "raw_text", "tags").post_process([item])


def test_populated_fails_on_an_empty_field():
    item = RawItem(url="u", spider_slug="s", raw_text="t")  # tags defaults to []

    with pytest.raises(ContractFail, match="tags"):
        _populated("tags").post_process([item])


def test_populated_ignores_non_items():
    _populated("anything").post_process(["not an item", None])


def _contract() -> RawItemContract:
    return RawItemContract(SpielDesJahresSpider().parse_wp_json, "item")


def test_raw_item_contract_injects_a_raw_item_cb_kwarg():
    args = _contract().adjust_request_args({"cb_kwargs": None})

    assert isinstance(args["cb_kwargs"]["item"], RawItem)


def test_raw_item_contract_keeps_other_cb_kwargs():
    args = _contract().adjust_request_args({"cb_kwargs": {"page": 1}})

    assert args["cb_kwargs"]["page"] == 1
    assert isinstance(args["cb_kwargs"]["item"], RawItem)
