"""Scraper pour Amazon avec techniques anti-détection avancées."""

import asyncio
import random
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from apify import Actor

from .base_scraper import BaseScraper, Product

# Import de la fonction safe_log depuis utils
from ..utils import safe_log


class AmazonScraper(BaseScraper):
    """Scraper spécialisé pour Amazon avec techniques anti-détection avancées."""
    
    def __init__(self, max_results: int = 50, domain: str = 'amazon.com'):
        super().__init__(max_results)
        self.domain = domain
        self.base_url = f'https://www.{domain}'
        
        # URLs alternatives pour éviter la détection (inspiré des actors Apify)
        self.search_endpoints = [
            '/s?k={}',
            '/s?k={}&ref=sr_pg_1',
            '/s?k={}&i=aps&ref=nb_sb_noss',
            '/s?k={}&sprefix={}&ref=nb_sb_noss_1',
            '/s?k={}&crid=random&sprefix={}&ref=nb_sb_noss'
        ]
        
        # Configuration retry inspirée des actors Apify
        self.max_retries = 3
        self.retry_delay_base = 5.0
        self.use_residential_proxy = True
        
        # Sélecteurs multiples pour robustesse
        self.product_selectors = [
            'div[data-component-type="s-search-result"]',
            'div[data-asin]:not([data-asin=""])',
            '.s-result-item[data-asin]',
            '[data-cel-widget="search_result"]'
        ]
    
    def get_platform_name(self) -> str:
        return 'Amazon'
    
    async def search_products(self, search_term: str) -> List[Product]:
        """Recherche des produits sur Amazon avec techniques anti-détection avancées."""
        products = []
        
        try:
            # Headers rotatifs inspirés des actors Apify performants
            await self._setup_amazon_headers()
            
            # Essayer plusieurs stratégies de recherche
            for strategy in range(3):
                strategy_products = await self._try_search_strategy(search_term, strategy)
                products.extend(strategy_products)
                
                if len(products) >= self.max_results:
                    break
                    
                # Délai entre stratégies
                await self.random_delay(3.0, 8.0)
            
            await safe_log('info', f'Amazon: Total {len(products)} produits extraits')
            return products[:self.max_results]
            
        except Exception as e:
            await safe_log('error', f'Erreur lors de la recherche Amazon: {str(e)}')
            return products
    
    async def _setup_amazon_headers(self):
        """Configure des headers rotatifs pour Amazon."""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        amazon_headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive',
            'DNT': '1'
        }
        
        # Mettre à jour les headers de session
        self.session.headers.update(amazon_headers)
    
    async def _try_search_strategy(self, search_term: str, strategy: int) -> List[Product]:
        """Essaie une stratégie de recherche spécifique."""
        products = []
        
        try:
            # Stratégie 0: Endpoints standards
            # Stratégie 1: Endpoints avec paramètres supplémentaires  
            # Stratégie 2: Recherche par catégorie
            
            endpoints_to_try = self.search_endpoints[strategy:strategy+2] if strategy < 2 else self.search_endpoints[:2]
            
            for i, endpoint in enumerate(endpoints_to_try):
                for retry in range(self.max_retries):
                    try:
                        # Construire l'URL avec gestion des placeholders multiples
                        if endpoint.count('{}') == 2:
                            search_url = f'{self.base_url}{endpoint.format(quote_plus(search_term), quote_plus(search_term))}'
                        else:
                            search_url = f'{self.base_url}{endpoint.format(quote_plus(search_term))}'
                        
                        await safe_log('info', f'Amazon stratégie {strategy+1}, endpoint {i+1}, tentative {retry+1}: {search_url[:100]}...')
                        
                        # Délai progressif avec retry
                        delay = self.retry_delay_base * (retry + 1) + random.uniform(2.0, 8.0)
                        await asyncio.sleep(delay)
                        
                        soup = await self._get_page_with_retry(search_url)
                        if not soup:
                            continue
                        
                        # Détection de blocage améliorée
                        if await self._is_blocked(soup):
                            await safe_log('warning', f'Blocage détecté, retry {retry+1}/{self.max_retries}')
                            if retry < self.max_retries - 1:
                                await self._rotate_headers()
                                continue
                            else:
                                break
                        
                        # Extraction avec sélecteurs multiples
                        product_containers = await self._find_product_containers(soup)
                        
                        if product_containers:
                            await safe_log('info', f'Trouvé {len(product_containers)} conteneurs de produits')
                            
                            # Extraire les produits avec limite
                            extracted_count = 0
                            for container in product_containers:
                                if len(products) >= self.max_results:
                                    break
                                    
                                product = await self._extract_product_info_enhanced(container)
                                if product:
                                    products.append(product)
                                    extracted_count += 1
                                    await safe_log('info', f'Produit Amazon extrait: {product.title[:50]}...')
                                
                                # Petit délai entre extractions
                                await asyncio.sleep(random.uniform(0.3, 1.5))
                            
                            await safe_log('info', f'Extraits {extracted_count} produits de cette page')
                            break  # Succès, sortir de la boucle retry
                        
                        else:
                            await safe_log('warning', f'Aucun conteneur de produit trouvé')
                            
                    except Exception as e:
                        await safe_log('error', f'Erreur endpoint {i+1}, retry {retry+1}: {str(e)}')
                        if retry == self.max_retries - 1:
                            await safe_log('error', f'Échec définitif pour endpoint {i+1}')
            
            await safe_log('info', f'Total produits Amazon trouvés: {len(products)}')
            
        except Exception as e:
            await safe_log('error', f'Erreur lors du scraping Amazon: {str(e)}')
        
        return products
    
    async def _get_page_with_retry(self, url: str) -> Optional[BeautifulSoup]:
        """Récupère une page avec retry et gestion d'erreurs."""
        try:
            return await self.get_page_content(url)
        except Exception as e:
            await safe_log('error', f'Erreur lors de la récupération de page: {str(e)}')
            return None
    
    async def _is_blocked(self, soup: BeautifulSoup) -> bool:
        """Détecte si on a été bloqué par Amazon."""
        # Indicateurs de blocage inspirés des actors Apify
        block_indicators = [
            soup.find('img', {'alt': 'captcha'}),
            'robot' in soup.get_text().lower(),
            'blocked' in soup.get_text().lower(),
            soup.find('form', {'action': lambda x: x and 'captcha' in x}),
            'sorry, we just need to make sure you\'re not a robot' in soup.get_text().lower(),
            soup.find('div', {'id': 'captchacharacters'})
        ]
        
        return any(block_indicators)
    
    async def _rotate_headers(self):
        """Fait tourner les headers pour éviter la détection."""
        await self._setup_amazon_headers()
        await safe_log('info', 'Headers rotés pour éviter la détection')
    
    async def _find_product_containers(self, soup: BeautifulSoup) -> List:
        """Trouve les conteneurs de produits avec sélecteurs multiples."""
        for selector in self.product_selectors:
            try:
                containers = soup.select(selector)
                if containers:
                    await safe_log('info', f'Sélecteur réussi: {selector} ({len(containers)} éléments)')
                    return containers
            except Exception as e:
                await safe_log('warning', f'Erreur sélecteur {selector}: {str(e)}')
                continue
        
        # Fallback vers les anciens sélecteurs
        fallback_containers = soup.find_all('div', {'data-asin': True})
        if fallback_containers:
            await safe_log('info', f'Fallback sélecteur réussi ({len(fallback_containers)} éléments)')
        
        return fallback_containers
    
    async def _extract_product_info_enhanced(self, container: BeautifulSoup) -> Optional[Product]:
        """Extraction améliorée des informations produit avec sélecteurs robustes."""
        try:
            # Extraction du titre avec sélecteurs multiples
            title = await self._extract_title(container)
            if not title:
                return None
            
            # Extraction du prix avec sélecteurs multiples
            price, currency = await self._extract_price(container)
            
            # Extraction de l'URL
            url = await self._extract_url(container)
            
            # Extraction de l'image
            image_url = await self._extract_image(container)
            
            # Extraction du rating
            rating = await self._extract_rating(container)
            
            # Extraction de l'ASIN
            asin = container.get('data-asin', '')
            
            return Product(
                title=title,
                price=price,
                currency=currency,
                url=url,
                image_url=image_url,
                platform='Amazon',
                availability='In Stock',  # Amazon par défaut
                rating=rating,
                asin=asin,
                scraped_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            await safe_log('error', f'Erreur extraction produit: {str(e)}')
            return None
    
    async def _extract_title(self, container: BeautifulSoup) -> Optional[str]:
        """Extrait le titre avec sélecteurs multiples."""
        title_selectors = [
            'h2 a span',
            'h2 span',
            '.s-size-mini span',
            '[data-cy="title-recipe-title"]',
            '.a-size-base-plus',
            '.a-size-medium'
        ]
        
        for selector in title_selectors:
            try:
                element = container.select_one(selector)
                if element and element.get_text(strip=True):
                    return element.get_text(strip=True)
            except:
                continue
        
        return None
    
    async def _extract_price(self, container: BeautifulSoup) -> tuple[Optional[float], Optional[str]]:
        """Extrait le prix avec sélecteurs multiples."""
        price_selectors = [
            '.a-price-whole',
            '.a-price .a-offscreen',
            '.a-price-range .a-offscreen',
            '.a-price-symbol + .a-price-whole'
        ]
        
        for selector in price_selectors:
            try:
                element = container.select_one(selector)
                if element:
                    price_text = element.get_text(strip=True)
                    # Extraction du prix numérique
                    import re
                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                    if price_match:
                        price = float(price_match.group())
                        currency = '$'  # Par défaut USD pour Amazon.com
                        return price, currency
            except:
                continue
        
        return None, None
    
    async def _extract_url(self, container: BeautifulSoup) -> Optional[str]:
        """Extrait l'URL du produit."""
        url_selectors = [
            'h2 a',
            '.a-link-normal',
            'a[href*="/dp/"]'
        ]
        
        for selector in url_selectors:
            try:
                element = container.select_one(selector)
                if element and element.get('href'):
                    href = element.get('href')
                    if href.startswith('/'):
                        return f'{self.base_url}{href}'
                    return href
            except:
                continue
        
        return None
    
    async def _extract_image(self, container: BeautifulSoup) -> Optional[str]:
        """Extrait l'URL de l'image."""
        try:
            img = container.select_one('img')
            if img:
                return img.get('src') or img.get('data-src')
        except:
            pass
        return None
    
    async def _extract_rating(self, container: BeautifulSoup) -> Optional[float]:
        """Extrait la note du produit."""
        try:
            rating_element = container.select_one('.a-icon-alt')
            if rating_element:
                rating_text = rating_element.get_text()
                import re
                rating_match = re.search(r'(\d+\.\d+)', rating_text)
                if rating_match:
                    return float(rating_match.group(1))
        except:
            pass
        return None
    
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