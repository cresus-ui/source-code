"""Scraper pour les boutiques Shopify."""

from typing import List, Optional
from datetime import datetime
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from apify import Actor

from .base_scraper import BaseScraper, Product

# Import de la fonction safe_log depuis utils
from ..utils import safe_log


class ShopifyScraper(BaseScraper):
    """Scraper spécialisé pour les boutiques Shopify."""
    
    def __init__(self, max_results: int = 50, domains: List[str] = None):
        super().__init__(max_results)
        self.domains = domains or ['shopify.com']
        self.current_domain = None
    
    def get_platform_name(self) -> str:
        return 'Shopify'
    
    async def search_products(self, search_term: str) -> List[Product]:
        """Recherche des produits sur les boutiques Shopify."""
        all_products = []
        
        for domain in self.domains:
            self.current_domain = domain
            products = await self._search_on_domain(domain, search_term)
            all_products.extend(products)
            
            if len(all_products) >= self.max_results:
                break
        
        return all_products[:self.max_results]
    
    async def _search_on_domain(self, domain: str, search_term: str) -> List[Product]:
        """Recherche des produits sur un domaine Shopify spécifique."""
        products = []
        
        try:
            # Assurer que le domaine a le bon format
            if not domain.startswith('http'):
                base_url = f'https://{domain}'
            else:
                base_url = domain
            
            # Construction de l'URL de recherche Shopify
            search_url = f'{base_url}/search?q={quote_plus(search_term)}&type=product'
            await safe_log('info', f'Recherche Shopify sur {domain}: {search_url}')
            
            soup = await self.get_page_content(search_url)
            if not soup:
                # Essayer l'API de recherche Shopify
                api_url = f'{base_url}/search/suggest.json?q={quote_plus(search_term)}&resources[type]=product'
                return await self._search_via_api(base_url, api_url)
            
            # Sélecteurs pour les résultats de recherche Shopify
            product_containers = (
                soup.find_all('div', class_='product-item') or
                soup.find_all('div', class_='grid-product') or
                soup.find_all('article', class_='product-card') or
                soup.find_all('div', class_='product-card')
            )
            
            for container in product_containers:
                product = await self._extract_product_info(container, base_url)
                if product:
                    products.append(product)
                    await safe_log('info', f'Produit Shopify extrait: {product.title[:50]}...')
            
            await safe_log('info', f'Total produits Shopify trouvés sur {domain}: {len(products)}')
            
        except Exception as e:
            await safe_log('error', f'Erreur lors du scraping Shopify sur {domain}: {str(e)}')
        
        return products
    
    async def _search_via_api(self, base_url: str, api_url: str) -> List[Product]:
        """Recherche via l'API Shopify si disponible."""
        products = []
        
        try:
            response = await self.session.get(api_url)
            if response.status_code == 200:
                data = response.json()
                
                if 'resources' in data and 'results' in data['resources']:
                    for item in data['resources']['results']['products'][:self.max_results]:
                        product = await self._extract_product_from_api(item, base_url)
                        if product:
                            products.append(product)
            
        except Exception as e:
            await safe_log('warning', f'Erreur API Shopify: {str(e)}')
        
        return products
    
    async def _extract_product_info(self, container: BeautifulSoup, base_url: str) -> Optional[Product]:
        """Extrait les informations d'un produit depuis son conteneur."""
        try:
            # Titre du produit
            title_elem = (
                container.find('h3', class_='product-title') or
                container.find('h2', class_='product-title') or
                container.find('a', class_='product-link') or
                container.find('h3') or
                container.find('h2')
            )
            
            if not title_elem:
                return None
            
            # Récupération du lien
            if title_elem.name == 'a':
                title_link = title_elem
            else:
                title_link = title_elem.find('a') or container.find('a')
            
            if not title_link:
                return None
                
            title = self.clean_text(title_link.get_text())
            product_url = urljoin(base_url, title_link.get('href', ''))
            
            # Prix
            price = None
            currency = 'USD'
            
            price_elem = (
                container.find('span', class_='price') or
                container.find('div', class_='price') or
                container.find('span', class_='money') or
                container.find('div', class_='product-price')
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
                elif 'CAD' in price_text or 'C$' in price_text:
                    currency = 'CAD'
            
            # Image
            img_elem = container.find('img')
            image_url = None
            if img_elem:
                img_src = img_elem.get('src') or img_elem.get('data-src')
                if img_src:
                    image_url = urljoin(base_url, img_src)
            
            # Note et avis (moins commun sur Shopify)
            rating = None
            reviews_count = None
            
            rating_elem = container.find('div', class_='rating') or container.find('span', class_='stars')
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating = self.extract_rating(rating_text)
            
            # Disponibilité
            availability = 'Disponible'
            
            # Vérification du stock
            stock_elem = container.find('span', class_='sold-out') or container.find('div', class_='sold-out')
            if stock_elem:
                availability = 'Rupture de stock'
            
            # Badge de vente ou promotion
            badge_elem = container.find('span', class_='badge') or container.find('div', class_='sale-badge')
            badge_info = ''
            if badge_elem:
                badge_info = self.clean_text(badge_elem.get_text())
            
            # Vendeur (nom de la boutique Shopify)
            seller = self.current_domain
            
            # Variantes de produit
            variants_elem = container.find('div', class_='product-variants')
            variants_info = ''
            if variants_elem:
                variants_info = self.clean_text(variants_elem.get_text())
            
            description = ''
            if badge_info:
                description += f'Promotion: {badge_info}'
            if variants_info:
                description += f' - Variantes: {variants_info}' if description else f'Variantes: {variants_info}'
            
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
            await safe_log('warning', f'Erreur extraction produit Shopify: {str(e)}')
            return None
    
    async def _extract_product_from_api(self, item: dict, base_url: str) -> Optional[Product]:
        """Extrait les informations d'un produit depuis les données API."""
        try:
            title = item.get('title', '')
            product_url = urljoin(base_url, item.get('url', ''))
            
            # Prix depuis l'API
            price = None
            currency = 'USD'
            
            if 'price' in item:
                price = float(item['price']) / 100  # Shopify stocke les prix en centimes
            
            # Image
            image_url = None
            if 'image' in item:
                image_url = urljoin(base_url, item['image'])
            
            # Disponibilité
            availability = 'Disponible' if item.get('available', True) else 'Rupture de stock'
            
            return Product(
                title=title,
                price=price,
                currency=currency,
                url=product_url,
                image_url=image_url,
                rating=None,
                reviews_count=None,
                availability=availability,
                seller=self.current_domain,
                platform=self.get_platform_name(),
                scraped_at=datetime.now()
            )
            
        except Exception as e:
            await safe_log('warning', f'Erreur extraction produit API Shopify: {str(e)}')
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[dict]:
        """Récupère les détails complets d'un produit Shopify."""
        try:
            soup = await self.get_page_content(product_url)
            if not soup:
                return None
            
            details = {}
            
            # Description détaillée
            desc_elem = soup.find('div', class_='product-description') or soup.find('div', class_='rte')
            if desc_elem:
                details['description'] = self.clean_text(desc_elem.get_text())
            
            # Variantes de produit
            variants_section = soup.find('div', class_='product-variants') or soup.find('form', class_='product-form')
            if variants_section:
                variants = {}
                select_elements = variants_section.find_all('select')
                for select in select_elements:
                    variant_name = select.get('name', 'variant')
                    options = [option.get_text() for option in select.find_all('option') if option.get('value')]
                    variants[variant_name] = options
                details['variants'] = variants
            
            # Informations sur la livraison
            shipping_elem = soup.find('div', class_='shipping-info')
            if shipping_elem:
                details['shipping_info'] = self.clean_text(shipping_elem.get_text())
            
            return details
            
        except Exception as e:
            await safe_log('warning', f'Erreur récupération détails Shopify: {str(e)}')
            return None