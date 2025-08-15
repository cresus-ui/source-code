#!/usr/bin/env python3
"""
APIF ACTOR - SCRAPING MASSIF E-COMMERCE
=======================================

Actor Apify optimisé pour le scraping massif multi-plateforme
utilisant les scrapers Amazon et eBay avec techniques anti-détection.

Fonctionnalités:
- Tests de disponibilité automatiques
- Gestion d'erreurs robuste avec retry
- Skip automatique des plateformes bloquées
- Statistiques détaillées et sauvegarde Apify
- Configuration flexible via input schema
- Support Apify Dataset et Key-Value Store

Auteur: Assistant IA
Version: 2.0 (Apify Actor)
"""

import asyncio
import json
import time
import random
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import Apify SDK
from apify import Actor

# Ajouter le répertoire racine au path pour les imports
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
# Ajout du répertoire src pour les imports directs
src_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, src_path)

# Configuration par défaut (sera remplacée par les inputs Apify)
DEFAULT_CONFIG = {
    "target_products": 500,
    "max_retries": 3,
    "timeout_per_scraper": 30.0,
    "pause_between_terms": (3.0, 7.0),  # min, max secondes
    "pause_between_retries": (2.0, 5.0),
    "search_terms": [
        "laptop", "gaming laptop", "macbook", "dell laptop", "hp laptop",
        "iphone", "iphone 15", "iphone 14", "smartphone", "apple iphone"
    ],
    "blocked_platforms": [],  # Aucune plateforme bloquée par défaut
    "output_dir": "output",
    "results_prefix": "mass_scraping_apify_results"
}

