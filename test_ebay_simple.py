#!/usr/bin/env python3
"""Test simple du scraper eBay pour vérifier le fonctionnement de base."""

import asyncio
import json
from src.scrapers.ebay_scraper import EbayScraper

async def test_ebay_simple():
    """Test simple du scraper eBay."""
    
    print("=== Test simple eBay ===")
    print("Terme de recherche: iPhone 15")
    print("Objectif: Vérifier que le scraper fonctionne")
    print("\n" + "="*40 + "\n")
    
    # Initialiser le scraper eBay
    async with EbayScraper(max_results=10) as scraper:
        # Lancer le scraping
        products = await scraper.search_products('iPhone 15')
        
        # Analyser les résultats
        print(f"\n=== RÉSULTATS ===")
        print(f"Total produits extraits: {len(products)}")
        
        # Vérifier le succès
        success = len(products) > 0
        print(f"Test réussi: {'✅ OUI' if success else '❌ NON'}")
        
        # Afficher les produits trouvés
        if products:
            print("\n=== PRODUITS TROUVÉS ===")
            for i, product in enumerate(products[:5]):
                print(f"{i+1}. {product.title[:60]}...")
                print(f"   Prix: {product.price} {product.currency}")
                print(f"   URL: {product.url[:80]}...")
                print()
        
        # Sauvegarder les résultats
        output_file = 'test_ebay_simple_output.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_products': len(products),
                'success': success,
                'products': [product.to_dict() for product in products]
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Résultats sauvegardés dans: {output_file}")
    
    return success

if __name__ == '__main__':
    success = asyncio.run(test_ebay_simple())
    print(f"\nTest {'RÉUSSI' if success else 'ÉCHOUÉ'}")
    exit(0 if success else 1)