#!/usr/bin/env python3
"""Test rapide du scraper Amazon avec la nouvelle URL."""

import asyncio
import json
from src.scrapers.amazon_scraper import AmazonScraper

async def test_amazon_url():
    """Test rapide du scraper Amazon avec la nouvelle URL."""
    
    print("=== Test rapide Amazon avec nouvelle URL ===")
    print("Terme de recherche: iPhone15")
    print("Objectif: Vérifier que l'URL fonctionne et extrait des produits")
    print("\n" + "="*50 + "\n")
    
    # Initialiser le scraper Amazon avec context manager
    async with AmazonScraper(max_results=10) as scraper:
        # Lancer le scraping
        products = await scraper.search_products('iPhone15')
        
        # Analyser les résultats
        print(f"\n=== RÉSULTATS ===")
        print(f"Total produits extraits: {len(products)}")
        
        # Vérifier le succès
        success = len(products) > 0
        print(f"Test réussi: {'✅ OUI' if success else '❌ NON'}")
        
        # Afficher les produits trouvés
        if products:
            print("\n=== PRODUITS TROUVÉS ===")
            for i, product in enumerate(products):
                print(f"{i+1}. {product.title[:60]}...")
                print(f"   Prix: {product.price}")
                print(f"   URL: {product.url[:80]}...")
                print()
        
        # Sauvegarder les résultats
        output_file = 'test_amazon_url_output.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_products': len(products),
                'success': success,
                'products': [product.to_dict() for product in products]
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Résultats sauvegardés dans: {output_file}")
    
    return success

if __name__ == '__main__':
    success = asyncio.run(test_amazon_url())
    print(f"\nTest {'RÉUSSI' if success else 'ÉCHOUÉ'}")
    exit(0 if success else 1)