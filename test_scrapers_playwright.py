#!/usr/bin/env python3
"""
Test des scrapers Playwright pour e-commerce
Test d'intégration complet avec Amazon et multi-plateformes
"""

import sys
import os
import asyncio
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from scrapers.amazon_playwright_scraper import AmazonPlaywrightScraper
    from scrapers.multi_platform_playwright_scraper import MultiPlatformPlaywrightScraper
    print("✅ Import des scrapers Playwright réussi")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)

async def test_amazon_playwright():
    """Test du scraper Amazon Playwright"""
    print("\n🔍 Test Amazon Playwright Scraper...")
    
    scraper = AmazonPlaywrightScraper()
    
    # URL de test Amazon
    test_url = "https://www.amazon.com/dp/B08N5WRWNW"  # Echo Dot
    
    try:
        print(f"📡 Scraping: {test_url}")
        result = await scraper.scrape_product(test_url)
        
        if result:
            print("✅ Scraping Amazon réussi!")
            print(f"📦 Produit: {result.get('title', 'N/A')[:50]}...")
            print(f"💰 Prix: {result.get('price', 'N/A')}")
            print(f"⭐ Note: {result.get('rating', 'N/A')}")
            print(f"📊 Stock: {result.get('availability', 'N/A')}")
            return True
        else:
            print("❌ Aucun résultat retourné")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du scraping Amazon: {e}")
        return False
    finally:
        await scraper.close()

async def test_multi_platform_playwright():
    """Test du scraper multi-plateformes Playwright"""
    print("\n🌐 Test Multi-Platform Playwright Scraper...")
    
    scraper = MultiPlatformPlaywrightScraper()
    
    # URLs de test pour différentes plateformes
    test_urls = [
        "https://www.amazon.com/dp/B08N5WRWNW",  # Amazon
        "https://www.ebay.com/itm/123456789",     # eBay (exemple)
    ]
    
    success_count = 0
    
    for url in test_urls:
        try:
            print(f"📡 Test URL: {url}")
            result = await scraper.scrape_product(url)
            
            if result:
                print(f"✅ Scraping réussi pour {url}")
                print(f"📦 Produit: {result.get('title', 'N/A')[:50]}...")
                success_count += 1
            else:
                print(f"⚠️ Aucun résultat pour {url}")
                
        except Exception as e:
            print(f"❌ Erreur pour {url}: {e}")
    
    await scraper.close()
    return success_count > 0

async def test_playwright_features():
    """Test des fonctionnalités Playwright spécifiques"""
    print("\n🎭 Test des fonctionnalités Playwright...")
    
    scraper = AmazonPlaywrightScraper()
    
    try:
        # Test d'initialisation
        await scraper._init_playwright()
        print("✅ Playwright initialisé")
        
        # Test de lancement du navigateur
        if scraper.browser:
            print("✅ Navigateur Chromium lancé")
            
            # Test de création de page
            page = await scraper.browser.new_page()
            print("✅ Nouvelle page créée")
            
            # Test de navigation simple
            await page.goto("https://httpbin.org/user-agent")
            content = await page.content()
            
            if "Mozilla" in content:
                print("✅ User-Agent configuré correctement")
            else:
                print("⚠️ User-Agent non détecté")
                
            await page.close()
            print("✅ Page fermée")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test Playwright: {e}")
        return False
    finally:
        await scraper.close()

async def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests Scrapers Playwright")
    print("=" * 50)
    
    tests_results = []
    
    # Test 1: Fonctionnalités Playwright de base
    result1 = await test_playwright_features()
    tests_results.append(("Fonctionnalités Playwright", result1))
    
    # Test 2: Scraper Amazon Playwright
    result2 = await test_amazon_playwright()
    tests_results.append(("Amazon Playwright Scraper", result2))
    
    # Test 3: Scraper Multi-Platform
    result3 = await test_multi_platform_playwright()
    tests_results.append(("Multi-Platform Scraper", result3))
    
    # Résumé des résultats
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    success_count = 0
    for test_name, success in tests_results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"{test_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n🎯 Résultat global: {success_count}/{len(tests_results)} tests réussis")
    
    if success_count == len(tests_results):
        print("🎉 Tous les tests Playwright sont réussis!")
        print("🚀 Le scraper e-commerce est prêt pour la production!")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez la configuration.")
    
    return success_count == len(tests_results)

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrompus par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erreur critique: {e}")
        sys.exit(1)