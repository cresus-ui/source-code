#!/usr/bin/env python3
"""Test du scraper Amazon pour extraire 50 produits."""

import asyncio
import json
from src.main import EcommerceScraper

async def test_amazon_50():
    """Test le scraper Amazon pour obtenir 50 produits."""
    
    # Configuration avec Amazon uniquement
    config = {
        'platforms': ['amazon'],
        'searchTerms': ['iPhone 15'],
        'maxResults': 50,
        'trackPrices': True,
        'trackStock': True,
        'trackTrends': False
    }
    
    print("=== Test du scraper Amazon pour 50 produits ===")
    print(f"Terme de recherche: {config['searchTerms'][0]}")
    print(f"Objectif: {config['maxResults']} produits")
    print("\n" + "="*50 + "\n")
    
    # Initialiser le scraper
    scraper = EcommerceScraper(config)
    await scraper.initialize_scrapers()
    
    # Lancer le scraping
    products = await scraper.scrape_all_platforms()
    
    # Analyser les résultats
    print(f"\n=== RÉSULTATS ===")
    print(f"Total produits extraits: {len(products)}")
    
    # Vérifier l'objectif
    success = len(products) >= config['maxResults']
    print(f"Objectif atteint: {'✅ OUI' if success else '❌ NON'}")
    
    if not success:
        print(f"Manque {config['maxResults'] - len(products)} produits")
    
    # Sauvegarder les résultats
    output_file = 'test_amazon_50_output.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'config': config,
            'total_products': len(products),
            'success': success,
            'products': products
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Résultats sauvegardés dans: {output_file}")
    
    # Afficher quelques exemples de produits
    if products:
        print("\n=== EXEMPLES DE PRODUITS ===")
        for i, product in enumerate(products[:10]):
            print(f"{i+1}. {product.get('title', 'N/A')[:60]}...")
            print(f"   Prix: {product.get('price', 'N/A')}")
            print()
    
    return success

if __name__ == '__main__':
    success = asyncio.run(test_amazon_50())
    exit(0 if success else 1)