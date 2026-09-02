# Spider contracts

Every parsing callback in the site-specific spiders carries [Scrapy spider
contracts](https://docs.scrapy.org/en/latest/topics/contracts.html) in its
docstring: a lightweight smoke test that fetches one stable known-good URL and
checks the callback still parses it. They exist to catch an upstream layout
change that would otherwise turn a crawl into silent empty output — there is
essentially no other signal that a scraper still does what it should.

Covered: `spiel_des_jahres`, `games_we_play`, `space_biff`,
`rezensionen_fuer_millionen`, `meeple_mountain`, `hall9000`, and
`shut_up_and_sit_down.parse_list`.

Not covered:

- `shut_up_and_sit_down.parse_review` — against the current live site it
  returns `None` for every review (the theme dropped the `meta-category` span
  the `reviews_only` gate keys on), and the site 503s intermittently behind bot
  protection. The spider needs its own fix before a contract can be green.
- `review_links`, `luding` — parse arbitrary third-party markup with
  trafilatura and take no single stable URL, so contracts do not fit them.

## Running them

```sh
uv run scrapy check          # every spider
uv run scrapy check hall9000 # one spider
```

`scrapy.cfg` points Scrapy at `finalscoring.scraping.scrapy_settings`, which
sets `SPIDER_MODULES` so `scrapy check` discovers the spiders — the pipeline
itself runs them through `python -m finalscoring.scraping`, not the CLI.

## The checks

Each callback declares:

- `@url` — a stable, long-lived review or index URL. If one 404s, swap it for
  another stable page on the same site rather than deleting the contract.
- `@returns items 1` / `@returns requests 1` — the load-bearing assertion.
  Every item callback returns `None` when its selectors stop matching, so
  "returned 0 items" *is* the layout-break signal.
- `@populated <fields>` — a **custom** contract (`scraping/contracts.py`).
  Scrapy's built-in `@scrapes` only checks a field *exists*, which is always
  true for a Pydantic `RawItem`; `@populated` checks it has a truthy value, so
  a selector that quietly stops matching (empty `title`, no `tags`, lost
  `outlet_slug`) fails instead of passing.

Two callbacks take `cb_kwargs`:

- `hall9000.parse_list` — `@cb_kwargs` with plain JSON.
- `spiel_des_jahres.parse_wp_json` — the custom `@raw_item` contract injects a
  synthetic `RawItem` (there is no upstream callback under `scrapy check`).
  `@populated extra` tells success from fallback: `merge_wp_json` only fills
  `extra` when the REST payload parsed.

## CI

These make real HTTP requests to third-party sites — slow, and occasionally
flaky — so they do not belong in the per-commit pytest run (which is fully
offline against hand-written fixtures). They *do* belong in CI as a **separate
scheduled job** (e.g. nightly) that is allowed to fail without blocking a
merge: a red run there is the alert that a site changed shape. No pipeline is
wired yet; when one exists, add a `scrapy check` stage on a schedule trigger.
