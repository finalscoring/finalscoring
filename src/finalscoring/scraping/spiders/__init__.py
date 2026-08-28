"""Spiders, one module per source."""

from finalscoring.scraping.spiders.games_we_play import GamesWePlaySpider
from finalscoring.scraping.spiders.rezensionen_fuer_millionen import (
    RezensionenFuerMillionenSpider,
)
from finalscoring.scraping.spiders.space_biff import SpaceBiffSpider
from finalscoring.scraping.spiders.spiel_des_jahres import SpielDesJahresSpider

__all__ = [
    "GamesWePlaySpider",
    "RezensionenFuerMillionenSpider",
    "SpaceBiffSpider",
    "SpielDesJahresSpider",
]
