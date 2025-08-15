"""Module defines the main entry point for the Apify Actor.

Scraper e-commerce multi-plateformes pour Amazon, eBay, Walmart, Etsy, Shopify
avec suivi automatique des prix, stocks et tendances.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

from apify import Actor

from .scrapers import (
    AmazonScraper,
    EbayScraper,
    WalmartScraper,
    EtsyScraper,
    ShopifyScraper
)

# Import des nouveaux scrapers Playwright
from .scrapers.amazon_playwright_scraper import AmazonPlaywrightScraper
from .scrapers.multi_platform_playwright_scraper import MultiPlatformPlaywrightScraper


# Import de safe_log depuis utils
from .utils import safe_log


async def retry_on_error(func, *args, max_retries: int = 20, delay: float = 1.0, **kwargs):
    """Fonction de retry qui tente une opération jusqu'à 20 fois en cas d'erreur.
    
    Args:
        func: La fonction à exécuter
        *args: Arguments positionnels pour la fonction
        max_retries: Nombre maximum de tentatives (défaut: 20)
        delay: Délai entre les tentatives en secondes (défaut: 1.0)
        **kwargs: Arguments nommés pour la fonction
    
    Returns:
        Le résultat de la fonction si succès
    
    Raises:
        Exception: La dernière exception si toutes les tentatives échouent
    """
    import asyncio
    
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            if attempt > 1:
                await safe_log('info', f'Succès après {attempt} tentatives')
            
            return result
            
        except Exception as e:
            last_exception = e
            await safe_log('warning', f'Tentative {attempt}/{max_retries} échouée: {str(e)}')
            
            if attempt < max_retries:
                await safe_log('info', f'Nouvelle tentative dans {delay} secondes...')
                await asyncio.sleep(delay)
            else:
                await safe_log('error', f'Toutes les {max_retries} tentatives ont échoué')
    
    # Si on arrive ici, toutes les tentatives ont échoué
    raise last_exception


class EcommerceScraper:
    """Orchestrateur principal pour le scraping multi-plateformes."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platforms = config.get('platforms', ['amazon', 'ebay', 'walmart', 'etsy', 'shopify'])
        self.search_terms = config.get('searchTerms', ['smartphone'])
        self.max_results = config.get('maxResults', 50)
        self.track_prices = config.get('trackPrices', True)
        self.track_stock = config.get('trackStock', True)
        self.track_trends = config.get('trackTrends', False)
        self.shopify_domains = config.get('shopifyDomains', [])
        self.use_playwright = config.get('usePlaywright', True)  # Nouveau: utiliser Playwright par défaut
        self.headless = config.get('headless', True)  # Mode headless pour Playwright
        
        self.scrapers = {}
        self.results = defaultdict(list)
        
    async def initialize_scrapers(self):
        """Initialise les scrapers pour chaque plateforme sélectionnée."""
        max_per_platform = max(1, self.max_results // len(self.platforms))
        
        await safe_log('info', f'Initialisation des scrapers (Playwright: {self.use_playwright})')
        
        if self.use_playwright:
            # Utilisation du scraper multi-plateformes Playwright
            await safe_log('info', 'Utilisation du scraper Playwright multi-plateformes')
            self.scrapers['multi_platform'] = MultiPlatformPlaywrightScraper(
                max_results=self.max_results,
                headless=self.headless
            )
            
            # Scraper Amazon spécialisé avec Playwright
            if 'amazon' in self.platforms:
                self.scrapers['amazon_playwright'] = AmazonPlaywrightScraper(
                    max_results=max_per_platform,
                    headless=self.headless
                )
        else:
            # Utilisation des scrapers traditionnels
            await safe_log('info', 'Utilisation des scrapers traditionnels')
            
            if 'amazon' in self.platforms:
                self.scrapers['amazon'] = AmazonScraper(max_results=max_per_platform)
                
            if 'ebay' in self.platforms:
                self.scrapers['ebay'] = EbayScraper(max_results=max_per_platform)
                
            if 'walmart' in self.platforms:
                self.scrapers['walmart'] = WalmartScraper(max_results=max_per_platform)
                
            if 'etsy' in self.platforms:
                self.scrapers['etsy'] = EtsyScraper(max_results=max_per_platform)
                
            if 'shopify' in self.platforms:
                domains = self.shopify_domains if self.shopify_domains else ['shopify.com']
                self.scrapers['shopify'] = ShopifyScraper(max_results=max_per_platform, domains=domains)
    
    async def scrape_all_platforms(self) -> List[Dict[str, Any]]:
        """Lance le scraping sur toutes les plateformes avec retry intelligent jusqu'à obtenir 50 produits."""
        all_products = []
        platform_products = {platform: [] for platform in self.scrapers.keys()}
        attempt = 0
        max_attempts = 20
        target_total = self.max_results
        min_per_platform = 5
        
        await safe_log('info', f'Objectif: {target_total} produits au total, minimum {min_per_platform} par plateforme')
        
        while attempt < max_attempts:
            attempt += 1
            await safe_log('info', f'Tentative {attempt}/{max_attempts}')
            
            # Vérifier si on a atteint l'objectif
            total_products = sum(len(products) for products in platform_products.values())
            platforms_with_min = sum(1 for products in platform_products.values() if len(products) >= min_per_platform)
            
            if total_products >= target_total and platforms_with_min == len(self.scrapers):
                await safe_log('info', f'Objectif atteint: {total_products} produits trouvés avec au moins {min_per_platform} par plateforme')
                break
            
            # Identifier les plateformes qui ont besoin de plus de produits
            platforms_to_scrape = []
            for platform in self.scrapers.keys():
                current_count = len(platform_products[platform])
                if current_count < min_per_platform or total_products < target_total:
                    platforms_to_scrape.append(platform)
            
            if not platforms_to_scrape:
                break
            
            await safe_log('info', f'Scraping des plateformes: {", ".join(platforms_to_scrape)}')
            
            # Scraper les plateformes qui ont besoin de plus de produits
            for search_term in self.search_terms:
                await safe_log('info', f'Recherche pour le terme: {search_term}')
                
                # Lancer le scraping en parallèle sur les plateformes sélectionnées
                tasks = []
                for platform in platforms_to_scrape:
                    if platform in self.scrapers:
                        scraper = self.scrapers[platform]
                        task = self._scrape_platform(platform, scraper, search_term)
                        tasks.append((platform, task))
                
                # Attendre que tous les scrapers terminent
                for platform, task in tasks:
                    try:
                        result = await task
                        if result:
                            # Éviter les doublons en vérifiant les URLs
                            existing_urls = set()
                            for p in platform_products[platform]:
                                if hasattr(p, 'to_dict'):
                                    existing_urls.add(p.to_dict().get('url', ''))
                                elif hasattr(p, 'url'):
                                    existing_urls.add(p.url)
                                else:
                                    existing_urls.add(p.get('url', '') if hasattr(p, 'get') else '')
                            
                            new_products = []
                            for p in result:
                                product_url = ''
                                if hasattr(p, 'to_dict'):
                                    product_url = p.to_dict().get('url', '')
                                elif hasattr(p, 'url'):
                                    product_url = p.url
                                else:
                                    product_url = p.get('url', '') if hasattr(p, 'get') else ''
                                
                                if product_url not in existing_urls:
                                    new_products.append(p)
                                    existing_urls.add(product_url)
                            
                            if new_products:
                                platform_products[platform].extend(new_products)
                                await safe_log('info', f'{platform}: +{len(new_products)} nouveaux produits (total: {len(platform_products[platform])})')
                    except Exception as e:
                        await safe_log('error', f'Erreur sur {platform}: {str(e)}')
            
            # Attendre un peu avant la prochaine tentative
            if attempt < max_attempts:
                await asyncio.sleep(2)
        
        # Compiler tous les produits
        for platform, products in platform_products.items():
            self.results[platform] = products
            all_products.extend([product.to_dict() for product in products])
        
        total_found = len(all_products)
        await safe_log('info', f'Scraping terminé après {attempt} tentatives: {total_found} produits trouvés')
        
        # Afficher le résumé par plateforme
        for platform, products in platform_products.items():
            count = len(products)
            status = "✓" if count >= min_per_platform else "✗"
            await safe_log('info', f'{platform}: {count} produits {status}')
        
        return all_products
    
    async def _scrape_platform(self, platform: str, scraper, search_term: str) -> list:
        """Scrape une plateforme spécifique avec gestion d'erreurs et retry automatique."""
        async def scrape_with_context():
            async with scraper:
                products = await scraper.search_products(search_term)
                await safe_log('info', f'{platform}: {len(products)} produits trouvés pour "{search_term}"')
                return products
        
        try:
            # Utilisation du système de retry pour plus de robustesse
            return await retry_on_error(scrape_with_context, max_retries=20, delay=2.0)
        except Exception as e:
            await safe_log('error', f'Échec définitif du scraping {platform} après 20 tentatives: {str(e)}')
            return []
    
    def analyze_prices(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyse les prix par plateforme et produit."""
        if not self.track_prices:
            return {}
        
        price_analysis = {
            'by_platform': defaultdict(list),
            'price_ranges': {},
            'best_deals': [],
            'average_prices': {}
        }
        
        # Grouper les prix par plateforme
        for product in products:
            if product.get('price'):
                platform = product['platform']
                price_analysis['by_platform'][platform].append(product['price'])
        
        # Calculer les statistiques
        for platform, prices in price_analysis['by_platform'].items():
            if prices:
                price_analysis['average_prices'][platform] = sum(prices) / len(prices)
                price_analysis['price_ranges'][platform] = {
                    'min': min(prices),
                    'max': max(prices),
                    'count': len(prices)
                }
        
        # Identifier les meilleures offres
        sorted_products = sorted(
            [p for p in products if p.get('price')],
            key=lambda x: x['price']
        )
        price_analysis['best_deals'] = sorted_products[:10]
        
        return price_analysis
    
    def analyze_stock(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyse la disponibilité des stocks."""
        if not self.track_stock:
            return {}
        
        stock_analysis = {
            'availability_by_platform': defaultdict(int),
            'out_of_stock_count': 0,
            'in_stock_count': 0,
            'stock_alerts': []
        }
        
        for product in products:
            availability = product.get('availability', '').lower()
            platform = product['platform']
            
            if 'stock' in availability or 'disponible' in availability:
                if 'rupture' in availability or 'out of stock' in availability:
                    stock_analysis['out_of_stock_count'] += 1
                    stock_analysis['stock_alerts'].append({
                        'product': product['title'],
                        'platform': platform,
                        'status': 'Rupture de stock'
                    })
                else:
                    stock_analysis['in_stock_count'] += 1
                    stock_analysis['availability_by_platform'][platform] += 1
        
        return stock_analysis
    
    def analyze_trends(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyse les tendances de vente."""
        if not self.track_trends:
            return {}
        
        trends_analysis = {
            'popular_products': [],
            'top_rated': [],
            'most_reviewed': [],
            'platform_popularity': defaultdict(int)
        }
        
        # Produits les mieux notés
        rated_products = [p for p in products if p.get('rating')]
        trends_analysis['top_rated'] = sorted(
            rated_products,
            key=lambda x: x['rating'],
            reverse=True
        )[:10]
        
        # Produits les plus commentés
        reviewed_products = [p for p in products if p.get('reviews_count')]
        trends_analysis['most_reviewed'] = sorted(
            reviewed_products,
            key=lambda x: x['reviews_count'],
            reverse=True
        )[:10]
        
        # Popularité par plateforme
        for product in products:
            trends_analysis['platform_popularity'][product['platform']] += 1
        
        return trends_analysis
    
    async def generate_report(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Génère un rapport complet des résultats."""
        report = {
            'summary': {
                'total_products': len(products),
                'platforms_scraped': list(self.scrapers.keys()),
                'search_terms': self.search_terms,
                'scraped_at': datetime.now().isoformat()
            },
            'products': products
        }
        
        # Ajouter les analyses si activées
        if self.track_prices:
            report['price_analysis'] = self.analyze_prices(products)
        
        if self.track_stock:
            report['stock_analysis'] = self.analyze_stock(products)
        
        if self.track_trends:
            report['trends_analysis'] = self.analyze_trends(products)
        
        return report


async def main() -> None:
    """Point d'entrée principal de l'Actor Apify."""
    async with Actor:
        # Récupération de la configuration
        actor_input = await Actor.get_input() or {
            'platforms': ['amazon'],
            'searchTerms': ['smartphone'],
            'maxResults': 50,
            'trackPrices': True,
            'trackStock': True,
            'trackTrends': False
        }
        
        await safe_log('info', f'Configuration reçue: {actor_input}')
        
        # Validation des paramètres
        if not actor_input.get('platforms'):
            raise ValueError('Au moins une plateforme doit être sélectionnée!')
        
        if not actor_input.get('searchTerms'):
            raise ValueError('Au moins un terme de recherche doit être fourni!')
        
        # Initialisation du scraper
        scraper = EcommerceScraper(actor_input)
        await scraper.initialize_scrapers()
        
        await safe_log('info', f'Scrapers initialisés pour: {", ".join(scraper.platforms)}')
        
        # Lancement du scraping
        products = await scraper.scrape_all_platforms()
        
        # Génération du rapport
        report = await scraper.generate_report(products)
        
        await safe_log('info', f'Scraping terminé: {len(products)} produits trouvés')
        
        # Sauvegarde des résultats
        await Actor.push_data(report)
        
        # Sauvegarde des produits individuels pour faciliter l'analyse
        for product in products:
            await Actor.push_data(product)
