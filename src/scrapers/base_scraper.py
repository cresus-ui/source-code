"""Classe de base pour tous les scrapers e-commerce."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import random
from fake_useragent import UserAgent
from httpx import AsyncClient
from bs4 import BeautifulSoup
from apify import Actor

from src.utils import safe_log

try:
    from src.config.anti_detection import AntiDetectionConfig
except ImportError:
    # Fallback si le module n'est pas trouvé
    class AntiDetectionConfig:
        @staticmethod
        def get_random_user_agent():
            return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
        @staticmethod
        def generate_realistic_headers(platform=None, base_url=None):
            return {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
        
        @staticmethod
        def get_platform_delay(platform):
            return 2.0, 8.0
        
        @staticmethod
        def get_block_indicators(platform):
            return ['captcha', 'blocked', 'access denied']


@dataclass
class Product:
    """Structure de données pour un produit."""
    title: str
    price: Optional[float]
    currency: str
    url: str
    availability: str
    platform: str
    image_url: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    seller: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    asin: Optional[str] = None  # Amazon Standard Identification Number
    scraped_at: Optional[str] = None  # Timestamp du scraping
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le produit en dictionnaire."""
        return {
            'title': self.title,
            'price': self.price,
            'currency': self.currency,
            'url': self.url,
            'image_url': self.image_url,
            'rating': self.rating,
            'reviews_count': self.reviews_count,
            'availability': self.availability,
            'seller': self.seller,
            'platform': self.platform,
            'scraped_at': self.scraped_at if isinstance(self.scraped_at, str) else (self.scraped_at.isoformat() if self.scraped_at else None),
            'description': self.description,
            'category': self.category,
            'brand': self.brand,
            'sku': self.sku
        }


class BaseScraper(ABC):
    """Classe de base abstraite pour tous les scrapers."""
    
    def __init__(self, max_results: int = 50):
        self.max_results = max_results
        self.ua = UserAgent()
        self.session = None
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    async def __aenter__(self):
        """Initialise la session HTTP avec des headers anti-détection."""
        self.session = AsyncClient(
            headers=self.get_random_headers(),
            timeout=30.0,
            follow_redirects=True
        )
        return self
    
    def get_random_headers(self, platform: str = None, base_url: str = None) -> Dict[str, str]:
        """Génère des headers HTTP aléatoires pour éviter la détection."""
        return AntiDetectionConfig.generate_realistic_headers(platform, base_url)
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ferme la session HTTP."""
        if self.session:
            await self.session.aclose()
    
    @abstractmethod
    async def search_products(self, search_term: str) -> List[Product]:
        """Recherche des produits sur la plateforme."""
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Retourne le nom de la plateforme."""
        pass
    
    async def random_delay(self, min_seconds: float = None, max_seconds: float = None, platform: str = None):
        """Ajoute un délai aléatoire pour éviter la détection."""
        # Utiliser les délais spécifiques à la plateforme si disponibles
        if platform and min_seconds is None and max_seconds is None:
            min_seconds, max_seconds = AntiDetectionConfig.get_platform_delay(platform)
        elif min_seconds is None or max_seconds is None:
            min_seconds, max_seconds = 2.0, 8.0
        
        # Délai de base avec variation gaussienne pour plus de réalisme
        base_delay = random.uniform(min_seconds, max_seconds)
        gaussian_variation = random.gauss(0, 0.5)
        delay = max(0.5, base_delay + gaussian_variation)
        
        await safe_log('info', f"Attente de {delay:.2f} secondes...")
        await asyncio.sleep(delay)
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """Extrait le prix numérique d'un texte."""
        if not price_text:
            return None
        
        import re
        # Supprime les caractères non numériques sauf les points et virgules
        price_clean = re.sub(r'[^\d.,]', '', price_text.replace(',', '.'))
        
        try:
            return float(price_clean)
        except (ValueError, TypeError):
            return None
    
    def extract_rating(self, rating_text: str) -> Optional[float]:
        """Extrait la note numérique d'un texte."""
        if not rating_text:
            return None
            
        import re
        rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
        if rating_match:
            try:
                return float(rating_match.group(1))
            except ValueError:
                return None
        return None
    
    def extract_reviews_count(self, reviews_text: str) -> Optional[int]:
        """Extrait le nombre d'avis d'un texte."""
        if not reviews_text:
            return None
            
        import re
        # Recherche des nombres avec des séparateurs de milliers
        reviews_match = re.search(r'([\d,]+)', reviews_text.replace(' ', '').replace('.', ','))
        if reviews_match:
            try:
                return int(reviews_match.group(1).replace(',', ''))
            except ValueError:
                return None
        return None
    
    async def get_page_content(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """Récupère le contenu d'une page web avec retry et anti-détection."""
        if not self.session:
            await safe_log('error', "Session non initialisée. Utilisez 'async with scraper:' pour initialiser.")
            return None
            
        for attempt in range(max_retries):
            try:
                # Rotation des headers à chaque tentative
                if attempt > 0:
                    self.session.headers.update(self.get_random_headers())
                    await self.random_delay(3.0, 10.0)  # Délai plus long entre les tentatives
                
                await safe_log('info', f"Tentative {attempt + 1}/{max_retries} pour {url}")
                
                response = await self.session.get(url)
                
                if response.status_code == 403:
                    await safe_log('warning', f"Accès refusé (403) pour {url}, tentative {attempt + 1}")
                    if attempt < max_retries - 1:
                        await self.random_delay(5.0, 15.0)
                        continue
                    
                elif response.status_code == 429:
                    await safe_log('warning', f"Trop de requêtes (429) pour {url}, attente plus longue")
                    if attempt < max_retries - 1:
                        await self.random_delay(10.0, 30.0)
                        continue
                
                response.raise_for_status()
                
                # Vérifier si la page contient des indicateurs de détection
                content = response.text
                if any(indicator in content.lower() for indicator in [
                    'captcha', 'robot', 'blocked', 'access denied', 
                    'security check', 'unusual traffic'
                ]):
                    await safe_log('warning', f"Détection possible sur {url}, rotation des headers")
                    if attempt < max_retries - 1:
                        continue
                
                return BeautifulSoup(content, 'html.parser')
                
            except Exception as e:
                await safe_log('error', f"Erreur tentative {attempt + 1} pour {url}: {e}")
                if attempt < max_retries - 1:
                    await self.random_delay(2.0, 8.0)
                    continue
        
        await safe_log('error', f"Échec de récupération après {max_retries} tentatives pour {url}")
        return None
    
    def clean_text(self, text: str) -> str:
        """Nettoie et normalise le texte."""
        if not text:
            return ''
        
        import re
        # Supprime les espaces multiples et les caractères de contrôle
        cleaned = re.sub(r'\s+', ' ', text.strip())
        return cleaned