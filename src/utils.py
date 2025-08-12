"""Utilitaires partagés pour le projet."""

from apify import Actor


async def safe_log(level: str, message: str):
    """Fonction utilitaire pour le logging sécurisé."""
    try:
        # Vérification complète de l'existence d'Actor.log
        if Actor and hasattr(Actor, 'log') and Actor.log is not None:
            if hasattr(Actor.log, level):
                log_func = getattr(Actor.log, level, None)
                if log_func is not None and callable(log_func):
                    try:
                        result = log_func(message)
                        if result is not None:
                            await result
                        return
                    except Exception:
                        pass
    except Exception:
        pass
    
    # Fallback vers print en cas d'erreur ou si Actor.log n'est pas disponible
    print(f'[{level.upper()}] {message}')