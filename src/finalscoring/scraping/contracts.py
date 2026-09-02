"""Custom spider contracts.

`@populated` is the one that does the real work. Scrapy's built-in `@scrapes`
only checks a field *exists* on the item, which is always true for a Pydantic
`RawItem` — every field is declared. `@populated` checks the field has a
truthy value, so a selector that silently stops matching (an empty `title`, no
`tags`, a lost `outlet_slug`) fails the check instead of passing it.

`@raw_item` covers `parse_wp_json`, which normally receives the page's item
from `parse_roundup` through `cb_kwargs`; under `scrapy check` there is no
upstream callback, so it synthesises a minimal one.
"""

from typing import Any

from itemadapter import ItemAdapter, is_item
from scrapy.contracts import Contract
from scrapy.exceptions import ContractFail

from finalscoring.scraping.item import RawItem


class PopulatedContract(Contract):
    """`@populated f1 f2 …` — every returned item must have a truthy value there."""

    name = "populated"

    def post_process(self, output: list[Any]) -> None:
        for item in output:
            if not is_item(item):
                continue
            adapter = ItemAdapter(item)
            empty = [field for field in self.args if not adapter.get(field)]
            if empty:
                raise ContractFail(f"Empty fields: {', '.join(empty)}")


class RawItemContract(Contract):
    """`@raw_item <name>` — set a synthetic `RawItem` on that `cb_kwargs` key."""

    name = "raw_item"

    def adjust_request_args(self, args: dict[str, Any]) -> dict[str, Any]:
        if not args.get("cb_kwargs"):
            args["cb_kwargs"] = {}
        args["cb_kwargs"][self.args[0]] = RawItem(
            url="https://example.com/contract",
            spider_slug="contract",
            raw_text="contract placeholder",
        )
        return args
