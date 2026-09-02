"""Tests for the custom `@raw_item` spider contract."""

from finalscoring.scraping.contracts import RawItemContract
from finalscoring.scraping.item import RawItem
from finalscoring.scraping.spiders import SpielDesJahresSpider


def _contract() -> RawItemContract:
    return RawItemContract(SpielDesJahresSpider().parse_wp_json, "item")


def test_raw_item_contract_injects_a_raw_item_cb_kwarg():
    args = _contract().adjust_request_args({"cb_kwargs": None})

    assert isinstance(args["cb_kwargs"]["item"], RawItem)


def test_raw_item_contract_keeps_other_cb_kwargs():
    args = _contract().adjust_request_args({"cb_kwargs": {"page": 1}})

    assert args["cb_kwargs"]["page"] == 1
    assert isinstance(args["cb_kwargs"]["item"], RawItem)
