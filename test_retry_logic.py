#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la nouvelle logique de retry pour le scraper e-commerce.
Ce script teste spécifiquement la logique qui garantit 50 produits
avec au moins 5 produits par plateforme sur 20 tentatives maximum.
"""

import asyncio
import json
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Mock de l'environnement Apify
class MockActor:
    @staticmethod
    async def get_input():
        return {
            'platforms': ['amazon', 'ebay'],  # Test avec 2 plateformes
            'searchTerms': ['iPhone'],
            'maxResults': 50,  # Objectif: 50 produits
            'trackPrices': True,
            'trackStock': True,
            'trackTrends': False
        }
    
    @staticmethod
    async def push_data(data):
        print(f"[MOCK] Données envoyées: {len(data.get('products', []))} produits")
    
    @staticmethod
    async def __aenter__():
        return MockActor
    
    @staticmethod
    async def __aexit__(exc_type, exc_val, exc_tb):
        pass

# Mock des scrapers avec simulation de résultats progressifs
class MockProduct:
    def __init__(self, title, price, url, platform):
        self.title = title
        self.price = price
        self.url = url
        self.platform = platform
        self.currency = 'EUR'
        self.availability = 'En stock'
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'title': self.title,
            'price': self.price,
            'currency': self.currency,
            'url': self.url,
            'platform': self.platform,
            'availability': self.availability,
            'timestamp': self.timestamp
        }

class MockScraper:
    def __init__(self, platform, max_results=25):
        self.platform = platform
        self.max_results = max_results
        self.call_count = 0
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def search_products(self, search_term):
        self.call_count += 1
        print(f"[MOCK] {self.platform} - Appel #{self.call_count} pour '{search_term}'")
        
        # Simuler des résultats progressifs
        if self.platform == 'amazon':
            # Amazon trouve 3 produits par tentative
            products = [
                MockProduct(f"iPhone 15 Amazon #{i + (self.call_count-1)*3}", 800 + i*10, 
                           f"https://amazon.fr/iphone-{i + (self.call_count-1)*3}", 'amazon')
                for i in range(3)
            ]
        elif self.platform == 'ebay':
            # eBay trouve 2 produits par tentative
            products = [
                MockProduct(f"iPhone 15 eBay #{i + (self.call_count-1)*2}", 750 + i*15, 
                           f"https://ebay.fr/iphone-{i + (self.call_count-1)*2}", 'ebay')
                for i in range(2)
            ]
        else:
            products = []
        
        # Simuler un délai de réseau
        await asyncio.sleep(0.5)
        
        print(f"[MOCK] {self.platform} - Retourne {len(products)} produits")
        return products

# Injection des mocks
import sys
sys.modules['apify'] = MagicMock()
sys.modules['apify'].Actor = MockActor

# Import du module principal après les mocks
from src.main import EcommerceScraper
from src.utils import safe_log

async def test_retry_logic():
    """Test de la logique de retry intelligente."""
    print("🧪 Test de la logique de retry intelligente")
    print("📋 Objectif: 50 produits avec minimum 5 par plateforme")
    print("🔄 Maximum: 20 tentatives")
    print()
    
    # Configuration de test
    config = {
        'platforms': ['amazon', 'ebay'],
        'searchTerms': ['iPhone'],
        'maxResults': 50,
        'trackPrices': True,
        'trackStock': True,
        'trackTrends': False
    }
    
    # Créer le scraper
    scraper = EcommerceScraper(config)
    
    # Remplacer les scrapers par des mocks
    scraper.scrapers = {
        'amazon': MockScraper('amazon'),
        'ebay': MockScraper('ebay')
    }
    
    print("⏳ Démarrage du test...")
    start_time = datetime.now()
    
    # Lancer le scraping avec la nouvelle logique
    products = await scraper.scrape_all_platforms()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print()
    print("📊 Résultats du test:")
    print(f"⏱️  Durée: {duration:.1f} secondes")
    print(f"📦 Total produits: {len(products)}")
    
    # Analyser les résultats par plateforme
    platform_counts = {}
    for product in products:
        platform = product['platform']
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    print("\n📈 Répartition par plateforme:")
    for platform, count in platform_counts.items():
        status = "✅" if count >= 5 else "❌"
        print(f"  {platform}: {count} produits {status}")
    
    # Vérifier les objectifs
    total_ok = len(products) >= 50
    min_per_platform_ok = all(count >= 5 for count in platform_counts.values())
    
    print("\n🎯 Validation des objectifs:")
    print(f"  Total ≥ 50: {'✅' if total_ok else '❌'} ({len(products)}/50)")
    print(f"  Min 5/plateforme: {'✅' if min_per_platform_ok else '❌'}")
    
    # Afficher les appels par scraper
    print("\n📞 Statistiques d'appels:")
    for platform, mock_scraper in scraper.scrapers.items():
        print(f"  {platform}: {mock_scraper.call_count} appels")
    
    # Sauvegarder les résultats
    output_file = 'test_retry_output.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_config': config,
            'results': {
                'total_products': len(products),
                'platform_counts': platform_counts,
                'duration_seconds': duration,
                'objectives_met': {
                    'total_target': total_ok,
                    'min_per_platform': min_per_platform_ok
                },
                'scraper_calls': {platform: scraper.call_count for platform, scraper in scraper.scrapers.items()}
            },
            'products': products
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés dans {output_file}")
    
    if total_ok and min_per_platform_ok:
        print("\n🎉 Test réussi! La logique de retry fonctionne correctement.")
        return True
    else:
        print("\n❌ Test échoué! La logique de retry nécessite des ajustements.")
        return False

if __name__ == '__main__':
    print("🧪 Test de la logique de retry - Scraper E-commerce")
    print("=" * 60)
    
    try:
        success = asyncio.run(test_retry_logic())
        exit_code = 0 if success else 1
    except Exception as e:
        print(f"\n💥 Erreur durant le test: {e}")
        exit_code = 1
    
    print("\n" + "=" * 60)
    print(f"🏁 Test terminé avec le code de sortie: {exit_code}")
    exit(exit_code)