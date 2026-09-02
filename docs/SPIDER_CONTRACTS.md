# Spider contracts

Every parsing callback in the six site-specific spiders — `spiel_des_jahres`,
`games_we_play`, `space_biff`, `rezensionen_fuer_millionen`, `meeple_mountain`,
`hall9000` — carries [Scrapy spider
contracts](https://docs.scrapy.org/en/latest/topics/contracts.html) in its
docstring: a lightweight smoke test that fetches one stable known-good URL and
checks the callback still returns something. `shut_up_and_sit_down` is not yet
covered; `review_links` and `luding` parse arbitrary markup with trafilatura
and take no single stable URL, so contracts do not fit them. They exist to catch an upstream
layout change that would otherwise turn a crawl into silent empty output.

## Running them

```sh
uv run scrapy check          # every spider
uv run scrapy check hall9000 # one spider
```

`scrapy.cfg` points Scrapy at `finalscoring.scraping.scrapy_settings`, which
sets `SPIDER_MODULES` so `scrapy check` discovers the spiders — the pipeline
itself runs them through `python -m finalscoring.scraping`, not the CLI.

## Not in CI

The checks make real HTTP requests to third-party sites, so they are slow and
occasionally flaky — the wrong shape for the offline pytest suite. Run them
manually after touching a spider, or on a schedule as a monitoring signal.

## Coverage notes

- `@returns items 1` is the load-bearing assertion: every item-producing
  callback returns `None` when its selectors stop matching, which is exactly
  the failure to catch. `@scrapes` is belt-and-braces — on a Pydantic
  `RawItem` every field is always present.
- Callbacks that take `cb_kwargs` use `@cb_kwargs` (plain JSON: `hall9000.parse_list`)
  or the custom `@raw_item` contract (`finalscoring/scraping/contracts.py`),
  which injects a synthetic `RawItem` for `spiel_des_jahres.parse_wp_json`.
  Because that item is synthetic, its contract only checks the REST URL is
  reachable and the parse does not raise — not that the merge found content.
- URLs favour long-lived reviews over recent posts. If a target 404s, swap it
  for another stable one on the same site rather than deleting the contract.
