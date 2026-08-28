"""Spiders, one module per source."""

from finalscoring.scraping.spiders.space_biff import SpaceBiffSpider
from finalscoring.scraping.spiders.spiel_des_jahres import SpielDesJahresSpider

__all__ = ["SpaceBiffSpider", "SpielDesJahresSpider"]
