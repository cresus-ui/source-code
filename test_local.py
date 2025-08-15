#!/usr/bin/env python3
"""
Script de test local pour l'application de scraping e-commerce.
Ce script simule l'environnement Apify pour permettre de tester localement.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Configuration des chemins
project_root = Path(__file__).parent
src_path = project_root / "src"

# Ajouter les chemins au PYTHONPATH
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# Mock de l'environnement Apify pour les tests locaux
class MockActor:
    """Mock de la classe Actor d'Apify pour les tests locaux."""
    
    class Log:
        @staticmethod
        async def info(message):
            print(f"[INFO] {message}")
            
        @staticmethod
        async def warning(message):
            print(f"[WARNING] {message}")
            
        @staticmethod
        async def error(message):
            print(f"[ERROR] {message}")
    
    log = Log()
    
    @staticmethod
    async def get_input():
        """Retourne une configuration de test par défaut."""
        return {
            "search_terms": ["iPhone 15"],
            "platforms": ["amazon"],
            "max_products_per_platform": 3,
            "include_reviews": False,
            "include_images": False,
            "price_tracking": False,
            "stock_monitoring": False,
            "trend_analysis": False,
            "export_format": "json",
            "delay_between_requests": 3.0,
            "max_retries": 2,
            "timeout": 30,
            "user_agent_rotation": True,
            "proxy_rotation": False,
            "headless_mode": True,
            "anti_detection": True,
            "respect_robots_txt": True,
            "rate_limiting": True
        }
    
    @staticmethod
    async def push_data(data):
        """Simule la sauvegarde des données."""
        if isinstance(data, list):
            print(f"[DATA] Données sauvegardées: {len(data)} éléments")
        else:
            print(f"[DATA] Données sauvegardées: 1 élément")
            data = [data]
        
        # Sauvegarder dans un fichier local pour inspection
        output_file = project_root / "test_output.json"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"[DATA] Résultats sauvegardés dans {output_file}")
        except Exception as e:
            print(f"[ERROR] Erreur lors de la sauvegarde: {e}")
    
    @staticmethod
    async def set_status_message(message):
        """Simule la mise à jour du statut."""
        print(f"[STATUS] {message}")

def setup_mock_environment():
    """Configure l'environnement mock pour éviter les problèmes d'imports."""
    # Mock du module apify
    import types
    apify_mock = types.ModuleType('apify')
    apify_mock.Actor = MockActor
    sys.modules['apify'] = apify_mock
    
    # Mock de safe_log pour éviter les imports relatifs
    def mock_safe_log(level, message):
        if level == 'info':
            print(f"[INFO] {message}")
        elif level == 'warning':
            print(f"[WARNING] {message}")
        elif level == 'error':
            print(f"[ERROR] {message}")
        else:
            print(f"[{level.upper()}] {message}")
    
    # Créer un module utils mock
    utils_mock = types.ModuleType('utils')
    utils_mock.safe_log = mock_safe_log
    sys.modules['utils'] = utils_mock
    
    print("✅ Environnement mock configuré")

