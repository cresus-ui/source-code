"""Scraper pour eBay."""

from typing import List, Optional
from datetime import datetime
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from apify import Actor

from .base_scraper import BaseScraper, Product


class EbayScraper(BaseScraper):
    """Scraper spécialisé pour eBay."""
    
    def __init__(self, max_results: int = 50, domain: str = 'ebay.com'):
        super().__init__(max_results)
        self.domain = domain
        self.base_url = f'https://www.{domain}'
    
    def get_platform_name(self) -> str:
        return 'eBay'
    
    async def search_products(self, search_term: str) -> List[Product]:
        """Recherche des produits sur eBay."""
        products = []
        
        try:
            # Construction de l'URL de recherche eBay
            search_url = f'{self.base_url}/sch/i.html?_nkw={quote_plus(search_term)}&_sacat=0'
            Actor.log.info(f'Recherche eBay: {search_url}')
            
            soup = await self.get_page_content(search_url)
            if not soup:
                return products
            
            # Sélecteurs pour les résultats de recherche eBay
            product_containers = soup.find_all('div', class_='s-item__wrapper clearfix')
            
            for container in product_containers[:self.max_results]:
                product = await self._extract_product_info(container)
                if product:
                    products.append(product)
                    Actor.log.info(f'Produit eBay extrait: {product.title[:50]}...')
            
            Actor.log.info(f'Total produits eBay trouvés: {len(products)}')
            
        except Exception as e:
            Actor.log.error(f'Erreur lors du scraping eBay: {str(e)}')
        
        return products
    
    async def _extract_product_info(self, container: BeautifulSoup) -> Optional[Product]:
        """Extrait les informations d'un produit depuis son conteneur."""
        try:
            # Titre du produit
            title_elem = container.find('h3', class_='s-item__title') or container.find('a', class_='s-item__link')
            if not title_elem:
                return None
            
            title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
            if not title_link:
                return None
                
            title = self.clean_text(title_link.get_text())
            product_url = title_link.get('href', '')
            
            # Prix
            price = None
            currency = 'USD'
            
            price_elem = container.find('span', class_='s-item__price')
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
            img_elem = container.find('img', class_='s-item__image')
            image_url = img_elem.get('src') if img_elem else None
            
            # Note et avis (moins commun sur eBay)
            rating = None
            reviews_count = None
            
            rating_elem = container.find('span', class_='clipped')
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating = self.extract_rating(rating_text)
            
            # Disponibilité et type de vente
            availability = 'Disponible'
            condition_elem = container.find('span', class_='SECONDARY_INFO')
            if condition_elem:
                availability = self.clean_text(condition_elem.get_text())
            
            # Type de vente (Achat immédiat, Enchère, etc.)
            sale_type_elem = container.find('span', class_='s-item__purchase-options-with-icon')
            if sale_type_elem:
                sale_type = self.clean_text(sale_type_elem.get_text())
                availability += f' - {sale_type}'
            
            # Vendeur
            seller = 'eBay Seller'
            seller_elem = container.find('span', class_='s-item__seller-info-text')
            if seller_elem:
                seller = self.clean_text(seller_elem.get_text())
            
            # Localisation
            location_elem = container.find('span', class_='s-item__location')
            location = None
            if location_elem:
                location = self.clean_text(location_elem.get_text())
            
            # Frais de livraison
            shipping_elem = container.find('span', class_='s-item__shipping')
            shipping_info = None
            if shipping_elem:
                shipping_info = self.clean_text(shipping_elem.get_text())
            
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
                description=f'Localisation: {location}' + (f' - Livraison: {shipping_info}' if shipping_info else '') if location else shipping_info
            )
            
        except Exception as e:
            Actor.log.warning(f'Erreur extraction produit eBay: {str(e)}')
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[dict]:
        """Récupère les détails complets d'un produit eBay."""
        try:
            soup = await self.get_page_content(product_url)
            if not soup:
                return None
            
            details = {}
            
            # Description
            desc_elem = soup.find('div', {'id': 'desc_div'}) or soup.find('div', class_='u-flL condText')
            if desc_elem:
                details['description'] = self.clean_text(desc_elem.get_text())
            
            # Condition de l'objet
            condition_elem = soup.find('div', {'id': 'u_kp_1'}) or soup.find('span', {'id': 'cc_condText'})
            if condition_elem:
                details['condition'] = self.clean_text(condition_elem.get_text())
            
            # Numéro d'objet eBay
            item_number_elem = soup.find('span', {'id': 'x-item-title-label'})
            if item_number_elem:
                item_text = item_number_elem.get_text()
                if '#' in item_text:
                    details['sku'] = item_text.split('#')[-1].strip()
            
            # Informations sur le vendeur
            seller_info_elem = soup.find('span', class_='mbg-nw')
            if seller_info_elem:
                details['seller_info'] = self.clean_text(seller_info_elem.get_text())
            
            return details
            
        except Exception as e:
            Actor.log.warning(f'Erreur récupération détails eBay: {str(e)}')
            return None