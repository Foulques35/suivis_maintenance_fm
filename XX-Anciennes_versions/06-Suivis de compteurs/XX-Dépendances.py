import subprocess
import sys
import pkg_resources

# Liste des dépendances nécessaires
DEPENDENCIES = [
    "matplotlib",
    "numpy"
]

def check_and_install_dependencies():
    """Vérifie et installe les dépendances manquantes."""
    print("Vérification des dépendances...")

    # Vérifier si chaque dépendance est installée
    missing = []
    for package in DEPENDENCIES:
        try:
            pkg_resources.require(package)
            print(f"{package} est déjà installé.")
        except pkg_resources.DistributionNotFound:
            print(f"{package} n'est pas installé. Installation en cours...")
            missing.append(package)

    # Installer les dépendances manquantes
    if missing:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            print("Toutes les dépendances ont été installées avec succès.")
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de l'installation des dépendances : {e}")
            sys.exit(1)

def main():
    """Vérifie les dépendances et lance l'application."""
    check_and_install_dependencies()

    # Lancer l'application principale
    try:
        print("Lancement de l'application Rapport-compteurs.py...")
        subprocess.check_call([sys.executable, "00-DB_designer.py"])
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du lancement de l'application : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
