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


@dataclass
class Product:
    """Structure de données pour un produit."""
    title: str
    price: Optional[float]
    currency: str
    url: str
    image_url: Optional[str]
    rating: Optional[float]
    reviews_count: Optional[int]
    availability: str
    seller: Optional[str]
    platform: str
    scraped_at: datetime
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    
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
            'scraped_at': self.scraped_at.isoformat(),
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
        
    async def __aenter__(self):
        """Initialise la session HTTP."""
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session = AsyncClient(headers=headers, follow_redirects=True, timeout=30.0)
        return self
        
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
    
    async def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Ajoute un délai aléatoire pour éviter la détection."""
        delay = random.uniform(min_seconds, max_seconds)
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
    
    async def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Récupère et parse le contenu d'une page."""
        try:
            await self.random_delay()
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            return soup
            
        except Exception as e:
            Actor.log.warning(f'Erreur lors du chargement de {url}: {str(e)}')
            return None
    
    def clean_text(self, text: str) -> str:
        """Nettoie et normalise le texte."""
        if not text:
            return ''
        
        import re
        # Supprime les espaces multiples et les caractères de contrôle
        cleaned = re.sub(r'\s+', ' ', text.strip())
        return cleaned