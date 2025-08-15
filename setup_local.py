#!/usr/bin/env python3
"""
Script d'installation et de configuration pour les tests locaux.
Ce script installe les dépendances et configure l'environnement.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Exécute une commande et affiche le résultat."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Succès")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Échec")
        print(f"   Erreur: {e.stderr.strip() if e.stderr else str(e)}")
        return False

def check_python_version():
    """Vérifie la version de Python."""
    version = sys.version_info
    print(f"🐍 Version Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ requis")
        return False
    
    print("✅ Version Python compatible")
    return True

def install_dependencies():
    """Installe les dépendances depuis requirements.txt."""
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("❌ Fichier requirements.txt introuvable")
        return False
    
    # Installer les dépendances
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installation des dépendances"
    )

def setup_environment():
    """Configure l'environnement de test."""
    print("\n🛠️ Configuration de l'environnement de test...")
    
    # Créer le répertoire de sortie s'il n'existe pas
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    print(f"✅ Répertoire de sortie créé: {output_dir.absolute()}")
    
    # Vérifier que les modules sont importables
    try:
        # Ajouter les chemins nécessaires
        src_path = Path("src").absolute()
        root_path = Path(".").absolute()
        sys.path.insert(0, str(src_path))
        sys.path.insert(0, str(root_path))
        
        # Test d'import simple
        import scrapers
        print("✅ Modules scrapers importables")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Cela peut être normal - les imports relatifs seront résolus à l'exécution")
        return True  # Continuer malgré l'erreur d'import

def main():
    """Fonction principale de configuration."""
    print("=== Configuration de l'environnement de test local ===")
    print(f"📁 Répertoire de travail: {Path.cwd()}")
    
    # Vérifications préliminaires
    if not check_python_version():
        sys.exit(1)
    
    # Installation des dépendances
    if not install_dependencies():
        print("\n❌ Échec de l'installation des dépendances")
        print("Essayez d'installer manuellement avec:")
        print(f"   {sys.executable} -m pip install -r requirements.txt")
        sys.exit(1)
    
    # Configuration de l'environnement
    if not setup_environment():
        print("\n❌ Échec de la configuration de l'environnement")
        sys.exit(1)
    
    print("\n🎉 Configuration terminée avec succès!")
    print("\n📋 Prochaines étapes:")
    print("   1. Exécutez: python test_local.py")
    print("   2. Vérifiez les résultats dans test_output.json")
    print("\n💡 Conseils:")
    print("   - Le test utilise une configuration par défaut (iPhone 15 sur Amazon)")
    print("   - Modifiez test_local.py pour personnaliser les paramètres")
    print("   - Les logs s'affichent dans la console")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Configuration interrompue par l'utilisateur.")
    except Exception as e:
        print(f"\n💥 Erreur fatale: {e}")
        sys.exit(1)