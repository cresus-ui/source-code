# Test Local du Scraper E-commerce

Ce guide vous explique comment tester l'application de scraping e-commerce en local, sans avoir besoin d'Apify.

## 🚀 Démarrage Rapide

### 1. Configuration automatique

```bash
# Installer les dépendances et configurer l'environnement
python setup_local.py
```

### 2. Lancer le test

```bash
# Exécuter le test avec la configuration par défaut
python test_local.py
```

### 3. Vérifier les résultats

Les résultats seront sauvegardés dans `test_output.json`

## 📋 Configuration Manuelle

Si vous préférez configurer manuellement :

### Prérequis

- Python 3.8+
- pip

### Installation des dépendances

```bash
pip install -r requirements.txt
```

## ⚙️ Personnalisation du Test

Pour modifier les paramètres de test, éditez le fichier `test_local.py` :

```python
# Dans la méthode get_input() de MockActor
return {
    "search_terms": ["iPhone 15", "Samsung Galaxy"],  # Termes de recherche
    "platforms": ["amazon", "ebay"],                   # Plateformes à scraper
    "max_products_per_platform": 10,                   # Nombre max de produits
    "include_reviews": True,                            # Inclure les avis
    "include_images": True,                             # Inclure les images
    # ... autres paramètres
}
```

### Plateformes disponibles

- `"amazon"` - Amazon
- `"ebay"` - eBay
- `"walmart"` - Walmart
- `"etsy"` - Etsy
- `"shopify"` - Shopify

## 🔍 Debugging

### Logs détaillés

Les logs s'affichent dans la console avec les niveaux :
- `[INFO]` - Informations générales
- `[WARNING]` - Avertissements
- `[ERROR]` - Erreurs
- `[DATA]` - Données sauvegardées
- `[STATUS]` - Statut de l'opération

### Fichiers de sortie

- `test_output.json` - Résultats du scraping au format JSON
- Console - Logs en temps réel

### Problèmes courants

#### Erreur d'import
```
ModuleNotFoundError: No module named 'scrapers'
```
**Solution :** Exécutez `python setup_local.py` pour configurer l'environnement

#### Erreur de dépendances
```
ModuleNotFoundError: No module named 'beautifulsoup4'
```
**Solution :** Installez les dépendances avec `pip install -r requirements.txt`

#### Timeout ou erreurs réseau
```
[ERROR] Échec de récupération après 3 tentatives
```
**Solution :** 
- Vérifiez votre connexion internet
- Augmentez le `timeout` dans la configuration
- Réduisez le nombre de produits à scraper

## 🛠️ Développement

### Structure du test

```
test_local.py
├── MockActor          # Simule l'environnement Apify
│   ├── Log           # Mock des logs Apify
│   ├── get_input()   # Configuration de test
│   ├── push_data()   # Sauvegarde des résultats
│   └── set_status_message() # Statut
└── test_local()      # Fonction principale de test
```

### Ajout de nouveaux tests

Pour créer des tests spécifiques :

```python
# Créer un nouveau fichier test_custom.py
import asyncio
from test_local import MockActor
import sys
from pathlib import Path

sys.path.insert(0, str(Path("src")))
sys.modules['apify'] = type('MockApify', (), {'Actor': MockActor})()

async def test_amazon_only():
    """Test spécifique pour Amazon uniquement."""
    # Votre configuration personnalisée
    pass

if __name__ == "__main__":
    asyncio.run(test_amazon_only())
```

## 📊 Analyse des Résultats

Le fichier `test_output.json` contient :

```json
[
  {
    "platform": "amazon",
    "search_term": "iPhone 15",
    "title": "Apple iPhone 15 Pro",
    "price": "1199.00",
    "currency": "EUR",
    "url": "https://amazon.fr/...",
    "image_url": "https://...",
    "rating": 4.5,
    "reviews_count": 1250,
    "availability": "in_stock",
    "scraped_at": "2024-01-15T10:30:00Z"
  }
]
```

## 🚨 Limitations du Test Local

- **Pas de proxy** : Le test local n'utilise pas de proxies
- **Rate limiting** : Respectez les limites des sites web
- **Anti-détection** : Certaines protections peuvent bloquer les requêtes
- **Données limitées** : Test avec un nombre réduit de produits

## 💡 Conseils

1. **Commencez petit** : Testez avec 1-2 produits d'abord
2. **Surveillez les logs** : Vérifiez les erreurs dans la console
3. **Respectez les sites** : Ajoutez des délais entre les requêtes
4. **Testez par plateforme** : Testez une plateforme à la fois

## 🆘 Support

En cas de problème :

1. Vérifiez les logs dans la console
2. Consultez le fichier `test_output.json`
3. Réduisez la configuration de test
4. Vérifiez votre connexion internet

---

**Note :** Ce test local simule l'environnement Apify. Pour un déploiement en production, utilisez la plateforme Apify officielle.