# Guide du Système de Retry Intelligent

## 🎯 Vue d'ensemble

Le scraper e-commerce dispose maintenant d'un **système de retry intelligent** qui garantit l'obtention du nombre de produits souhaité avec une répartition équitable entre les plateformes.

## 🔧 Fonctionnalités

### Objectifs Automatiques
- **Nombre total**: Atteindre le `maxResults` spécifié (par défaut: 50 produits)
- **Minimum par plateforme**: Au moins 5 produits par plateforme activée
- **Limite de tentatives**: Maximum 20 tentatives pour éviter les boucles infinies

### Logique Intelligente
1. **Analyse continue**: Vérifie à chaque tentative si les objectifs sont atteints
2. **Scraping ciblé**: Ne scrape que les plateformes qui ont besoin de plus de produits
3. **Évitement des doublons**: Détecte et évite les produits déjà trouvés
4. **Arrêt automatique**: S'arrête dès que tous les objectifs sont atteints

## 📊 Configuration

### Input JSON
```json
{
  "platforms": ["amazon", "ebay", "walmart"],
  "searchTerms": ["iPhone", "smartphone"],
  "maxResults": 50,
  "trackPrices": true,
  "trackStock": true,
  "trackTrends": false
}
```

### Comportement Attendu
- **Total**: 50 produits minimum
- **Par plateforme**: 5 produits minimum sur chaque plateforme
- **Tentatives**: Jusqu'à 20 tentatives si nécessaire

## 🔄 Algorithme de Retry

### Étapes du Processus

1. **Initialisation**
   ```
   Tentative = 1
   Objectif total = maxResults (50)
   Minimum par plateforme = 5
   Maximum tentatives = 20
   ```

2. **Boucle de Retry**
   ```
   POUR chaque tentative (1 à 20):
     - Vérifier les objectifs actuels
     - Identifier les plateformes à scraper
     - Lancer le scraping ciblé
     - Éviter les doublons
     - Vérifier si objectifs atteints
     - SI oui: ARRÊTER
     - SINON: Continuer
   ```

3. **Conditions d'Arrêt**
   - ✅ Total ≥ 50 produits ET minimum 5 par plateforme
   - ⏰ 20 tentatives atteintes

## 📈 Exemples de Résultats

### Cas de Succès
```
🎯 Objectif: 50 produits au total, minimum 5 par plateforme
📊 Résultats après 11 tentatives:
  - Amazon: 30 produits ✅
  - eBay: 20 produits ✅
  - Total: 50 produits ✅
⏱️ Durée: 30.3 secondes
```

### Cas Partiel
```
🎯 Objectif: 50 produits au total, minimum 5 par plateforme
📊 Résultats après 20 tentatives:
  - Amazon: 25 produits ✅
  - eBay: 15 produits ✅
  - Walmart: 2 produits ❌ (anti-bot)
  - Total: 42 produits ❌
⏱️ Durée: 120 secondes
```

## 🛡️ Gestion des Erreurs

### Anti-Bot et Blocages
- **Rotation automatique**: Headers et User-Agents
- **Délais aléatoires**: Entre 1-5 secondes
- **Retry par plateforme**: 20 tentatives par plateforme
- **Gestion des 403/429**: Attente progressive

### Plateformes Indisponibles
- **Isolation des erreurs**: Une plateforme en erreur n'affecte pas les autres
- **Logs détaillés**: Traçabilité complète des erreurs
- **Fallback**: Continue avec les plateformes fonctionnelles

## 📝 Logs et Monitoring

### Logs de Progression
```
[INFO] Objectif: 50 produits au total, minimum 5 par plateforme
[INFO] Tentative 1/20
[INFO] Scraping des plateformes: amazon, ebay, walmart
[INFO] amazon: +8 nouveaux produits (total: 8)
[INFO] ebay: +5 nouveaux produits (total: 5)
[INFO] walmart: +0 nouveaux produits (total: 0)
```

### Résumé Final
```
[INFO] Scraping terminé après 11 tentatives: 50 produits trouvés
[INFO] amazon: 30 produits ✓
[INFO] ebay: 20 produits ✓
[INFO] walmart: 0 produits ✗
```

## 🧪 Tests

### Test Local Simple
```bash
python test_local.py
```

### Test de la Logique de Retry
```bash
python test_retry_logic.py
```

### Validation des Résultats
- **Fichier de sortie**: `test_retry_output.json`
- **Métriques**: Nombre de produits, durée, appels par plateforme
- **Validation**: Objectifs atteints ou non

## ⚙️ Personnalisation

### Modifier les Seuils
```python
# Dans src/main.py, ligne ~118
min_per_platform = 5  # Changer ici
max_attempts = 20     # Changer ici
```

### Ajouter des Plateformes
```python
# Dans src/main.py, méthode initialize_scrapers
if 'nouvelle_plateforme' in self.platforms:
    self.scrapers['nouvelle_plateforme'] = NouveauScraper(max_results=max_per_platform)
```

## 🚀 Déploiement sur Apify

Le système de retry intelligent fonctionne automatiquement sur Apify:

1. **Configuration**: Via `input_schema.json`
2. **Exécution**: Automatique avec logs détaillés
3. **Résultats**: Sauvegardés dans le dataset Apify
4. **Monitoring**: Logs visibles dans l'interface Apify

## 📋 Checklist de Validation

- [ ] Configuration correcte dans `input_schema.json`
- [ ] Test local réussi avec `test_local.py`
- [ ] Test de retry réussi avec `test_retry_logic.py`
- [ ] Logs détaillés et compréhensibles
- [ ] Gestion des erreurs robuste
- [ ] Performance acceptable (< 2 minutes pour 50 produits)
- [ ] Évitement des doublons fonctionnel
- [ ] Arrêt automatique quand objectifs atteints

## 🔍 Dépannage

### Problèmes Courants

1. **Pas assez de produits trouvés**
   - Vérifier les termes de recherche
   - Tester manuellement les plateformes
   - Vérifier les logs d'erreurs

2. **Trop de tentatives**
   - Plateformes avec anti-bot agressif
   - Termes de recherche trop spécifiques
   - Problèmes de réseau

3. **Doublons détectés**
   - Normal, le système les évite automatiquement
   - Vérifier les URLs uniques dans les résultats

### Support

Pour toute question ou problème:
1. Vérifier les logs détaillés
2. Tester avec `test_retry_logic.py`
3. Consulter la documentation des scrapers individuels

---

**Note**: Ce système garantit une extraction robuste et équilibrée sur toutes les plateformes e-commerce supportées.