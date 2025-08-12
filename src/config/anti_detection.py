"""Configuration pour les techniques anti-détection."""

import random
from typing import List, Dict, Any


class AntiDetectionConfig:
    """Configuration pour contourner les protections anti-bot."""
    
    # Liste de proxies gratuits (à remplacer par des proxies premium en production)
    FREE_PROXIES = [
        # Ces proxies sont des exemples, ils peuvent ne pas fonctionner
        # En production, utilisez des services de proxies premium
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
        "http://proxy3.example.com:8080",
    ]
    
    # User agents réalistes et récents
    REALISTIC_USER_AGENTS = [
        # Chrome Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        
        # Chrome macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        
        # Firefox Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        
        # Safari macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        
        # Edge Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        
        # Chrome Linux
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    # Délais recommandés par plateforme (en secondes)
    PLATFORM_DELAYS = {
        'amazon': {'min': 3.0, 'max': 12.0},
        'etsy': {'min': 4.0, 'max': 15.0},
        'ebay': {'min': 2.0, 'max': 8.0},
        'walmart': {'min': 3.0, 'max': 10.0},
        'shopify': {'min': 2.0, 'max': 7.0},
        'default': {'min': 2.0, 'max': 8.0}
    }
    
    # Headers communs par plateforme
    PLATFORM_HEADERS = {
        'amazon': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        },
        'etsy': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        },
        'ebay': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    }
    
    # Indicateurs de blocage par plateforme
    BLOCK_INDICATORS = {
        'amazon': [
            'captcha', 'robot', 'blocked', 'access denied',
            'security check', 'unusual traffic', 'automated requests'
        ],
        'etsy': [
            'captcha', 'robot', 'blocked', 'access denied',
            'security check', 'unusual traffic', 'rate limit',
            'temporarily unavailable'
        ],
        'ebay': [
            'captcha', 'blocked', 'access denied', 'security check',
            'unusual activity', 'automated traffic'
        ],
        'walmart': [
            'captcha', 'blocked', 'access denied', 'bot',
            'automated requests', 'security check'
        ],
        'shopify': [
            'captcha', 'blocked', 'access denied', 'rate limit',
            'too many requests', 'security check'
        ]
    }
    
    @staticmethod
    def get_random_user_agent() -> str:
        """Retourne un User-Agent aléatoire."""
        return random.choice(AntiDetectionConfig.REALISTIC_USER_AGENTS)
    
    @staticmethod
    def get_random_proxy() -> str:
        """Retourne un proxy aléatoire."""
        if AntiDetectionConfig.FREE_PROXIES:
            return random.choice(AntiDetectionConfig.FREE_PROXIES)
        return None
    
    @staticmethod
    def get_platform_delay(platform: str) -> tuple:
        """Retourne les délais min/max pour une plateforme."""
        delays = AntiDetectionConfig.PLATFORM_DELAYS.get(
            platform.lower(), 
            AntiDetectionConfig.PLATFORM_DELAYS['default']
        )
        return delays['min'], delays['max']
    
    @staticmethod
    def get_platform_headers(platform: str, base_url: str = None) -> Dict[str, str]:
        """Retourne les headers spécifiques à une plateforme."""
        headers = AntiDetectionConfig.PLATFORM_HEADERS.get(
            platform.lower(), 
            AntiDetectionConfig.PLATFORM_HEADERS['amazon']
        ).copy()
        
        # Ajouter le referer si l'URL de base est fournie
        if base_url:
            headers['Referer'] = base_url
        
        return headers
    
    @staticmethod
    def get_block_indicators(platform: str) -> List[str]:
        """Retourne les indicateurs de blocage pour une plateforme."""
        return AntiDetectionConfig.BLOCK_INDICATORS.get(
            platform.lower(), 
            ['captcha', 'blocked', 'access denied']
        )
    
    @staticmethod
    def generate_realistic_headers(platform: str = None, base_url: str = None) -> Dict[str, str]:
        """Génère des headers HTTP réalistes."""
        user_agent = AntiDetectionConfig.get_random_user_agent()
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice([
                'en-US,en;q=0.9',
                'en-GB,en;q=0.9',
                'fr-FR,fr;q=0.9,en;q=0.8',
                'de-DE,de;q=0.9,en;q=0.8',
                'es-ES,es;q=0.9,en;q=0.8'
            ]),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }
        
        # Ajouter des headers spécifiques au navigateur
        if 'Chrome' in user_agent:
            headers.update({
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': random.choice(['"Windows"', '"macOS"', '"Linux"'])
            })
        
        # Ajouter les headers spécifiques à la plateforme
        if platform:
            platform_headers = AntiDetectionConfig.get_platform_headers(platform, base_url)
            headers.update(platform_headers)
        
        return headers