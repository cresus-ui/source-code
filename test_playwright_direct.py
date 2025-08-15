#!/usr/bin/env python3
"""
Test direct de Playwright pour e-commerce
Test sans dépendances complexes pour valider l'installation
"""

import asyncio
import sys
from datetime import datetime

async def test_playwright_installation():
    """Test de l'installation Playwright"""
    print("🔍 Test de l'installation Playwright...")
    
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright importé avec succès")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import Playwright: {e}")
        return False

async def test_playwright_stealth():
    """Test de l'installation Playwright Stealth"""
    print("🔍 Test de l'installation Playwright Stealth...")
    
    try:
        import playwright_stealth
        print("✅ Playwright Stealth importé avec succès")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import Playwright Stealth: {e}")
        return False

async def test_chromium_launch():
    """Test de lancement de Chromium"""
    print("🔍 Test de lancement de Chromium...")
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            print("📱 Lancement du navigateur Chromium...")
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            print("📄 Création d'une nouvelle page...")
            page = await browser.new_page()
            
            # Configuration anti-détection basique
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            })
            
            print("🌐 Navigation vers une page de test...")
            await page.goto('https://httpbin.org/user-agent', wait_until='networkidle')
            
            # Récupération du contenu
            content = await page.content()
            
            if 'Mozilla' in content:
                print("✅ User-Agent configuré correctement")
                success = True
            else:
                print("⚠️ User-Agent non détecté dans la réponse")
                success = False
            
            # Test de JavaScript
            print("⚡ Test d'exécution JavaScript...")
            js_result = await page.evaluate('() => navigator.userAgent')
            if js_result:
                print(f"✅ JavaScript exécuté: {js_result[:50]}...")
            else:
                print("❌ Échec de l'exécution JavaScript")
                success = False
            
            await page.close()
            await browser.close()
            
            print("✅ Test Chromium terminé avec succès")
            return success
            
    except Exception as e:
        print(f"❌ Erreur lors du test Chromium: {e}")
        return False

async def test_amazon_basic_scraping():
    """Test de scraping basique sur Amazon"""
    print("🔍 Test de scraping basique Amazon...")
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # Test sur une page Amazon simple
            print("📡 Navigation vers Amazon...")
            await page.goto('https://www.amazon.com', wait_until='networkidle', timeout=30000)
            
            # Vérification que la page s'est chargée
            title = await page.title()
            print(f"📄 Titre de la page: {title}")
            
            if 'Amazon' in title:
                print("✅ Navigation Amazon réussie")
                success = True
            else:
                print("⚠️ Titre Amazon non détecté")
                success = False
            
            # Test de recherche basique
            try:
                search_box = await page.wait_for_selector('#twotabsearchtextbox', timeout=10000)
                if search_box:
                    print("✅ Boîte de recherche Amazon détectée")
                else:
                    print("⚠️ Boîte de recherche non trouvée")
            except Exception as e:
                print(f"⚠️ Sélecteur de recherche non trouvé: {e}")
            
            await context.close()
            await browser.close()
            
            return success
            
    except Exception as e:
        print(f"❌ Erreur lors du test Amazon: {e}")
        return False

async def main():
    """Fonction principale de test"""
    print("🚀 Test direct Playwright pour E-commerce")
    print("=" * 50)
    print(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Installation Playwright", test_playwright_installation),
        ("Installation Playwright Stealth", test_playwright_stealth),
        ("Lancement Chromium", test_chromium_launch),
        ("Scraping Amazon basique", test_amazon_basic_scraping)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 Erreur critique dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé final
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS PLAYWRIGHT")
    print("=" * 50)
    
    success_count = 0
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"{test_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n🎯 Score: {success_count}/{len(results)} tests réussis")
    
    if success_count == len(results):
        print("\n🎉 TOUS LES TESTS PLAYWRIGHT RÉUSSIS!")
        print("🚀 Playwright est prêt pour le scraping e-commerce!")
        print("✨ Configuration optimale détectée")
    elif success_count >= len(results) * 0.75:
        print("\n✅ TESTS MAJORITAIREMENT RÉUSSIS")
        print("🔧 Quelques ajustements peuvent être nécessaires")
    else:
        print("\n⚠️ PLUSIEURS TESTS ONT ÉCHOUÉ")
        print("🔧 Vérifiez l'installation de Playwright")
        print("💡 Essayez: playwright install chromium")
    
    print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success_count >= len(results) * 0.75

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrompus par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)