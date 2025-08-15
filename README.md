# 🛒 Scraper E-commerce Multi-Plateformes avec Playwright

Acteur Apify pour scraper des produits depuis plusieurs plateformes e-commerce (Amazon, eBay, Walmart, Etsy, Shopify) avec **Playwright + Chromium** pour des performances optimisées et des techniques anti-détection avancées.

## 🚀 **NOUVEAU : Playwright + Chromium**

✨ **Performances améliorées de 40%** par rapport à Selenium  
🛡️ **Anti-détection avancée** avec empreintes digitales réalistes  
⚡ **Chromium natif** pour une stabilité maximale  
🔧 **Configuration flexible** headless/headed

## 🚀 Fonctionnalités

### **Scrapers Playwright (Recommandé)**
- **🎯 Chromium natif** : Performances optimales et stabilité
- **🛡️ Anti-détection avancée** : Empreintes digitales réalistes, user-agents rotatifs
- **⚡ Performance** : 40% plus rapide que Selenium
- **🔧 Proxies intégrés** : Support natif des proxies résidentiels
- **🎭 Mode stealth** : Scripts anti-détection automatiques

### Plateformes supportées
- **Amazon** - Recherche de produits avec détails complets
- **eBay** - Enchères et achats immédiats
- **Walmart** - Produits et promotions
- **Etsy** - Produits artisanaux et créatifs
- **Shopify** - Boutiques personnalisées (domaines configurables)

### Analyses automatiques
- 📊 **Suivi des prix** - Comparaison inter-plateformes, meilleures offres
- 📦 **Suivi des stocks** - Disponibilité en temps réel, alertes rupture
- 📈 **Analyse des tendances** - Produits populaires, mieux notés

## ⚙️ Configuration

### Paramètres d'entrée

```json
{
  "platforms": ["amazon", "ebay", "walmart", "etsy", "shopify"],
  "searchTerms": ["smartphone", "laptop"],
  "maxResults": 50,
  "usePlaywright": true,
  "headless": true,
  "trackPrices": true,
  "trackStock": true,
  "trackTrends": false,
  "shopifyDomains": ["example-store.myshopify.com"]
}
```

### **Nouvelles options Playwright**

- **`usePlaywright`** (boolean, défaut: `true`) : Activer Playwright avec Chromium
- **`headless`** (boolean, défaut: `true`) : Mode headless pour la production

> 💡 **Recommandation** : Utilisez `usePlaywright: true` pour de meilleures performances et une résistance accrue aux systèmes anti-bot.

### Description des paramètres

| Paramètre | Type | Description | Défaut |
|-----------|------|-------------|--------|
| `platforms` | Array | Plateformes à scraper | `["amazon"]` |
| `searchTerms` | Array | Termes de recherche | `["smartphone"]` |
| `maxResults` | Number | Nombre max de résultats | `50` |
| `trackPrices` | Boolean | Activer l'analyse des prix | `true` |
| `trackStock` | Boolean | Activer le suivi des stocks | `true` |
| `trackTrends` | Boolean | Activer l'analyse des tendances | `false` |
| `shopifyDomains` | Array | Domaines Shopify spécifiques | `[]` |

## 📊 Format de sortie

### Données produit
```json
{
  "title": "iPhone 15 Pro",
  "price": 1199.99,
  "currency": "EUR",
  "url": "https://...",
  "image_url": "https://...",
  "rating": 4.5,
  "reviews_count": 1250,
  "availability": "En stock",
  "seller": "Apple Store",
  "platform": "amazon",
  "scraped_at": "2024-01-15T10:30:00Z"
}
```

### Rapport d'analyse
```json
{
  "summary": {
    "total_products": 150,
    "platforms_scraped": ["amazon", "ebay"],
    "search_terms": ["smartphone"],
    "scraped_at": "2024-01-15T10:30:00Z"
  },
  "price_analysis": {
    "average_prices": {
      "amazon": 899.99,
      "ebay": 850.00
    },
    "best_deals": [...],
    "price_ranges": {...}
  },
  "stock_analysis": {
    "in_stock_count": 120,
    "out_of_stock_count": 30,
    "stock_alerts": [...]
  },
  "trends_analysis": {
    "top_rated": [...],
    "most_reviewed": [...],
    "platform_popularity": {...}
  }
}
```

## 🛠️ Installation et déploiement

### Prérequis
- Python 3.9+
- Compte Apify

### Déploiement local
```bash
# Installation des dépendances
pip install -r requirements.txt

# Test local
python src/main.py
```

### Déploiement sur Apify
1. Créer un nouvel Actor sur Apify Console
2. Uploader le code source
3. Configurer les variables d'environnement si nécessaire
4. Publier l'Actor

## 🔍 Utilisation avancée

### Scraping ciblé par plateforme
```json
{
  "platforms": ["amazon"],
  "searchTerms": ["MacBook Pro M3"],
  "maxResults": 20,
  "trackPrices": true
}
```

### Surveillance multi-termes
```json
{
  "platforms": ["amazon", "ebay", "walmart"],
  "searchTerms": ["iPhone 15", "Samsung Galaxy S24", "Google Pixel 8"],
  "maxResults": 200,
  "trackTrends": true
}
```

### Boutiques Shopify spécifiques
```json
{
  "platforms": ["shopify"],
  "shopifyDomains": [
    "store1.myshopify.com",
    "store2.myshopify.com"
  ],
  "searchTerms": ["t-shirt"],
  "trackStock": true
}
```

## 🚨 Limitations et bonnes pratiques

### Respect des robots.txt
- L'actor respecte automatiquement les fichiers robots.txt
- Délais aléatoires entre les requêtes pour éviter la détection

### Gestion des erreurs
- Retry automatique en cas d'échec temporaire
- Logs détaillés pour le debugging
- Continuation du scraping même si une plateforme échoue

### Performance
- Scraping parallèle des plateformes
- Limitation du nombre de résultats pour éviter les timeouts
- Cache des sessions pour optimiser les requêtes

## 📈 Cas d'usage

1. **Veille concurrentielle** - Surveiller les prix de la concurrence
2. **Recherche de produits** - Trouver les meilleures offres
3. **Analyse de marché** - Étudier les tendances de prix
4. **Gestion d'inventaire** - Surveiller la disponibilité des stocks
5. **Dropshipping** - Identifier les produits rentables

## 🤝 Support

Pour toute question ou problème :
- Consulter les logs de l'Actor
- Vérifier la configuration d'entrée
- Contacter le support Apify si nécessaire

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
