"""Custom spider contract for callbacks fed a pre-built `RawItem`.

`parse_wp_json` normally receives the page's item from `parse_roundup` through
`cb_kwargs`; under `scrapy check` there is no upstream callback, so `@raw_item
<name>` synthesises a minimal one to exercise the REST parse/merge path.
"""

from typing import Any

from scrapy.contracts import Contract

from finalscoring.scraping.item import RawItem


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
