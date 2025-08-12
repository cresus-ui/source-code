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

from src.scrapers import (
    AmazonScraper,
    EbayScraper,
    WalmartScraper,
    EtsyScraper,
    ShopifyScraper
)


class EcommerceScraper:
    """Orchestrateur principal pour le scraping multi-plateformes."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platforms = config.get('platforms', ['amazon'])
        self.search_terms = config.get('searchTerms', ['smartphone'])
        self.max_results = config.get('maxResults', 50)
        self.track_prices = config.get('trackPrices', True)
        self.track_stock = config.get('trackStock', True)
        self.track_trends = config.get('trackTrends', False)
        self.shopify_domains = config.get('shopifyDomains', [])
        
        self.scrapers = {}
        self.results = defaultdict(list)
        
    async def initialize_scrapers(self):
        """Initialise les scrapers pour chaque plateforme sélectionnée."""
        max_per_platform = max(1, self.max_results // len(self.platforms))
        
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
        """Lance le scraping sur toutes les plateformes sélectionnées."""
        all_products = []
        
        for search_term in self.search_terms:
            Actor.log.info(f'Recherche pour le terme: {search_term}')
            
            # Lancer le scraping en parallèle sur toutes les plateformes
            tasks = []
            for platform, scraper in self.scrapers.items():
                task = self._scrape_platform(platform, scraper, search_term)
                tasks.append(task)
            
            # Attendre que tous les scrapers terminent
            platform_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Traiter les résultats
            for i, result in enumerate(platform_results):
                platform = list(self.scrapers.keys())[i]
                if isinstance(result, Exception):
                    Actor.log.error(f'Erreur sur {platform}: {str(result)}')
                else:
                    self.results[platform].extend(result)
                    all_products.extend([product.to_dict() for product in result])
        
        return all_products
    
    async def _scrape_platform(self, platform: str, scraper, search_term: str):
        """Scrape une plateforme spécifique."""
        try:
            async with scraper:
                products = await scraper.search_products(search_term)
                Actor.log.info(f'{platform}: {len(products)} produits trouvés pour "{search_term}"')
                return products
        except Exception as e:
            Actor.log.error(f'Erreur lors du scraping {platform}: {str(e)}')
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
        
        Actor.log.info(f'Configuration reçue: {actor_input}')
        
        # Validation des paramètres
        if not actor_input.get('platforms'):
            raise ValueError('Au moins une plateforme doit être sélectionnée!')
        
        if not actor_input.get('searchTerms'):
            raise ValueError('Au moins un terme de recherche doit être fourni!')
        
        # Initialisation du scraper
        scraper = EcommerceScraper(actor_input)
        await scraper.initialize_scrapers()
        
        Actor.log.info(f'Scrapers initialisés pour: {", ".join(scraper.platforms)}')
        
        # Lancement du scraping
        products = await scraper.scrape_all_platforms()
        
        # Génération du rapport
        report = await scraper.generate_report(products)
        
        Actor.log.info(f'Scraping terminé: {len(products)} produits trouvés')
        
        # Sauvegarde des résultats
        await Actor.push_data(report)
        
        # Sauvegarde des produits individuels pour faciliter l'analyse
        for product in products:
            await Actor.push_data(product)
