#!/usr/bin/env python3
"""
Test de démonstration du scraper Playwright avec Chromium
Ce test montre les améliorations de performance et d'anti-détection
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scrapers.amazon_playwright_scraper import AmazonPlaywrightScraper
from scrapers.multi_platform_playwright_scraper import MultiPlatformPlaywrightScraper
from utils.logging_utils import safe_log

async def test_amazon_playwright():
    """Test du scraper Amazon avec Playwright"""
    print("\n=== Test Amazon Playwright Scraper ===")
    
    scraper = AmazonPlaywrightScraper(max_results=3, headless=True)
    
    try:
        await safe_log('info', 'Démarrage du test Amazon Playwright')
        results = await scraper.search_products('smartphone')
        
        print(f"Produits trouvés: {len(results)}")
        for i, product in enumerate(results, 1):
            print(f"{i}. {product.get('title', 'N/A')[:50]}...")
            print(f"   Prix: {product.get('price', 'N/A')}")
            print(f"   ASIN: {product.get('asin', 'N/A')}")
            print(f"   URL: {product.get('url', 'N/A')[:80]}...")
            print()
            
        return results
        
    except Exception as e:
        await safe_log('error', f'Erreur Amazon Playwright: {e}')
        print(f"Erreur: {e}")
        return []
    finally:
        await scraper.close()

async def test_multi_platform_playwright():
    """Test du scraper multi-plateformes avec Playwright"""
    print("\n=== Test Multi-Platform Playwright Scraper ===")
    
    scraper = MultiPlatformPlaywrightScraper(max_results=10, headless=True)
    
    try:
        await safe_log('info', 'Démarrage du test multi-plateformes Playwright')
        
        # Test sur différentes plateformes
        platforms = ['ebay', 'walmart', 'etsy']
        all_results = {}
        
        for platform in platforms:
            print(f"\nTest {platform.upper()}...")
            try:
                results = await scraper.search_platform(platform, 'smartphone', max_results=3)
                all_results[platform] = results
                print(f"  Produits trouvés: {len(results)}")
                
                for i, product in enumerate(results[:2], 1):  # Afficher seulement les 2 premiers
                    print(f"  {i}. {product.get('title', 'N/A')[:40]}...")
                    print(f"     Prix: {product.get('price', 'N/A')}")
                    
            except Exception as e:
                await safe_log('error', f'Erreur {platform}: {e}')
                print(f"  Erreur {platform}: {e}")
                all_results[platform] = []
        
        return all_results
        
    except Exception as e:
        await safe_log('error', f'Erreur multi-plateformes: {e}')
        print(f"Erreur générale: {e}")
        return {}
    finally:
        await scraper.close()

async def main():
    """Fonction principale de test"""
    print("🚀 Démonstration des scrapers Playwright avec Chromium")
    print("📊 Améliorations: Performance, Anti-détection, Stabilité")
    print("=" * 60)
    
    # Test Amazon Playwright
    amazon_results = await test_amazon_playwright()
    
    # Test Multi-Platform Playwright
    multi_results = await test_multi_platform_playwright()
    
    # Sauvegarde des résultats
    output_file = 'test_playwright_demo_output.json'
    results_summary = {
        'timestamp': asyncio.get_event_loop().time(),
        'amazon_playwright': {
            'count': len(amazon_results),
            'products': amazon_results
        },
        'multi_platform_playwright': {
            'platforms': {platform: {'count': len(results), 'products': results} 
                         for platform, results in multi_results.items()}
        },
        'performance_notes': {
            'chromium_engine': 'Utilisé pour tous les tests',
            'anti_detection': 'Empreintes digitales réalistes, user-agents rotatifs',
            'stealth_mode': 'Scripts anti-détection injectés',
            'proxy_support': 'Prêt pour proxies résidentiels'
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Résultats sauvegardés dans: {output_file}")
    print("\n📈 Avantages Playwright + Chromium:")
    print("   • Meilleure performance que Selenium")
    print("   • Anti-détection avancée")
    print("   • Support natif des proxies")
    print("   • Gestion JavaScript optimisée")
    print("   • Empreintes digitales réalistes")
    
    # Statistiques finales
    total_products = len(amazon_results) + sum(len(results) for results in multi_results.values())
    print(f"\n🎯 Total produits récupérés: {total_products}")
    
if __name__ == '__main__':
    asyncio.run(main())