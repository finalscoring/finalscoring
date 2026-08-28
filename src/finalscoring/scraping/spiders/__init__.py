"""Spiders, one module per source."""

from finalscoring.scraping.spiders.rezensionen_fuer_millionen import (
    RezensionenFuerMillionenSpider,
)
from finalscoring.scraping.spiders.spiel_des_jahres import SpielDesJahresSpider

__all__ = ["RezensionenFuerMillionenSpider", "SpielDesJahresSpider"]
