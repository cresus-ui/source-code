"""Scraper Amazon utilisant Playwright avec Chromium pour des performances optimales."""

import asyncio
import random
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from apify import Actor
from playwright.async_api import Page

from .playwright_scraper import PlaywrightScraper
from .base_scraper import Product
from ..utils import safe_log


class AmazonPlaywrightScraper(PlaywrightScraper):
    """Scraper Amazon utilisant Playwright avec Chromium pour contourner les détections."""
    
    def __init__(self, max_results: int = 50, domain: str = 'amazon.com', headless: bool = True):
        super().__init__(max_results, headless, use_stealth=True)
        self.domain = domain
        self.base_url = f'https://www.{domain}'
        
        # URLs de recherche alternatives pour éviter la détection
        self.search_endpoints = [
            '/s?k={}',
            '/s?k={}&ref=sr_pg_1',
            '/s?k={}&i=aps&ref=nb_sb_noss',
            '/s?k={}&sprefix={}&ref=nb_sb_noss_1'
        ]
        
        # Sélecteurs Amazon spécifiques
        self.product_selectors = [
            'div[data-component-type="s-search-result"]',
            'div[data-asin]:not([data-asin=""])',
            '.s-result-item[data-asin]',
            '[data-cel-widget="search_result"]'
        ]
        
        # Configuration anti-détection spécifique à Amazon
        self.amazon_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def get_platform_name(self) -> str:
        return 'Amazon-Playwright'
    
    async def search_products(self, search_term: str) -> List[Product]:
        """Recherche des produits sur Amazon en utilisant Playwright."""
        products = []
        
        try:
            safe_log(f"Démarrage de la recherche Amazon Playwright pour: {search_term}")
            
            # Initialisation du navigateur si nécessaire
            if not self.browser:
                await self.init_browser()
            
            # Création d'une nouvelle page
            page = await self.create_page()
            
            # Configuration des headers spécifiques à Amazon
            await page.set_extra_http_headers(self.amazon_headers)
            
            # Tentative avec différents endpoints
            for endpoint in self.search_endpoints:
                try:
                    search_url = self.base_url + endpoint.format(quote_plus(search_term))
                    safe_log(f"Tentative avec URL: {search_url}")
                    
                    # Navigation avec retry
                    if await self.navigate_with_retry(page, search_url):
                        # Vérification si on est bloqué
                        if await self._check_if_blocked(page):
                            safe_log("Détection de blocage Amazon, tentative de contournement...")
                            await self._handle_amazon_captcha(page)
                            continue
                        
                        # Extraction des produits
                        page_products = await self._extract_amazon_products(page)
                        products.extend(page_products)
                        
                        if products:
                            safe_log(f"Trouvé {len(products)} produits avec l'endpoint {endpoint}")
                            break
                    
                    # Délai entre les tentatives
                    await asyncio.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    safe_log(f"Erreur avec l'endpoint {endpoint}: {e}")
                    continue
            
            await page.close()
            
        except Exception as e:
            safe_log(f"Erreur lors de la recherche Amazon: {e}")
        
        finally:
            # Nettoyage
            try:
                await self.close()
            except:
                pass
        
        safe_log(f"Recherche Amazon terminée. {len(products)} produits trouvés.")
        return products[:self.max_results]
    
    async def _check_if_blocked(self, page: Page) -> bool:
        """Vérifie si la page indique un blocage ou un CAPTCHA."""
        try:
            # Vérification des indicateurs de blocage
            blocked_indicators = [
                'captcha',
                'robot',
                'automated',
                'blocked',
                'access denied',
                'sorry, something went wrong'
            ]
            
            page_content = await page.content()
            page_text = page_content.lower()
            
            for indicator in blocked_indicators:
                if indicator in page_text:
                    return True
            
            # Vérification des sélecteurs de CAPTCHA
            captcha_selectors = [
                '[name="captcha"]',
                '#captchacharacters',
                '.captcha-container',
                '[data-testid="captcha"]'
            ]
            
            for selector in captcha_selectors:
                if await page.query_selector(selector):
                    return True
            
            return False
            
        except Exception as e:
            safe_log(f"Erreur lors de la vérification de blocage: {e}")
            return False
    
    async def _handle_amazon_captcha(self, page: Page) -> bool:
        """Tente de gérer les CAPTCHAs Amazon (basique)."""
        try:
            safe_log("Tentative de gestion du CAPTCHA Amazon...")
            
            # Attendre un peu pour voir si le CAPTCHA se résout automatiquement
            await asyncio.sleep(random.uniform(5, 10))
            
            # Recharger la page
            await page.reload(wait_until='domcontentloaded')
            
            # Vérifier si le CAPTCHA est toujours présent
            return not await self._check_if_blocked(page)
            
        except Exception as e:
            safe_log(f"Erreur lors de la gestion du CAPTCHA: {e}")
            return False
    
    async def _extract_amazon_products(self, page: Page) -> List[Product]:
        """Extrait les produits Amazon de la page."""
        products = []
        
        try:
            # Attendre que les résultats se chargent
            await page.wait_for_timeout(3000)
            
            # Essayer différents sélecteurs
            for selector in self.product_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        safe_log(f"Trouvé {len(elements)} éléments avec le sélecteur {selector}")
                        
                        for element in elements[:self.max_results]:
                            product = await self._extract_amazon_product_from_element(element)
                            if product:
                                products.append(product)
                        
                        if products:
                            break  # Utiliser le premier sélecteur qui fonctionne
                            
                except Exception as e:
                    safe_log(f"Erreur avec le sélecteur Amazon {selector}: {e}")
                    continue
            
        except Exception as e:
            safe_log(f"Erreur lors de l'extraction des produits Amazon: {e}")
        
        return products
    
    async def _extract_amazon_product_from_element(self, element) -> Optional[Product]:
        """Extrait les informations d'un produit Amazon à partir d'un élément DOM."""
        try:
            # Extraction du titre
            title_selectors = [
                'h2 a span',
                'h2 span',
                '.s-title-instructions-style h2 a span',
                '[data-cy="title-recipe-title"]',
                '.s-link-style a span'
            ]
            
            title = "Titre non trouvé"
            for selector in title_selectors:
                title_element = await element.query_selector(selector)
                if title_element:
                    title = await title_element.inner_text()
                    if title and title.strip():
                        break
            
            # Extraction du prix
            price_selectors = [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '.a-price-range .a-offscreen',
                '[data-cy="price-recipe"]'
            ]
            
            price = "Prix non trouvé"
            for selector in price_selectors:
                price_element = await element.query_selector(selector)
                if price_element:
                    price = await price_element.inner_text()
                    if price and price.strip():
                        break
            
            # Extraction de l'URL
            url = ""
            link_element = await element.query_selector('h2 a, .s-link-style a')
            if link_element:
                href = await link_element.get_attribute('href')
                if href:
                    url = urljoin(self.base_url, href)
            
            # Extraction de l'image
            image_url = ""
            img_element = await element.query_selector('img')
            if img_element:
                src = await img_element.get_attribute('src')
                if src:
                    image_url = src
            
            # Extraction de la note
            rating = ""
            rating_element = await element.query_selector('.a-icon-alt, [aria-label*="stars"]')
            if rating_element:
                rating_text = await rating_element.get_attribute('aria-label')
                if rating_text:
                    rating = rating_text
            
            # Extraction du nombre d'avis
            reviews_count = ""
            reviews_element = await element.query_selector('.a-size-base, [aria-label*="reviews"]')
            if reviews_element:
                reviews_text = await reviews_element.inner_text()
                if reviews_text and any(char.isdigit() for char in reviews_text):
                    reviews_count = reviews_text
            
            # Extraction de l'ASIN
            asin = ""
            asin_attr = await element.get_attribute('data-asin')
            if asin_attr:
                asin = asin_attr
            
            # Nettoyage des données
            title = title.strip()[:200] if title else "Titre non disponible"
            price = price.strip() if price else "Prix non disponible"
            rating = rating.strip() if rating else ""
            reviews_count = reviews_count.strip() if reviews_count else ""
            
            return Product(
                title=title,
                price=price,
                currency="USD",
                url=url,
                image_url=image_url,
                rating=rating,
                reviews_count=reviews_count,
                asin=asin,
                availability="En stock",
                scraped_at=datetime.now()
            )
            
        except Exception as e:
            safe_log(f"Erreur lors de l'extraction du produit Amazon: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """Récupère les détails complets d'un produit Amazon."""
        try:
            if not self.browser:
                await self.init_browser()
            
            page = await self.create_page()
            await page.set_extra_http_headers(self.amazon_headers)
            
            if await self.navigate_with_retry(page, product_url):
                # Extraction des détails complets
                details = await self._extract_product_details(page)
                await page.close()
                return details
            
            await page.close()
            return None
            
        except Exception as e:
            safe_log(f"Erreur lors de la récupération des détails: {e}")
            return None
    
    async def _extract_product_details(self, page: Page) -> Dict[str, Any]:
        """Extrait les détails complets d'un produit Amazon."""
        details = {}
        
        try:
            # Titre du produit
            title_element = await page.query_selector('#productTitle')
            if title_element:
                details['title'] = await title_element.inner_text()
            
            # Prix
            price_selectors = ['.a-price .a-offscreen', '.a-price-whole', '#price_inside_buybox']
            for selector in price_selectors:
                price_element = await page.query_selector(selector)
                if price_element:
                    details['price'] = await price_element.inner_text()
                    break
            
            # Description
            desc_element = await page.query_selector('#feature-bullets ul, #productDescription')
            if desc_element:
                details['description'] = await desc_element.inner_text()
            
            # Images
            img_elements = await page.query_selector_all('#altImages img, #landingImage')
            if img_elements:
                images = []
                for img in img_elements[:5]:  # Limiter à 5 images
                    src = await img.get_attribute('src')
                    if src:
                        images.append(src)
                details['images'] = images
            
            # Disponibilité
            availability_element = await page.query_selector('#availability span')
            if availability_element:
                details['availability'] = await availability_element.inner_text()
            
            # Vendeur
            seller_element = await page.query_selector('#sellerProfileTriggerId, #bylineInfo')
            if seller_element:
                details['seller'] = await seller_element.inner_text()
            
        except Exception as e:
            safe_log(f"Erreur lors de l'extraction des détails: {e}")
        
        return details