"""Test rapide du scraper Amazon amélioré."""

import asyncio
import json
from datetime import datetime

from src.scrapers.amazon_scraper import AmazonScraper
from src.utils import safe_log

async def test_amazon_quick():
    """Test rapide du scraper Amazon avec timeout."""
    try:
        print("=== Test rapide Amazon ===")
        print(f"Début du test: {datetime.now()}")
        
        # Configuration du scraper avec paramètres réduits
        async with AmazonScraper(max_results=5, domain='amazon.com') as scraper:
            print("Scraper Amazon initialisé")
            
            # Test avec timeout de 60 secondes
            try:
                products = await asyncio.wait_for(
                    scraper.search_products('iPhone'),  # Terme plus simple
                    timeout=60.0
                )
                
                print(f"\n=== Résultats ===")
                print(f"Nombre de produits trouvés: {len(products)}")
                
                if products:
                    print("\n=== Premiers produits ===")
                    for i, product in enumerate(products[:3], 1):
                        print(f"{i}. {product.title[:60]}...")
                        print(f"   Prix: {product.price} {product.currency if product.currency else ''}")
                        print(f"   URL: {product.url[:80]}...")
                        print()
                    
                    # Sauvegarder les résultats
                    results = {
                        'timestamp': datetime.now().isoformat(),
                        'search_term': 'iPhone',
                        'total_products': len(products),
                        'products': [product.to_dict() for product in products]
                    }
                    
                    with open('test_amazon_quick_output.json', 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    
                    print(f"Résultats sauvegardés dans test_amazon_quick_output.json")
                    return len(products) > 0
                else:
                    print("Aucun produit trouvé")
                    return False
                    
            except asyncio.TimeoutError:
                print("Timeout atteint (60s) - Test interrompu")
                return False
                
    except Exception as e:
        print(f"Erreur lors du test: {str(e)}")
        return False

if __name__ == '__main__':
    success = asyncio.run(test_amazon_quick())
    print(f"\n=== Résultat final ===")
    print(f"Test {'RÉUSSI' if success else 'ÉCHOUÉ'}")
    exit(0 if success else 1)