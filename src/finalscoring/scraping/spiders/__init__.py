"""Spiders, one module per source."""

from finalscoring.scraping.spiders.games_we_play import GamesWePlaySpider
from finalscoring.scraping.spiders.spiel_des_jahres import SpielDesJahresSpider

__all__ = ["GamesWePlaySpider", "SpielDesJahresSpider"]
