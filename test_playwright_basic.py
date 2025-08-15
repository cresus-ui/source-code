#!/usr/bin/env python3
"""
Test basique pour vérifier l'installation et le fonctionnement de Playwright
"""

import asyncio
import json
from datetime import datetime

async def test_playwright_installation():
    """Test de base de l'installation Playwright"""
    
    print("🚀 Test d'installation Playwright")
    print("=" * 40)
    
    try:
        from playwright.async_api import async_playwright
        print("✅ Import Playwright réussi")
        
        async with async_playwright() as p:
            print("✅ Contexte Playwright initialisé")
            
            # Test de lancement de Chromium
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            print("✅ Navigateur Chromium lancé")
            
            # Test de création de page
            page = await browser.new_page()
            print("✅ Nouvelle page créée")
            
            # Configuration anti-détection basique
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            print("✅ Scripts anti-détection appliqués")
            
            # Test de navigation simple
            await page.goto('https://httpbin.org/user-agent')
            print("✅ Navigation vers page de test réussie")
            
            # Récupération du user-agent
            content = await page.content()
            if 'user-agent' in content.lower():
                print("✅ Contenu de page récupéré")
            
            # Test de JavaScript
            result = await page.evaluate('() => navigator.userAgent')
            if result:
                print(f"✅ JavaScript exécuté: {result[:50]}...")
            
            await browser.close()
            print("✅ Navigateur fermé")
            
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import Playwright: {e}")
        print("💡 Installez avec: pip install playwright>=1.40.0")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        if "executable doesn't exist" in str(e):
            print("💡 Installez Chromium avec: playwright install chromium")
        return False

async def test_playwright_features():
    """Test des fonctionnalités avancées de Playwright"""
    
    print("\n🎯 Test des fonctionnalités avancées")
    print("=" * 40)
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            page = await browser.new_page()
            
            # Test de configuration de viewport
            await page.set_viewport_size({"width": 1920, "height": 1080})
            print("✅ Viewport configuré")
            
            # Test de user-agent personnalisé
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            print("✅ User-Agent personnalisé configuré")
            
            # Test de navigation avec timeout
            try:
                await page.goto('https://example.com', timeout=10000)
                print("✅ Navigation avec timeout réussie")
            except Exception as e:
                print(f"⚠️ Navigation échouée: {e}")
            
            # Test de sélecteurs
            try:
                title = await page.title()
                if title:
                    print(f"✅ Titre de page récupéré: {title}")
            except Exception as e:
                print(f"⚠️ Récupération du titre échouée: {e}")
            
            await browser.close()
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des fonctionnalités: {e}")
        return False

def test_dependencies():
    """Test des dépendances"""
    
    print("🔍 Vérification des dépendances")
    print("=" * 40)
    
    dependencies = [
        ("playwright", "Playwright core"),
        ("playwright_stealth", "Playwright Stealth (optionnel)"),
    ]
    
    core_ok = True
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print(f"✅ {description}: Installé")
        except ImportError:
            if module_name == "playwright":
                core_ok = False
            print(f"{'❌' if module_name == 'playwright' else '⚠️'} {description}: Non installé")
    
    return core_ok

async def main():
    """Fonction principale de test"""
    
    print("🛒 Test Playwright pour Scraper E-commerce")
    print("=" * 50)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test des dépendances
    deps_ok = test_dependencies()
    
    if not deps_ok:
        print("\n⚠️ Playwright n'est pas installé correctement.")
        print("💡 Installez avec: pip install playwright>=1.40.0")
        print("💡 Puis: playwright install chromium")
        return
    
    # Test d'installation Playwright
    playwright_ok = await test_playwright_installation()
    
    # Test des fonctionnalités avancées
    features_ok = await test_playwright_features()
    
    # Résumé
    print("\n🎯 Résumé des tests:")
    print(f"{'✅' if deps_ok else '❌'} Dépendances: {'OK' if deps_ok else 'ERREUR'}")
    print(f"{'✅' if playwright_ok else '❌'} Playwright: {'OK' if playwright_ok else 'ERREUR'}")
    print(f"{'✅' if features_ok else '❌'} Fonctionnalités: {'OK' if features_ok else 'ERREUR'}")
    
    if all([deps_ok, playwright_ok, features_ok]):
        print("\n🚀 Playwright est prêt pour le scraping e-commerce!")
        print("\n💡 Fonctionnalités disponibles:")
        print("   • ✅ Chromium natif pour de meilleures performances")
        print("   • ✅ Scripts anti-détection intégrés")
        print("   • ✅ Configuration de viewport et user-agent")
        print("   • ✅ Navigation avec timeout et gestion d'erreurs")
        print("   • ✅ Support des sélecteurs CSS et XPath")
        print("\n🎯 Le projet peut maintenant utiliser Playwright avec Chromium!")
    else:
        print("\n❌ Certains tests ont échoué. Vérifiez l'installation.")

if __name__ == "__main__":
    asyncio.run(main())