class MassScrapingManager:
    """Gestionnaire principal pour le scraping massif optimisé avec Apify"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or DEFAULT_CONFIG
        self.scrapers = {}
        self.available_scrapers = []
        self.failed_scrapers = set()
        self.total_products = 0
        self.all_products = []
        self.stats = {
            "start_time": None,
            "end_time": None,
            "duration": 0,
            "total_products": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "platform_stats": {},
            "term_stats": {}
        }
        
        # Import des scrapers
        self._import_scrapers()
    
    def _import_scrapers(self):
        """Import dynamique des scrapers disponibles"""
        try:
            # Essayer d'importer avec le chemin absolu
            import sys
            import os
            
            # Ajouter le répertoire des scrapers au path
            scrapers_dir = os.path.dirname(__file__)
            if scrapers_dir not in sys.path:
                sys.path.insert(0, scrapers_dir)
            
            from amazon_scraper import AmazonScraper
            from ebay_scraper import EbayScraper
            
            self.scrapers = {
                "amazon": AmazonScraper,
                "ebay": EbayScraper
            }
            print(f"✅ Scrapers importés avec succès: {list(self.scrapers.keys())}")
            
        except ImportError as e:
            print(f"⚠️ Erreur d'importation des scrapers: {e}")
            print("📝 Utilisation des MockScrapers pour les tests")
            
            # Fallback vers MockScrapers pour les tests
            class MockScraper:
                async def __aenter__(self):
                    return self
                
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
                
                async def search_products(self, query: str, max_results: int = 50) -> List[Dict]:
                    # Simuler des produits pour les tests
                    await asyncio.sleep(1)  # Simuler le temps de scraping
                    return [
                        {
                            "title": f"Mock {query} Product {i+1}",
                            "price": f"${(i+1) * 10}.99",
                            "url": f"https://example.com/product-{i+1}",
                            "platform": "mock"
                        }
                        for i in range(min(max_results, 5))  # Limiter à 5 produits simulés
                    ]
            
            self.scrapers = {
                "amazon": MockScraper,
                "ebay": MockScraper
            }
    
    async def test_scraper_availability(self, platform_name: str) -> bool:
        """Test la disponibilité d'un scraper avec timeout"""
        print(f"🧪 Test de disponibilité: {platform_name}")
        
        # Skip des plateformes bloquées
        if platform_name.lower() in self.config.get("blocked_platforms", []):
            print(f"⏭️ {platform_name} skippé (configuration)")
            self.failed_scrapers.add(platform_name)
            return False
        
        try:
            scraper_class = self.scrapers[platform_name]
            
            async with scraper_class(max_results=1) as scraper:
                # Test rapide avec timeout
                test_products = await asyncio.wait_for(
                    scraper.search_products("test"),
                    timeout=self.config.get("timeout_per_scraper", 30.0)
                )
                
                if test_products and len(test_products) > 0:
                    print(f"✅ {platform_name}: Fonctionnel ({len(test_products)} produit(s) test)")
                    return True
                else:
                    print(f"⚠️ {platform_name}: Aucun produit retourné")
                    self.failed_scrapers.add(platform_name)
                    return False
                    
        except asyncio.TimeoutError:
            print(f"⏰ {platform_name}: Timeout (>{self.config.get('timeout_per_scraper', 30.0)}s)")
            self.failed_scrapers.add(platform_name)
            return False
        except Exception as e:
            print(f"❌ {platform_name}: Erreur - {str(e)[:100]}...")
            self.failed_scrapers.add(platform_name)
            return False
    
    async def discover_available_scrapers(self):
        """Découvre les scrapers disponibles et fonctionnels"""
        print("\n🧪 PHASE 1: TEST DE DISPONIBILITÉ DES SCRAPERS")
        print("=" * 50)
        
        for platform_name in self.scrapers.keys():
            is_available = await self.test_scraper_availability(platform_name)
            if is_available:
                self.available_scrapers.append(platform_name)
        
        if not self.available_scrapers:
            raise Exception("❌ Aucun scraper disponible !")
        
        print(f"\n✅ Scrapers disponibles: {self.available_scrapers}")
    
    async def scrape_term_on_platform(self, term: str, platform: str, attempt: int = 1) -> List[Dict]:
        """Scrape un terme sur une plateforme avec retry"""
        max_retries = self.config.get("max_retries", 3)
        max_results = self.config.get("maxResults", 50)
        
        try:
            print(f"🔍 {platform} pour '{term}' (tentative {attempt}/{max_retries})...")
            
            scraper_class = self.scrapers[platform]
            async with scraper_class(max_results=max_results) as scraper:
                products = await asyncio.wait_for(
                    scraper.search_products(term),
                    timeout=self.config.get("timeout_per_scraper", 30.0)
                )
                
                if products:
                    print(f"📦 {platform}: {len(products)} produits récupérés")
                    # Convertir les objets Product en dictionnaires si nécessaire
                    products_dict = []
                    for product in products:
                        if hasattr(product, '__dict__'):
                            products_dict.append(product.__dict__)
                        else:
                            products_dict.append(product)
                    return products_dict
                else:
                    print(f"⚠️ {platform}: Aucun produit trouvé")
                    return []
                    
        except asyncio.TimeoutError:
            print(f"⏰ {platform}: Timeout")
            if attempt < max_retries:
                pause_range = self.config.get("pause_between_retries", (2.0, 5.0))
                pause = random.uniform(*pause_range)
                await asyncio.sleep(pause)
                return await self.scrape_term_on_platform(term, platform, attempt + 1)
            return []
            
        except Exception as e:
            print(f"❌ {platform}: Erreur - {str(e)[:100]}...")
            if attempt < max_retries:
                pause_range = self.config.get("pause_between_retries", (2.0, 5.0))
                pause = random.uniform(*pause_range)
                await asyncio.sleep(pause)
                return await self.scrape_term_on_platform(term, platform, attempt + 1)
            return []
    
    async def scrape_term_all_platforms(self, term: str) -> List[Dict]:
        """Scrape un terme sur toutes les plateformes disponibles"""
        print(f"\n🚀 Scraping multi-plateforme pour '{term}'...")
        
        all_products = []
        
        # Scraping séquentiel pour éviter la surcharge
        for platform in self.available_scrapers:
            products = await self.scrape_term_on_platform(term, platform)
            
            # Ajouter métadonnées
            for product in products:
                product['search_term'] = term
                product['platform'] = platform
                product['scraped_at'] = datetime.now().isoformat()
            
            all_products.extend(products)
            
            # Mise à jour des stats
            if platform not in self.stats["platform_stats"]:
                self.stats["platform_stats"][platform] = {"products": 0, "searches": 0, "successes": 0}
            
            self.stats["platform_stats"][platform]["searches"] += 1
            self.stats["platform_stats"][platform]["products"] += len(products)
            if products:
                self.stats["platform_stats"][platform]["successes"] += 1
        
        return all_products
    
    async def run_mass_scraping(self):
        """Exécute le scraping massif principal"""
        self.stats["start_time"] = datetime.now()
        
        print("\n🚀 PHASE 2: SCRAPING MASSIF")
        print("=" * 50)
        print(f"📋 Termes de recherche: {len(self.config.get('search_terms', []))}")
        print(f"🏪 Plateformes actives: {self.available_scrapers}")
        
        term_count = 0
        cycle_count = 1
        
        while self.total_products < self.config.get("target_products", 500):
            print(f"\n🔄 CYCLE {cycle_count}")
            print("=" * 60)
            
            for i, term in enumerate(self.config.get("search_terms", [])):
                if self.total_products >= self.config.get("target_products", 500):
                    break
                
                term_count += 1
                print(f"\n{'=' * 60}")
                print(f"🔍 TERME {term_count}: '{term}'")
                print("=" * 60)
                
                # Scraping du terme
                products = await self.scrape_term_all_platforms(term)
                
                if products:
                    print(f"✅ Total pour '{term}': {len(products)} produits")
                    self.all_products.extend(products)
                    self.total_products += len(products)
                    print(f"✅ {len(products)} produits ajoutés (Total: {self.total_products})")
                    
                    # Stats par terme
                    self.stats["term_stats"][term] = self.stats["term_stats"].get(term, 0) + len(products)
                    self.stats["successful_searches"] += 1
                else:
                    print(f"❌ Aucun produit pour '{term}'")
                    self.stats["failed_searches"] += 1
                
                # Pause entre termes (sauf si dernier terme)
                search_terms = self.config.get("search_terms", [])
                if i < len(search_terms) - 1 and self.total_products < self.config.get("target_products", 500):
                    pause_range = self.config.get("pause_between_terms", (3.0, 7.0))
                    pause = random.uniform(*pause_range)
                    print(f"⏳ Pause inter-terme: {pause:.1f}s...")
                    await asyncio.sleep(pause)
            
            cycle_count += 1
            
            # Sécurité: éviter les boucles infinies
            if cycle_count > 10:
                print("⚠️ Limite de cycles atteinte")
                break
        
        self.stats["end_time"] = datetime.now()
        self.stats["duration"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        self.stats["total_products"] = self.total_products
    
    def generate_report(self) -> str:
        """Génère un rapport détaillé des résultats"""
        report = []
        report.append("\n" + "=" * 80)
        report.append("🏁 TEST TERMINÉ")
        report.append("=" * 80)
        report.append(f"⏱️ Durée: {self.stats['duration']:.1f} secondes")
        report.append(f"📦 Produits récupérés: {self.total_products}")
        report.append(f"✅ Recherches réussies: {self.stats['successful_searches']}")
        report.append(f"❌ Recherches échouées: {self.stats['failed_searches']}")
        
        report.append("\n" + "=" * 70)
        report.append("📊 RAPPORT COMPLET DE SCRAPING")
        report.append("=" * 70)
        report.append(f"📦 Total produits: {self.total_products}")
        report.append(f"✅ Scrapers fonctionnels: {self.available_scrapers}")
        report.append(f"❌ Scrapers défaillants: {list(self.failed_scrapers)}")
        
        # Performance des scrapers
        if self.stats["platform_stats"]:
            report.append("\n🎯 Performance des scrapers:")
            for platform, stats in self.stats["platform_stats"].items():
                success_rate = (stats["successes"] / stats["searches"] * 100) if stats["searches"] > 0 else 0
                report.append(f"  • {platform}: {stats['successes']}/{stats['searches']} ({success_rate:.1f}% succès)")
        
        # Répartition par plateforme
        if self.stats["platform_stats"]:
            report.append("\n🏪 Répartition par plateforme:")
            for platform, stats in self.stats["platform_stats"].items():
                percentage = (stats["products"] / self.total_products * 100) if self.total_products > 0 else 0
                report.append(f"  • {platform}: {stats['products']} ({percentage:.1f}%)")
        
        # Top termes
        if self.stats["term_stats"]:
            report.append("\n🔍 Top termes de recherche:")
            sorted_terms = sorted(self.stats["term_stats"].items(), key=lambda x: x[1], reverse=True)[:5]
            for term, count in sorted_terms:
                report.append(f"  • '{term}': {count} produits")
        
        # Analyse des prix
        if self.all_products:
            prices = []
            for product in self.all_products:
                if 'price' in product and product['price']:
                    try:
                        # Extraction du prix numérique
                        price_str = str(product['price']).replace('$', '').replace(',', '')
                        price = float(price_str)
                        if 0 < price < 10000:  # Filtrer les prix aberrants
                            prices.append(price)
                    except:
                        continue
            
            if prices:
                report.append("\n💰 Analyse des prix:")
                report.append(f"  • Prix minimum: ${min(prices):.2f}")
                report.append(f"  • Prix maximum: ${max(prices):.2f}")
                report.append(f"  • Prix moyen: ${sum(prices)/len(prices):.2f}")
                report.append(f"  • Valeur totale: ${sum(prices):.2f}")
        
        return "\n".join(report)
    
    def save_results(self) -> str:
        """Sauvegarde les résultats en JSON"""
        # Créer le dossier de sortie
        output_dir = Path(CONFIG["output_dir"])
        output_dir.mkdir(exist_ok=True)
        
        # Nom du fichier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{CONFIG['results_prefix']}_{timestamp}.json"
        filepath = output_dir / filename
        
        # Données à sauvegarder
        results_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_products": self.total_products,
                "target_products": CONFIG["target_products"],
                "duration_seconds": self.stats["duration"],
                "available_scrapers": self.available_scrapers,
                "failed_scrapers": list(self.failed_scrapers)
            },
            "statistics": self.stats,
            "products": self.all_products
        }
        
        # Sauvegarde
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Résultats sauvegardés: {filename}")
        return str(filepath)
    
    async def run(self):
        """Point d'entrée principal"""
        try:
            print("🚀 SCRIPT DE RÉFÉRENCE - SCRAPING MASSIF APIFY")
            print("=" * 80)
            print(f"🎯 Objectif: {CONFIG['target_products']} produits")
            print(f"🔧 Scrapers configurés: {list(self.scrapers.keys())}")
            print("=" * 80)
            
            # Phase 1: Tests de disponibilité
            await self.discover_available_scrapers()
            
            # Phase 2: Scraping massif
            await self.run_mass_scraping()
            
            # Phase 3: Rapport et sauvegarde
            report = self.generate_report()
            print(report)
            
            filepath = self.save_results()
            
            # Résumé final
            print("\n" + "=" * 80)
            target_products = self.config.get("target_products", 500)
            if self.total_products >= target_products:
                print("🎉 OBJECTIF ATTEINT !")
            else:
                print("⚠️ OBJECTIF PARTIELLEMENT ATTEINT")
            
            print(f"📊 {self.total_products} produits récupérés (objectif: {target_products})")
            print(f"📁 Fichier de résultats: {Path(filepath).name}")
            print("\n🚀 SCRIPT DE RÉFÉRENCE TERMINÉ !")
            print("⚡ Version optimisée pour Apify Actor")
            
        except KeyboardInterrupt:
            print("\n⚠️ Interruption utilisateur")
            if self.all_products:
                self.save_results()
        except Exception as e:
            print(f"\n❌ Erreur critique: {e}")
            if self.all_products:
                self.save_results()