async def test_simple_scraping():
    """Test simple de scraping sans les modules complexes."""
    print("=== Test Simple de Scraping ===")
    
    try:
        import httpx
        from bs4 import BeautifulSoup
        import random
        import time
        
        # Configuration simple
        search_term = "iPhone 15"
        base_url = "https://www.amazon.fr"
        search_url = f"{base_url}/s?k={search_term.replace(' ', '+')}"
        
        print(f"🔍 Recherche: {search_term}")
        print(f"🌐 URL: {search_url}")
        
        # Headers pour éviter la détection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Délai aléatoire
        delay = random.uniform(2, 4)
        print(f"⏳ Attente de {delay:.1f} secondes...")
        await asyncio.sleep(delay)
        
        # Requête HTTP
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            print("📡 Envoi de la requête...")
            response = await client.get(search_url)
            
            if response.status_code == 200:
                print(f"✅ Réponse reçue (status: {response.status_code})")
                
                # Parser le HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Rechercher les produits (sélecteurs Amazon basiques)
                products = []
                
                # Différents sélecteurs possibles pour Amazon
                selectors = [
                    '[data-component-type="s-search-result"]',
                    '.s-result-item',
                    '[data-asin]'
                ]
                
                product_elements = []
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        product_elements = elements[:3]  # Limiter à 3 produits
                        print(f"📦 Trouvé {len(elements)} produits avec le sélecteur: {selector}")
                        break
                
                if not product_elements:
                    print("⚠️ Aucun produit trouvé avec les sélecteurs standards")
                    # Essayer de trouver des liens de produits
                    links = soup.find_all('a', href=True)
                    product_links = [link for link in links if '/dp/' in link.get('href', '')]
                    print(f"🔗 Trouvé {len(product_links)} liens de produits potentiels")
                    
                    if product_links:
                        for i, link in enumerate(product_links[:2]):
                            title_elem = link.find(text=True)
                            if title_elem and len(title_elem.strip()) > 10:
                                products.append({
                                    'title': title_elem.strip()[:100],
                                    'url': base_url + link['href'] if link['href'].startswith('/') else link['href'],
                                    'price': 'N/A',
                                    'currency': 'EUR',
                                    'source': 'amazon_simple_test',
                                    'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
                                })
                else:
                    # Parser les produits trouvés
                    for i, element in enumerate(product_elements):
                        try:
                            # Titre
                            title_selectors = ['h2 a span', 'h2 span', '.a-text-normal', 'h3']
                            title = 'Produit sans titre'
                            for sel in title_selectors:
                                title_elem = element.select_one(sel)
                                if title_elem:
                                    title = title_elem.get_text(strip=True)
                                    break
                            
                            # Prix
                            price_selectors = ['.a-price-whole', '.a-offscreen', '.a-price .a-offscreen']
                            price = 'N/A'
                            for sel in price_selectors:
                                price_elem = element.select_one(sel)
                                if price_elem:
                                    price = price_elem.get_text(strip=True)
                                    break
                            
                            # URL
                            url = 'N/A'
                            link_elem = element.select_one('h2 a, .a-link-normal')
                            if link_elem and link_elem.get('href'):
                                href = link_elem['href']
                                url = base_url + href if href.startswith('/') else href
                            
                            product = {
                                'title': title[:100],
                                'price': price,
                                'currency': 'EUR',
                                'url': url,
                                'source': 'amazon_simple_test',
                                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
                            }
                            
                            products.append(product)
                            
                        except Exception as e:
                            print(f"⚠️ Erreur lors du parsing du produit {i+1}: {e}")
                
                if products:
                    print(f"\n✅ {len(products)} produits extraits avec succès!")
                    
                    # Afficher les résultats
                    for i, product in enumerate(products):
                        print(f"\n📱 Produit {i+1}:")
                        print(f"   Titre: {product['title']}")
                        print(f"   Prix: {product['price']} {product['currency']}")
                        print(f"   URL: {product['url'][:60]}...")
                    
                    # Sauvegarder
                    await MockActor.push_data(products)
                    return True
                else:
                    print("❌ Aucun produit extrait")
                    return False
                    
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                if response.status_code == 503:
                    print("   Possible détection anti-bot")
                return False
                
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_main():
    """Test principal."""
    print("=== Test Local du Scraper E-commerce ===")
    
    # Configuration de l'environnement
    setup_mock_environment()
    
    # Test de scraping simple
    success = await test_simple_scraping()
    
    if success:
        print("\n🎉 Test terminé avec succès!")
        print("📄 Vérifiez le fichier 'test_output.json' pour voir les résultats détaillés.")
    else:
        print("\n💥 Test échoué")
        print("💡 Cela peut être dû à:")
        print("   - Détection anti-bot d'Amazon")
        print("   - Changement de structure HTML")
        print("   - Problème de connexion réseau")
    
    return success

def main():
    """Fonction principale."""
    print("🚀 Test Local - Scraper E-commerce")
    print(f"📁 Répertoire: {project_root}")
    print("🎯 Objectif: Test simple de scraping Amazon")
    print("⚠️  Note: Ce test utilise une approche simplifiée")
    print("\n⏳ Démarrage...\n")
    
    try:
        success = asyncio.run(test_main())
        
        if success:
            print("\n✅ Test réussi!")
            return 0
        else:
            print("\n❌ Test échoué")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrompu par l'utilisateur")
        return 0
    except Exception as e:
        print(f"\n💥 Erreur fatale: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)