"""Scraper pour Amazon."""

from typing import List, Optional
from datetime import datetime
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from apify import Actor

from .base_scraper import BaseScraper, Product

# Import de la fonction safe_log depuis utils
from ..utils import safe_log


class AmazonScraper(BaseScraper):
    """Scraper spécialisé pour Amazon."""
    
    def __init__(self, max_results: int = 50, domain: str = 'amazon.com'):
        super().__init__(max_results)
        self.domain = domain
        self.base_url = f'https://www.{domain}'
        # URLs alternatives pour éviter la détection
        self.search_endpoints = [
            '/s?k={}&ref=sr_pg_1',
            '/s?k={}&i=aps&ref=nb_sb_noss',
            '/s?k={}&field-keywords={}'
        ]
    
    def get_platform_name(self) -> str:
        return 'Amazon'
    
    async def search_products(self, search_term: str) -> List[Product]:
        """Recherche des produits sur Amazon avec techniques anti-détection."""
        products = []
        
        try:
            # Ajouter des headers spécifiques à Amazon
            amazon_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': f'https://www.{self.domain}/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin'
            }
            
            # Mettre à jour les headers de session
            self.session.headers.update(amazon_headers)
            
            # Essayer différents endpoints de recherche
            for i, endpoint in enumerate(self.search_endpoints):
                try:
                    if endpoint.count('{}') == 2:
                        search_url = f'{self.base_url}{endpoint.format(quote_plus(search_term), quote_plus(search_term))}'
                    else:
                        search_url = f'{self.base_url}{endpoint.format(quote_plus(search_term))}'
                    
                    await safe_log('info', f'Tentative Amazon endpoint {i+1}: {search_url}')
                    
                    # Délai aléatoire avant chaque requête
                    await self.random_delay(3.0, 8.0)
                    
                    soup = await self.get_page_content(search_url)
                    if not soup:
                        continue
                    
                    # Vérifier si on a été bloqué
                    if soup.find('img', {'alt': 'captcha'}) or 'robot' in soup.get_text().lower():
                        await safe_log('warning', f'CAPTCHA détecté sur Amazon, essai endpoint suivant')
                        continue
                    
                    # Sélecteurs pour les résultats de recherche Amazon
                    product_containers = soup.find_all('div', {'data-component-type': 's-search-result'})
                    
                    if not product_containers:
                        # Essayer d'autres sélecteurs
                        product_containers = soup.find_all('div', {'data-asin': True})
                    
                    if product_containers:
                        await safe_log('info', f'Trouvé {len(product_containers)} conteneurs de produits')
                        
                        for container in product_containers[:self.max_results]:
                            product = await self._extract_product_info(container)
                            if product:
                                products.append(product)
                                await safe_log('info', f'Produit Amazon extrait: {product.title[:50]}...')
                            
                            # Petit délai entre extractions
                            await self.random_delay(0.5, 2.0)
                        
                        break  # Succès, sortir de la boucle
                    else:
                        await safe_log('warning', f'Aucun conteneur de produit trouvé avec endpoint {i+1}')
                        
                except Exception as e:
                    await safe_log('error', f'Erreur avec endpoint {i+1}: {str(e)}')
                    continue
            
            await safe_log('info', f'Total produits Amazon trouvés: {len(products)}')
            
        except Exception as e:
            await safe_log('error', f'Erreur lors du scraping Amazon: {str(e)}')
        
        return products
    
    async def _extract_product_info(self, container: BeautifulSoup) -> Optional[Product]:
        """Extrait les informations d'un produit depuis son conteneur."""
        try:
            # Titre du produit
            title_elem = container.find('h2', class_='a-size-mini') or container.find('span', class_='a-size-base-plus')
            if not title_elem:
                return None
            
            title_link = title_elem.find('a')
            if not title_link:
                return None
                
            title = self.clean_text(title_link.get_text())
            product_url = self.base_url + title_link.get('href', '')
            
            # Prix
            price = None
            currency = 'USD'
            
            # Différents sélecteurs pour le prix
            price_elem = (
                container.find('span', class_='a-price-whole') or
                container.find('span', class_='a-offscreen') or
                container.find('span', class_='a-price')
            )
            
            if price_elem:
                price_text = price_elem.get_text()
                price = self.extract_price(price_text)
                
                # Détection de la devise
                if '$' in price_text:
                    currency = 'USD'
                elif '€' in price_text:
                    currency = 'EUR'
                elif '£' in price_text:
                    currency = 'GBP'
            
            # Image
            img_elem = container.find('img', class_='s-image')
            image_url = img_elem.get('src') if img_elem else None
            
            # Note et avis
            rating = None
            reviews_count = None
            
            rating_elem = container.find('span', class_='a-icon-alt')
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating = self.extract_rating(rating_text)
            
            reviews_elem = container.find('span', class_='a-size-base')
            if reviews_elem and '(' in reviews_elem.get_text():
                reviews_text = reviews_elem.get_text()
                reviews_count = self.extract_reviews_count(reviews_text)
            
            # Disponibilité
            availability = 'En stock'
            availability_elem = container.find('span', string=lambda text: text and ('stock' in text.lower() or 'disponible' in text.lower()))
            if availability_elem:
                availability = self.clean_text(availability_elem.get_text())
            
            # Vendeur (souvent Amazon ou vendeur tiers)
            seller = 'Amazon'
            seller_elem = container.find('span', class_='a-size-base-plus')
            if seller_elem and 'by' in seller_elem.get_text().lower():
                seller = self.clean_text(seller_elem.get_text())
            
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
                scraped_at=datetime.now()
            )
            
        except Exception as e:
            await safe_log('warning', f'Erreur extraction produit Amazon: {str(e)}')
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[dict]:
        """Récupère les détails complets d'un produit."""
        try:
            soup = await self.get_page_content(product_url)
            if not soup:
                return None
            
            details = {}
            
            # Description
            desc_elem = soup.find('div', {'id': 'feature-bullets'}) or soup.find('div', {'id': 'productDescription'})
            if desc_elem:
                details['description'] = self.clean_text(desc_elem.get_text())
            
            # Marque
            brand_elem = soup.find('span', {'id': 'bylineInfo'}) or soup.find('a', {'id': 'bylineInfo'})
            if brand_elem:
                details['brand'] = self.clean_text(brand_elem.get_text())
            
            # ASIN (identifiant Amazon)
            asin_elem = soup.find('div', {'data-asin': True})
            if asin_elem:
                details['sku'] = asin_elem.get('data-asin')
            
            return details
            
        except Exception as e:
            await safe_log('warning', f'Erreur récupération détails Amazon: {str(e)}')
            return None