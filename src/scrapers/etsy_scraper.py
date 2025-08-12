"""Scraper pour Etsy."""

from typing import List, Optional
from datetime import datetime
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from apify import Actor

from .base_scraper import BaseScraper, Product

# Import de la fonction safe_log depuis main.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import safe_log


class EtsyScraper(BaseScraper):
    """Scraper spécialisé pour Etsy."""
    
    def __init__(self, max_results: int = 50):
        super().__init__(max_results)
        self.base_url = 'https://www.etsy.com'
        # URLs alternatives pour éviter la détection
        self.search_endpoints = [
            '/search?q={}&ref=search_bar',
            '/search?q={}&order=most_relevant',
            '/search?q={}&explicit=1',
            '/c/{}?q={}'
        ]
    
    def get_platform_name(self) -> str:
        return 'Etsy'
    
    async def search_products(self, search_term: str) -> List[Product]:
        """Recherche des produits sur Etsy avec techniques anti-détection."""
        products = []
        
        try:
            # Ajouter des headers spécifiques à Etsy
            etsy_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.etsy.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1'
            }
            
            # Mettre à jour les headers de session
            self.session.headers.update(etsy_headers)
            
            # Essayer différents endpoints de recherche
            for i, endpoint in enumerate(self.search_endpoints):
                try:
                    if endpoint.count('{}') == 2:
                        # Pour les endpoints avec catégorie
                        search_url = f'{self.base_url}{endpoint.format(quote_plus(search_term), quote_plus(search_term))}'
                    else:
                        search_url = f'{self.base_url}{endpoint.format(quote_plus(search_term))}'
                    
                    await safe_log('info', f'Tentative Etsy endpoint {i+1}: {search_url}')
                    
                    # Délai aléatoire avant chaque requête
                    await self.random_delay(4.0, 10.0)
                    
                    soup = await self.get_page_content(search_url)
                    if not soup:
                        continue
                    
                    # Vérifier si on a été bloqué
                    page_text = soup.get_text().lower()
                    if any(block_indicator in page_text for block_indicator in [
                        'captcha', 'robot', 'blocked', 'access denied', 
                        'security check', 'unusual traffic', 'rate limit'
                    ]):
                        await safe_log('warning', f'Blocage détecté sur Etsy, essai endpoint suivant')
                        continue
                    
                    # Sélecteurs pour les résultats de recherche Etsy
                    product_containers = soup.find_all('div', {'data-test-id': 'listing-card'})
                    
                    # Fallback avec d'autres sélecteurs
                    if not product_containers:
                        product_containers = soup.find_all('div', class_='v2-listing-card')
                    
                    if not product_containers:
                        product_containers = soup.find_all('div', class_='listing-card')
                    
                    if not product_containers:
                        product_containers = soup.find_all('article', {'data-test-id': True})
                    
                    if product_containers:
                        await safe_log('info', f'Trouvé {len(product_containers)} conteneurs de produits Etsy')
                        
                        for container in product_containers[:self.max_results]:
                            product = await self._extract_product_info(container)
                            if product:
                                products.append(product)
                                await safe_log('info', f'Produit Etsy extrait: {product.title[:50]}...')
                            
                            # Petit délai entre extractions
                            await self.random_delay(1.0, 3.0)
                        
                        break  # Succès, sortir de la boucle
                    else:
                        await safe_log('warning', f'Aucun conteneur de produit trouvé avec endpoint {i+1}')
                        
                except Exception as e:
                    await safe_log('error', f'Erreur avec endpoint Etsy {i+1}: {str(e)}')
                    continue
            
            await safe_log('info', f'Total produits Etsy trouvés: {len(products)}')
            
        except Exception as e:
            await safe_log('error', f'Erreur lors du scraping Etsy: {str(e)}')
        
        return products
    
    async def _extract_product_info(self, container: BeautifulSoup) -> Optional[Product]:
        """Extrait les informations d'un produit depuis son conteneur."""
        try:
            # Titre du produit
            title_elem = container.find('h3', class_='v2-listing-card__title') or container.find('a', {'data-test-id': 'listing-link'})
            if not title_elem:
                return None
            
            # Récupération du lien
            if title_elem.name == 'a':
                title_link = title_elem
            else:
                title_link = title_elem.find('a') or container.find('a', {'data-test-id': 'listing-link'})
            
            if not title_link:
                return None
                
            title = self.clean_text(title_link.get_text())
            product_url = title_link.get('href', '')
            
            # Assurer que l'URL est complète
            if product_url.startswith('/'):
                product_url = self.base_url + product_url
            
            # Prix
            price = None
            currency = 'USD'
            
            price_elem = container.find('span', class_='currency-value') or container.find('p', class_='a-offscreen')
            if price_elem:
                price_text = price_elem.get_text()
                price = self.extract_price(price_text)
                
                # Détection de la devise
                currency_elem = container.find('span', class_='currency-symbol')
                if currency_elem:
                    currency_symbol = currency_elem.get_text()
                    if '$' in currency_symbol:
                        currency = 'USD'
                    elif '€' in currency_symbol:
                        currency = 'EUR'
                    elif '£' in currency_symbol:
                        currency = 'GBP'
            
            # Image
            img_elem = container.find('img', {'data-test-id': 'listing-card-image'})
            image_url = img_elem.get('src') if img_elem else None
            
            # Note et avis
            rating = None
            reviews_count = None
            
            rating_elem = container.find('span', class_='screen-reader-only')
            if rating_elem and 'out of 5 stars' in rating_elem.get_text():
                rating_text = rating_elem.get_text()
                rating = self.extract_rating(rating_text)
            
            reviews_elem = container.find('span', class_='shop2-review-review')
            if reviews_elem:
                reviews_text = reviews_elem.get_text()
                reviews_count = self.extract_reviews_count(reviews_text)
            
            # Disponibilité (généralement disponible sur Etsy)
            availability = 'Disponible'
            
            # Badge de livraison gratuite ou autres promotions
            badge_elem = container.find('span', class_='free-shipping-note')
            shipping_info = ''
            if badge_elem:
                shipping_info = self.clean_text(badge_elem.get_text())
            
            # Vendeur (boutique Etsy)
            seller = 'Boutique Etsy'
            seller_elem = container.find('p', class_='shop-name')
            if seller_elem:
                seller = self.clean_text(seller_elem.get_text())
            
            # Favoris (nombre de personnes qui ont mis en favori)
            favorites_elem = container.find('span', class_='favorite-count')
            favorites_count = None
            if favorites_elem:
                favorites_text = favorites_elem.get_text()
                favorites_count = self.extract_reviews_count(favorites_text)
            
            # Tags ou catégories
            tags_elem = container.find('div', class_='listing-card-tags')
            tags = []
            if tags_elem:
                tag_elements = tags_elem.find_all('span')
                tags = [self.clean_text(tag.get_text()) for tag in tag_elements]
            
            description = ''
            if shipping_info:
                description += f'Livraison: {shipping_info}'
            if favorites_count:
                description += f' - {favorites_count} favoris' if description else f'{favorites_count} favoris'
            if tags:
                description += f' - Tags: {", ".join(tags[:3])}' if description else f'Tags: {", ".join(tags[:3])}'
            
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
            await safe_log('warning', f'Erreur extraction produit Etsy: {str(e)}')
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[dict]:
        """Récupère les détails complets d'un produit Etsy."""
        try:
            soup = await self.get_page_content(product_url)
            if not soup:
                return None
            
            details = {}
            
            # Description détaillée
            desc_elem = soup.find('div', {'data-test-id': 'description-text'}) or soup.find('div', class_='shop2-product-description')
            if desc_elem:
                details['description'] = self.clean_text(desc_elem.get_text())
            
            # Matériaux utilisés
            materials_elem = soup.find('div', {'data-test-id': 'materials'})
            if materials_elem:
                materials = []
                material_links = materials_elem.find_all('a')
                for link in material_links:
                    materials.append(self.clean_text(link.get_text()))
                details['materials'] = materials
            
            # Informations sur la boutique
            shop_elem = soup.find('div', class_='shop2-shop-info')
            if shop_elem:
                shop_name_elem = shop_elem.find('h1')
                if shop_name_elem:
                    details['shop_name'] = self.clean_text(shop_name_elem.get_text())
            
            # Politique de retour
            return_policy_elem = soup.find('div', {'data-test-id': 'return-policy'})
            if return_policy_elem:
                details['return_policy'] = self.clean_text(return_policy_elem.get_text())
            
            # Délai de traitement
            processing_time_elem = soup.find('div', {'data-test-id': 'processing-time'})
            if processing_time_elem:
                details['processing_time'] = self.clean_text(processing_time_elem.get_text())
            
            return details
            
        except Exception as e:
            await Actor.log.warning(f'Erreur récupération détails Etsy: {str(e)}')
            return None