"""Per-source spider implementations.

Add a new source by writing a spider module here, then registering its
critic record in ``data/overrides/critics.csv``. The CLI's
``fs scrape <name>`` command discovers spiders by class attribute
``name``.

The Spiel-des-Jahres spider below is the first concrete source, ported
from the proof-of-concept SdJ scraper. It serves as a meta-source — one
roundup page often cites several critics on several games — and as the
reference example for adding new spiders.
"""
