"""Scraper utilisant Playwright avec Chromium pour des performances optimales."""

import asyncio
import random
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from apify import Actor
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth import stealth_async

from .base_scraper import BaseScraper, Product
from ..utils import safe_log


class PlaywrightScraper(BaseScraper):
    """Scraper utilisant Playwright avec Chromium pour des performances optimales."""
    
    def __init__(self, max_results: int = 50, headless: bool = True, use_stealth: bool = True):
        super().__init__(max_results)
        self.headless = headless
        self.use_stealth = use_stealth
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        # Configuration Chromium optimisée pour Apify
        self.browser_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-gpu',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
        ]
        
        # User agents rotatifs pour éviter la détection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        ]
    
    async def init_browser(self) -> None:
        """Initialise le navigateur Chromium avec Playwright."""
        try:
            playwright = await async_playwright().start()
            
            # Lancement de Chromium avec configuration optimisée
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=self.browser_args,
                slow_mo=random.randint(50, 150)  # Délai aléatoire pour simuler un comportement humain
            )
            
            # Création du contexte avec empreinte digitale réaliste
            self.context = await self.browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # New York
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                }
            )
            
            safe_log("Navigateur Chromium initialisé avec succès")
            
        except Exception as e:
            safe_log(f"Erreur lors de l'initialisation du navigateur: {e}")
            raise
    
    async def create_page(self) -> Page:
        """Crée une nouvelle page avec configuration anti-détection."""
        if not self.context:
            await self.init_browser()
        
        page = await self.context.new_page()
        
        # Application du mode stealth si activé
        if self.use_stealth:
            await stealth_async(page)
        
        # Injection de scripts anti-détection
        await page.add_init_script("""
            // Masquer les propriétés WebDriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Masquer les propriétés Playwright
            delete window.playwright;
            delete window.__playwright;
            
            // Simuler des plugins réalistes
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Masquer l'automation
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Simuler une résolution d'écran réaliste
            Object.defineProperty(screen, 'width', {
                get: () => 1920,
            });
            Object.defineProperty(screen, 'height', {
                get: () => 1080,
            });
        """)
        
        # Configuration des timeouts
        page.set_default_timeout(30000)  # 30 secondes
        page.set_default_navigation_timeout(30000)
        
        return page
    
    async def navigate_with_retry(self, page: Page, url: str, max_retries: int = 3) -> bool:
        """Navigue vers une URL avec retry automatique."""
        for attempt in range(max_retries):
            try:
                # Délai aléatoire entre les tentatives
                if attempt > 0:
                    await asyncio.sleep(random.uniform(2, 5))
                
                # Navigation avec attente du chargement complet
                response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                if response and response.status < 400:
                    # Attente supplémentaire pour le JavaScript
                    await page.wait_for_timeout(random.randint(1000, 3000))
                    return True
                else:
                    safe_log(f"Réponse HTTP {response.status if response else 'None'} pour {url}")
                    
            except Exception as e:
                safe_log(f"Tentative {attempt + 1} échouée pour {url}: {e}")
                if attempt == max_retries - 1:
                    return False
        
        return False
    
    async def extract_products_from_page(self, page: Page, platform: str) -> List[Product]:
        """Extrait les produits d'une page en utilisant des sélecteurs spécifiques à la plateforme."""
        products = []
        
        try:
            # Attendre que les produits se chargent
            await page.wait_for_timeout(2000)
            
            # Sélecteurs par plateforme
            selectors = self._get_platform_selectors(platform)
            
            # Extraction des produits
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        safe_log(f"Trouvé {len(elements)} éléments avec le sélecteur {selector}")
                        
                        for element in elements[:self.max_results]:
                            product = await self._extract_product_from_element(element, platform)
                            if product:
                                products.append(product)
                        
                        if products:
                            break  # Utiliser le premier sélecteur qui fonctionne
                            
                except Exception as e:
                    safe_log(f"Erreur avec le sélecteur {selector}: {e}")
                    continue
            
        except Exception as e:
            safe_log(f"Erreur lors de l'extraction des produits: {e}")
        
        return products[:self.max_results]
    
    def _get_platform_selectors(self, platform: str) -> List[str]:
        """Retourne les sélecteurs CSS spécifiques à chaque plateforme."""
        selectors_map = {
            'amazon': [
                'div[data-component-type="s-search-result"]',
                'div[data-asin]:not([data-asin=""])',
                '.s-result-item[data-asin]',
                '[data-cel-widget="search_result"]'
            ],
            'ebay': [
                '.s-item',
                '.srp-results .s-item',
                '[data-view="mi:1686|iid:1"]'
            ],
            'walmart': [
                '[data-testid="item-stack"]',
                '[data-automation-id="product-title"]',
                '.mb0.ph1.pa0.bb.b--near-white.w-25'
            ],
            'etsy': [
                '.v2-listing-card',
                '.listing-link',
                '[data-test-id="listing"]'
            ]
        }
        
        return selectors_map.get(platform.lower(), [])
    
    async def _extract_product_from_element(self, element, platform: str) -> Optional[Product]:
        """Extrait les informations d'un produit à partir d'un élément DOM."""
        try:
            # Extraction basique - à adapter selon la plateforme
            title_element = await element.query_selector('h2, h3, .s-title, [data-testid="product-title"], .listing-link')
            title = await title_element.inner_text() if title_element else "Titre non trouvé"
            
            price_element = await element.query_selector('.a-price-whole, .s-price, .price, [data-testid="product-price"], .currency-value')
            price = await price_element.inner_text() if price_element else "Prix non trouvé"
            
            link_element = await element.query_selector('a')
            url = await link_element.get_attribute('href') if link_element else ""
            
            # Nettoyage et formatage
            title = title.strip()[:200] if title else "Titre non disponible"
            price = price.strip() if price else "Prix non disponible"
            
            if url and not url.startswith('http'):
                base_urls = {
                    'amazon': 'https://www.amazon.com',
                    'ebay': 'https://www.ebay.com',
                    'walmart': 'https://www.walmart.com',
                    'etsy': 'https://www.etsy.com'
                }
                url = urljoin(base_urls.get(platform.lower(), ''), url)
            
            return Product(
                title=title,
                price=price,
                currency="USD",
                url=url,
                image_url="",
                rating="",
                reviews_count="",
                asin="",
                availability="En stock",
                scraped_at=datetime.now()
            )
            
        except Exception as e:
            safe_log(f"Erreur lors de l'extraction du produit: {e}")
            return None
    
    async def close(self) -> None:
        """Ferme le navigateur et libère les ressources."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            safe_log("Navigateur fermé avec succès")
        except Exception as e:
            safe_log(f"Erreur lors de la fermeture du navigateur: {e}")
    
    def get_platform_name(self) -> str:
        return "Playwright-Chromium"
    
    async def search_products(self, search_term: str) -> List[Product]:
        """Méthode de base - à implémenter dans les classes dérivées."""
        raise NotImplementedError("Cette méthode doit être implémentée dans les classes dérivées")