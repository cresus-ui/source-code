#!/usr/bin/env python3
"""
Test simple pour démontrer les fonctionnalités Playwright
"""

import sys
import os
import json
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_playwright_integration():
    """Test d'intégration Playwright avec le scraper principal"""
    
    print("🚀 Test d'intégration Playwright avec Chromium")
    print("=" * 50)
    
    # Configuration de test
    test_input = {
        "platforms": ["amazon"],
        "searchTerms": ["smartphone"],
        "maxResults": 5,
        "usePlaywright": True,
        "headless": True,
        "trackPrices": False,
        "trackStock": False,
        "trackTrends": False
    }
    
    print(f"📋 Configuration de test:")
    print(json.dumps(test_input, indent=2, ensure_ascii=False))
    print()
    
    try:
        # Import du scraper principal
        from main import EcommerceScraper
        
        print("✅ Import du scraper principal réussi")
        
        # Initialisation du scraper avec Playwright
        scraper = EcommerceScraper(
            use_playwright=test_input["usePlaywright"],
            headless=test_input["headless"]
        )
        
        print("✅ Initialisation du scraper Playwright réussie")
        
        # Test de l'initialisation des scrapers
        scraper.initialize_scrapers()
        
        print("✅ Initialisation des scrapers spécialisés réussie")
        print(f"📊 Scrapers disponibles: {list(scraper.scrapers.keys())}")
        
        # Vérification du type de scraper utilisé
        if 'amazon' in scraper.scrapers:
            scraper_type = type(scraper.scrapers['amazon']).__name__
            print(f"🎯 Type de scraper Amazon: {scraper_type}")
            
            if "Playwright" in scraper_type:
                print("✅ Scraper Playwright correctement initialisé")
            else:
                print("⚠️ Scraper traditionnel utilisé")
        
        print("\n🎉 Test d'intégration Playwright terminé avec succès!")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_dependencies():
    """Test des dépendances Playwright"""
    
    print("\n🔍 Vérification des dépendances Playwright")
    print("=" * 50)
    
    dependencies = [
        ("playwright", "Playwright core"),
        ("playwright_stealth", "Playwright Stealth"),
    ]
    
    all_ok = True
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print(f"✅ {description}: Installé")
        except ImportError:
            print(f"❌ {description}: Non installé")
            all_ok = False
    
    return all_ok

def main():
    """Fonction principale de test"""
    
    print("🛒 Test du Scraper E-commerce avec Playwright")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test des dépendances
    deps_ok = test_dependencies()
    
    if not deps_ok:
        print("\n⚠️ Certaines dépendances sont manquantes.")
        print("💡 Exécutez: pip install playwright>=1.40.0 playwright-stealth>=1.0.6")
        print("💡 Puis: playwright install chromium")
        return
    
    # Test d'intégration
    integration_ok = test_playwright_integration()
    
    if integration_ok:
        print("\n🎯 Résumé des tests:")
        print("✅ Dépendances Playwright: OK")
        print("✅ Intégration Playwright: OK")
        print("✅ Initialisation des scrapers: OK")
        print("\n🚀 Le projet est prêt à utiliser Playwright avec Chromium!")
    else:
        print("\n❌ Des erreurs ont été détectées lors des tests.")

if __name__ == "__main__":
    main()