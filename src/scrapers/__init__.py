"""Package des scrapers e-commerce multi-plateformes.

Ce package contient les scrapers pour différentes plateformes e-commerce :
- Amazon
- eBay
- Walmart
- Etsy
- Shopify
"""

from .base_scraper import BaseScraper, Product
from .amazon_scraper import AmazonScraper
from .ebay_scraper import EbayScraper
from .walmart_scraper import WalmartScraper
from .etsy_scraper import EtsyScraper
from .shopify_scraper import ShopifyScraper

__all__ = [
    'BaseScraper',
    'Product',
    'AmazonScraper',
    'EbayScraper',
    'WalmartScraper',
    'EtsyScraper',
    'ShopifyScraper'
]