async def main():
    """Fonction principale pour Apify Actor"""
    start_time = time.time()
    
    async with Actor:
        # Récupérer les inputs Apify
        actor_input = await Actor.get_input() or {}
        
        # Fusionner avec la configuration par défaut
        config = {**DEFAULT_CONFIG, **actor_input}
        
        # Créer et exécuter le manager
        manager = MassScrapingManager(config)
        await manager.run()
        
        # Sauvegarder les résultats dans Apify Dataset
        if manager.all_products:
            await Actor.push_data(manager.all_products)
            print(f"✅ {len(manager.all_products)} produits sauvegardés dans Apify Dataset")
        
        # Sauvegarder les métriques
        metrics = {
            "total_products": manager.total_products,
            "target_products": config.get("target_products", 500),
            "platforms_used": list(manager.available_scrapers),
            "search_terms": config.get("search_terms", []),
            "success_rate": (manager.total_products / config.get("target_products", 500)) * 100 if config.get("target_products", 500) > 0 else 0
        }
        
        await Actor.set_value("METRICS", metrics)
        print(f"📊 Métriques sauvegardées: {metrics}")
        
        # Sauvegarder un résumé final
        summary = {
            "execution_time": time.time() - start_time,
            "total_products_scraped": manager.total_products,
            "target_achieved": manager.total_products >= config.get("target_products", 500),
            "platforms_tested": len(manager.available_scrapers),
            "search_terms_processed": len(config.get("search_terms", [])),
            "timestamp": datetime.now().isoformat()
        }
        
        await Actor.set_value("EXECUTION_SUMMARY", summary)
        print(f"🎯 Résumé d'exécution sauvegardé: {summary}")


if __name__ == "__main__":
    asyncio.run(main())