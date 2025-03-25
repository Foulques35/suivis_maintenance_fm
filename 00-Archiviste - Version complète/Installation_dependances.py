import subprocess
import sys
import pkg_resources

# Liste des dépendances requises
REQUIRED_PACKAGES = [
    "Pillow",        # Pour le traitement des images
    "reportlab",     # Pour la génération de PDF
    "extract_msg",   # Pour la lecture des fichiers .msg
    "tkcalendar",    # Pour les widgets de calendrier
]

def check_and_install_packages():
    """Vérifie et installe les dépendances manquantes."""
    # Vérifier les packages déjà installés
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = [pkg for pkg in REQUIRED_PACKAGES if pkg.lower() not in installed]

    if missing:
        print(f"Installation des dépendances manquantes : {missing}")
        try:
            # Mettre à jour pip
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
            
            # Installer les packages manquants
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            print("Toutes les dépendances ont été installées avec succès.")
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de l'installation des dépendances : {e}")
            sys.exit(1)
    else:
        print("Toutes les dépendances sont déjà installées.")

def verify_installation():
    """Vérifie que toutes les dépendances sont correctement installées."""
    try:
        import PIL
        import reportlab
        import extract_msg
        import tkcalendar
        print("Vérification réussie : toutes les bibliothèques sont accessibles.")
    except ImportError as e:
        print(f"Erreur : une dépendance n'est pas correctement installée - {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Vérification des dépendances pour les applications...")
    check_and_install_packages()
    verify_installation()
    print("Configuration terminée. Vous pouvez maintenant exécuter vos applications.")