"""Package des scrapers e-commerce multi-plateformes.

Ce package contient les scrapers pour différentes plateformes e-commerce :
- Amazon
- eBay
- Playwright (multi-plateforme)
"""

from .base_scraper import BaseScraper, Product
from .amazon_scraper import AmazonScraper
from .ebay_scraper import EbayScraper

__all__ = [
    'BaseScraper',
    'Product',
    'AmazonScraper',
    'EbayScraper'
]