#!/usr/bin/env python3
"""Test du scraper avec toutes les plateformes sauf Amazon pour extraire 50+ produits."""

import asyncio
import json
from src.main import EcommerceScraper

async def test_multi_platforms():
    """Test le scraper avec toutes les plateformes sauf Amazon pour obtenir 50+ produits."""
    
    # Configuration avec toutes les plateformes sauf Amazon
    config = {
        'platforms': ['ebay', 'walmart', 'etsy', 'shopify'],
        'searchTerms': ['iPhone 15'],
        'maxResults': 50,
        'trackPrices': True,
        'trackStock': True,
        'trackTrends': False,
        'shopifyDomains': ['shopify.com']
    }
    
    print("=== Test du scraper multi-plateformes (sans Amazon) ===")
    print(f"Plateformes: {config['platforms']}")
    print(f"Terme de recherche: {config['searchTerms'][0]}")
    print(f"Objectif: {config['maxResults']} produits minimum")
    print("\n" + "="*60 + "\n")
    
    # Initialiser le scraper
    scraper = EcommerceScraper(config)
    await scraper.initialize_scrapers()
    
    # Lancer le scraping
    products = await scraper.scrape_all_platforms()
    
    # Analyser les résultats
    print(f"\n=== RÉSULTATS ===")
    print(f"Total produits extraits: {len(products)}")
    
    # Compter par plateforme
    platform_counts = {}
    for product in products:
        platform = product.get('platform', 'unknown')
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    print("\nRépartition par plateforme:")
    for platform, count in platform_counts.items():
        print(f"  {platform}: {count} produits")
    
    # Vérifier l'objectif
    success = len(products) >= config['maxResults']
    print(f"\nObjectif atteint: {'✅ OUI' if success else '❌ NON'}")
    
    if not success:
        print(f"Manque {config['maxResults'] - len(products)} produits")
    else:
        print(f"Surplus: {len(products) - config['maxResults']} produits")
    
    # Sauvegarder les résultats
    output_file = 'test_multi_platforms_output.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'config': config,
            'total_products': len(products),
            'platform_counts': platform_counts,
            'success': success,
            'products': products
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nRésultats sauvegardés dans: {output_file}")
    
    # Afficher quelques exemples de produits
    if products:
        print("\n=== EXEMPLES DE PRODUITS ===")
        for i, product in enumerate(products[:8]):
            print(f"{i+1}. {product.get('title', 'N/A')[:60]}...")
            print(f"   Plateforme: {product.get('platform', 'N/A')}")
            print(f"   Prix: {product.get('price', 'N/A')} {product.get('currency', '')}")
            print(f"   URL: {product.get('url', 'N/A')[:80]}...")
            print()
    
    return success

if __name__ == '__main__':
    success = asyncio.run(test_multi_platforms())
    print(f"\n{'='*60}")
    print(f"RÉSULTAT FINAL: {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
    print(f"{'='*60}")
    exit(0 if success else 1)