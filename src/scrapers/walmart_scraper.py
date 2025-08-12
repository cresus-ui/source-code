"""Scraper pour Walmart."""

from typing import List, Optional
from datetime import datetime
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from apify import Actor

from .base_scraper import BaseScraper, Product


class WalmartScraper(BaseScraper):
    """Scraper spécialisé pour Walmart."""
    
    def __init__(self, max_results: int = 50):
        super().__init__(max_results)
        self.base_url = 'https://www.walmart.com'
    
    def get_platform_name(self) -> str:
        return 'Walmart'
    
    async def search_products(self, search_term: str) -> List[Product]:
        """Recherche des produits sur Walmart."""
        products = []
        
        try:
            # Construction de l'URL de recherche Walmart
            search_url = f'{self.base_url}/search?q={quote_plus(search_term)}'
            await Actor.log.info(f'Recherche Walmart: {search_url}')
            
            soup = await self.get_page_content(search_url)
            if not soup:
                return products
            
            # Sélecteurs pour les résultats de recherche Walmart
            product_containers = soup.find_all('div', {'data-automation-id': 'product-tile'})
            
            # Fallback si le premier sélecteur ne fonctionne pas
            if not product_containers:
                product_containers = soup.find_all('div', class_='mb1 ph1 pa0-xl bb b--near-white w-25')
            
            for container in product_containers[:self.max_results]:
                product = await self._extract_product_info(container)
                if product:
                    products.append(product)
                    await Actor.log.info(f'Produit Walmart extrait: {product.title[:50]}...')
            
            await Actor.log.info(f'Total produits Walmart trouvés: {len(products)}')
            
        except Exception as e:
            await Actor.log.error(f'Erreur lors du scraping Walmart: {str(e)}')
        
        return products
    
    async def _extract_product_info(self, container: BeautifulSoup) -> Optional[Product]:
        """Extrait les informations d'un produit depuis son conteneur."""
        try:
            # Titre du produit
            title_elem = container.find('a', {'data-automation-id': 'product-title'}) or container.find('span', {'data-automation-id': 'product-title'})
            if not title_elem:
                return None
                
            title = self.clean_text(title_elem.get_text())
            
            # URL du produit
            product_url = ''
            if title_elem.name == 'a':
                product_url = self.base_url + title_elem.get('href', '')
            else:
                link_elem = container.find('a')
                if link_elem:
                    product_url = self.base_url + link_elem.get('href', '')
            
            # Prix
            price = None
            currency = 'USD'
            
            # Différents sélecteurs pour le prix Walmart
            price_elem = (
                container.find('span', {'itemprop': 'price'}) or
                container.find('span', class_='price-current') or
                container.find('div', {'data-automation-id': 'product-price'})
            )
            
            if price_elem:
                price_text = price_elem.get_text()
                price = self.extract_price(price_text)
            
            # Image
            img_elem = container.find('img', {'data-automation-id': 'product-image'})
            image_url = img_elem.get('src') if img_elem else None
            
            # Note et avis
            rating = None
            reviews_count = None
            
            rating_elem = container.find('span', class_='average-rating')
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating = self.extract_rating(rating_text)
            
            reviews_elem = container.find('span', class_='review-count')
            if reviews_elem:
                reviews_text = reviews_elem.get_text()
                reviews_count = self.extract_reviews_count(reviews_text)
            
            # Disponibilité
            availability = 'En stock'
            
            # Vérification du stock
            stock_elem = container.find('div', {'data-automation-id': 'fulfillment-badge'})
            if stock_elem:
                stock_text = stock_elem.get_text().lower()
                if 'out of stock' in stock_text or 'rupture' in stock_text:
                    availability = 'Rupture de stock'
                elif 'limited' in stock_text or 'limité' in stock_text:
                    availability = 'Stock limité'
            
            # Options de livraison
            delivery_elem = container.find('div', {'data-automation-id': 'fulfillment-badge'})
            delivery_info = ''
            if delivery_elem:
                delivery_info = self.clean_text(delivery_elem.get_text())
            
            # Vendeur (Walmart ou vendeur tiers)
            seller = 'Walmart'
            seller_elem = container.find('span', class_='seller-name')
            if seller_elem:
                seller = self.clean_text(seller_elem.get_text())
            
            # Badge promotionnel
            promo_elem = container.find('span', class_='badge')
            promo_info = ''
            if promo_elem:
                promo_info = self.clean_text(promo_elem.get_text())
            
            description = ''
            if delivery_info:
                description += f'Livraison: {delivery_info}'
            if promo_info:
                description += f' - Promotion: {promo_info}' if description else f'Promotion: {promo_info}'
            
            return Product(
                title=title,
                price=price,
                currency=currency,
                url=product_url,
                image_url=image_url,
                rating=rating,
                reviews_count=reviews_count,
                availability=availability,
                seller=seller,
                platform=self.get_platform_name(),
                scraped_at=datetime.now(),
                description=description if description else None
            )
            
        except Exception as e:
            await Actor.log.warning(f'Erreur extraction produit Walmart: {str(e)}')
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[dict]:
        """Récupère les détails complets d'un produit Walmart."""
        try:
            soup = await self.get_page_content(product_url)
            if not soup:
                return None
            
            details = {}
            
            # Description détaillée
            desc_elem = soup.find('div', {'data-automation-id': 'product-highlights'}) or soup.find('div', class_='about-desc')
            if desc_elem:
                details['description'] = self.clean_text(desc_elem.get_text())
            
            # Marque
            brand_elem = soup.find('a', {'data-automation-id': 'product-brand-link'})
            if brand_elem:
                details['brand'] = self.clean_text(brand_elem.get_text())
            
            # Modèle/SKU
            model_elem = soup.find('span', {'data-automation-id': 'product-model'})
            if model_elem:
                details['sku'] = self.clean_text(model_elem.get_text())
            
            # Spécifications
            specs_section = soup.find('div', {'data-automation-id': 'product-specifications'})
            if specs_section:
                specs = {}
                spec_items = specs_section.find_all('div', class_='spec-row')
                for item in spec_items:
                    key_elem = item.find('div', class_='spec-name')
                    value_elem = item.find('div', class_='spec-value')
                    if key_elem and value_elem:
                        specs[self.clean_text(key_elem.get_text())] = self.clean_text(value_elem.get_text())
                details['specifications'] = specs
            
            return details
            
        except Exception as e:
            await Actor.log.warning(f'Erreur récupération détails Walmart: {str(e)}')
            return None