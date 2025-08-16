"""Scraper multi-plateformes utilisant Playwright avec Chromium."""

import asyncio
import random
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import quote_plus, urljoin
from playwright.async_api import Page

from src.scrapers.playwright_scraper import PlaywrightScraper
from src.scrapers.base_scraper import Product
from src.utils import safe_log


class MultiPlatformPlaywrightScraper(PlaywrightScraper):
    """Scraper multi-plateformes utilisant Playwright avec Chromium pour des performances optimales."""
    
    def __init__(self, max_results: int = 50, headless: bool = True):
        super().__init__(max_results, headless, use_stealth=True)
        
        # Configuration des plateformes
        self.platforms_config = {
            'amazon': {
                'base_url': 'https://www.amazon.com',
                'search_path': '/s?k={}',
                'selectors': [
                    'div[data-component-type="s-search-result"]',
                    'div[data-asin]:not([data-asin=""])',
                    '.s-result-item[data-asin]'
                ],
                'title_selectors': ['h2 a span', 'h2 span', '.s-title-instructions-style h2 a span'],
                'price_selectors': ['.a-price-whole', '.a-price .a-offscreen'],
                'link_selectors': ['h2 a', '.s-link-style a']
            },
            'ebay': {
                'base_url': 'https://www.ebay.com',
                'search_path': '/sch/i.html?_nkw={}',
                'selectors': ['.s-item', '.srp-results .s-item'],
                'title_selectors': ['.s-item__title', 'h3.s-item__title'],
                'price_selectors': ['.s-item__price', '.notranslate'],
                'link_selectors': ['.s-item__link']
            },
            'walmart': {
                'base_url': 'https://www.walmart.com',
                'search_path': '/search?q={}',
                'selectors': ['[data-testid="item-stack"]', '[data-automation-id="product-title"]'],
                'title_selectors': ['[data-automation-id="product-title"]', 'span[data-automation-id="product-title"]'],
                'price_selectors': ['[data-testid="product-price"]', '.price-current'],
                'link_selectors': ['a[data-testid="product-title"]']
            },
            'etsy': {
                'base_url': 'https://www.etsy.com',
                'search_path': '/search?q={}',
                'selectors': ['.v2-listing-card', '.listing-link', '[data-test-id="listing"]'],
                'title_selectors': ['.listing-link', 'h3.v2-listing-card__title'],
                'price_selectors': ['.currency-value', '.price'],
                'link_selectors': ['.listing-link']
            }
        }
    
    def get_platform_name(self) -> str:
        return 'MultiPlatform-Playwright'
    
    async def search_all_platforms(self, search_term: str) -> Dict[str, List[Product]]:
        """Recherche sur toutes les plateformes en parallèle."""
        results = {}
        
        try:
            await safe_log('info', f"Démarrage de la recherche multi-plateformes pour: {search_term}")
            
            # Initialisation du navigateur
            await self.init_browser()
            
            # Recherche en parallèle sur toutes les plateformes
            tasks = []
            for platform in self.platforms_config.keys():
                task = self._search_platform(platform, search_term)
                tasks.append(task)
            
            # Exécution des tâches en parallèle
            platform_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Traitement des résultats
            for i, platform in enumerate(self.platforms_config.keys()):
                result = platform_results[i]
                if isinstance(result, Exception):
                    await safe_log('error', f"Erreur pour {platform}: {result}")
                    results[platform] = []
                else:
                    results[platform] = result
                    await safe_log('info', f"{platform}: {len(result)} produits trouvés")
            
        except Exception as e:
            await safe_log('error', f"Erreur lors de la recherche multi-plateformes: {e}")
        
        finally:
            await self.close()
        
        return results
    
    async def _search_platform(self, platform: str, search_term: str) -> List[Product]:
        """Recherche sur une plateforme spécifique."""
        products = []
        
        try:
            config = self.platforms_config[platform]
            search_url = config['base_url'] + config['search_path'].format(quote_plus(search_term))
            
            await safe_log("info", f"Recherche sur {platform}: {search_url}")
            
            # Création d'une page dédiée
            page = await self.create_page()
            
            # Configuration spécifique par plateforme
            await self._configure_page_for_platform(page, platform)
            
            # Navigation
            if await self.navigate_with_retry(page, search_url):
                # Vérification de blocage
                if await self._check_platform_blocking(page, platform):
                    await safe_log("warning", f"Blocage détecté sur {platform}")
                    await page.close()
                    return products
                
                # Extraction des produits
                products = await self._extract_platform_products(page, platform)
                
            await page.close()
            
        except Exception as e:
            await safe_log("error", f"Erreur lors de la recherche sur {platform}: {e}")
        
        return products[:self.max_results]
    
    async def _configure_page_for_platform(self, page: Page, platform: str) -> None:
        """Configure la page selon la plateforme."""
        try:
            # Headers spécifiques par plateforme
            platform_headers = {
                'amazon': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'max-age=0'
                },
                'ebay': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5'
                },
                'walmart': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9'
                },
                'etsy': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            }
            
            headers = platform_headers.get(platform, {})
            if headers:
                await page.set_extra_http_headers(headers)
            
            # Scripts spécifiques par plateforme
            if platform == 'amazon':
                await page.add_init_script("""
                    // Masquer les indicateurs d'automation spécifiques à Amazon
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                """)
            
        except Exception as e:
            await safe_log("error", f"Erreur lors de la configuration pour {platform}: {e}")
    
    async def _check_platform_blocking(self, page: Page, platform: str) -> bool:
        """Vérifie si la plateforme bloque l'accès."""
        try:
            page_content = await page.content()
            page_text = page_content.lower()
            
            # Indicateurs de blocage par plateforme
            blocking_indicators = {
                'amazon': ['captcha', 'robot', 'automated', 'blocked'],
                'ebay': ['blocked', 'access denied', 'security check'],
                'walmart': ['blocked', 'access denied', 'security'],
                'etsy': ['blocked', 'access denied', 'captcha']
            }
            
            indicators = blocking_indicators.get(platform, ['blocked', 'access denied'])
            
            for indicator in indicators:
                if indicator in page_text:
                    return True
            
            # Vérification des codes de statut d'erreur
            if any(error in page_text for error in ['403', '503', '429']):
                return True
            
            return False
            
        except Exception as e:
            await safe_log("error", f"Erreur lors de la vérification de blocage pour {platform}: {e}")
            return False
    
    async def _extract_platform_products(self, page: Page, platform: str) -> List[Product]:
        """Extrait les produits d'une plateforme spécifique."""
        products = []
        
        try:
            config = self.platforms_config[platform]
            
            # Attendre le chargement
            await page.wait_for_timeout(3000)
            
            # Essayer différents sélecteurs
            for selector in config['selectors']:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        await safe_log("info", f"{platform}: Trouvé {len(elements)} éléments avec {selector}")
                        
                        for element in elements[:self.max_results]:
                            product = await self._extract_product_from_platform_element(
                                element, platform, config
                            )
                            if product:
                                products.append(product)
                        
                        if products:
                            break
                            
                except Exception as e:
                    await safe_log("error", f"Erreur avec le sélecteur {selector} sur {platform}: {e}")
                    continue
            
        except Exception as e:
            await safe_log("error", f"Erreur lors de l'extraction sur {platform}: {e}")
        
        return products
    
    async def _extract_product_from_platform_element(self, element, platform: str, config: Dict) -> Optional[Product]:
        """Extrait un produit à partir d'un élément selon la plateforme."""
        try:
            # Extraction du titre
            title = "Titre non trouvé"
            for selector in config['title_selectors']:
                title_element = await element.query_selector(selector)
                if title_element:
                    title = await title_element.inner_text()
                    if title and title.strip():
                        break
            
            # Extraction du prix
            price = "Prix non trouvé"
            for selector in config['price_selectors']:
                price_element = await element.query_selector(selector)
                if price_element:
                    price = await price_element.inner_text()
                    if price and price.strip():
                        break
            
            # Extraction de l'URL
            url = ""
            for selector in config['link_selectors']:
                link_element = await element.query_selector(selector)
                if link_element:
                    href = await link_element.get_attribute('href')
                    if href:
                        if href.startswith('http'):
                            url = href
                        else:
                            url = urljoin(config['base_url'], href)
                        break
            
            # Extraction de l'image
            image_url = ""
            img_element = await element.query_selector('img')
            if img_element:
                src = await img_element.get_attribute('src')
                if src:
                    image_url = src if src.startswith('http') else urljoin(config['base_url'], src)
            
            # Extraction de l'ASIN (pour Amazon)
            asin = ""
            if platform == 'amazon':
                asin_attr = await element.get_attribute('data-asin')
                if asin_attr:
                    asin = asin_attr
            
            # Nettoyage des données
            title = title.strip()[:200] if title else "Titre non disponible"
            price = price.strip() if price else "Prix non disponible"
            
            return Product(
                title=title,
                price=price,
                currency="USD",
                url=url,
                image_url=image_url,
                rating="",
                reviews_count="",
                asin=asin,
                availability="En stock",
                scraped_at=datetime.now()
            )
            
        except Exception as e:
            await safe_log("error", f"Erreur lors de l'extraction du produit sur {platform}: {e}")
            return None
    
    async def search_products(self, search_term: str) -> List[Product]:
        """Recherche sur toutes les plateformes et retourne tous les produits."""
        all_results = await self.search_all_platforms(search_term)
        
        # Combiner tous les résultats
        all_products = []
        for platform, products in all_results.items():
            all_products.extend(products)
        
        return all_products[:self.max_results]
    
    async def search_specific_platform(self, platform: str, search_term: str) -> List[Product]:
        """Recherche sur une plateforme spécifique."""
        if platform not in self.platforms_config:
            await safe_log("warning", f"Plateforme {platform} non supportée")
            return []
        
        try:
            await self.init_browser()
            products = await self._search_platform(platform, search_term)
            await self.close()
            return products
        except Exception as e:
            await safe_log("error", f"Erreur lors de la recherche sur {platform}: {e}")
            return []