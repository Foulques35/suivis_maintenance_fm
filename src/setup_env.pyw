import os
import subprocess
import sys
import venv
import importlib.util

# Chemin vers le dossier du projet
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
ENV_DIR = os.path.join(PROJECT_DIR, 'archiviste_env')

def create_virtual_environment():
    # Créer l'environnement virtuel s'il n'existe pas déjà
    if not os.path.exists(ENV_DIR):
        venv.create(ENV_DIR, with_pip=True)
        print(f"Environnement virtuel créé dans {ENV_DIR}")
    else:
        print(f"Environnement virtuel déjà existant dans {ENV_DIR}")

def install_dependencies():
    # Installer les dépendances nécessaires
    pip_path = os.path.join(ENV_DIR, 'bin', 'pip')
    if os.path.exists(pip_path):
        subprocess.check_call([pip_path, 'install', 'matplotlib', 'numpy', 'python-dateutil', 'tkcalendar'])
        print("Dépendances installées.")
    else:
        print(f"Erreur : {pip_path} introuvable.")
        sys.exit(1)

def modify_main_script():
    # Modifier le script principal pour utiliser l'environnement virtuel
    main_script_path = os.path.join(PROJECT_DIR, 'archiviste.pyw')
    if os.path.exists(main_script_path):
        with open(main_script_path, 'r') as file:
            lines = file.readlines()

        with open(main_script_path, 'w') as file:
            for line in lines:
                if line.startswith('import os'):
                    file.write(line)
                    file.write(f'import sys\n')
                    file.write(f'sys.path.insert(0, os.path.join(os.path.dirname(__file__), \'archiviste_env\', \'lib\', f\'python{sys.version_info.major}.{sys.version_info.minor}\', \'site-packages\'))\n')
                else:
                    file.write(line)

        print(f"Script principal modifié pour utiliser l'environnement virtuel.")
    else:
        print(f"Erreur : {main_script_path} introuvable.")
        sys.exit(1)

def check_dependencies():
    # Vérifier que toutes les dépendances sont installées
    dependencies = {
        "matplotlib": "matplotlib",
        "numpy": "numpy",
        "dateutil": "python-dateutil",
        "tkcalendar": "tkcalendar"
    }
    missing = []
    for module_name in dependencies.keys():
        if importlib.util.find_spec(module_name) is None:
            missing.append(dependencies[module_name])

    if missing:
        print(f"Modules manquants : {', '.join(missing)}. Veuillez exécuter setup_env.py pour installer les dépendances.")
        sys.exit(1)
    else:
        print("Toutes les dépendances sont satisfaites.")

def main():
    create_virtual_environment()
    install_dependencies()
    modify_main_script()
    check_dependencies()
    print("Configuration terminée. Vous pouvez maintenant exécuter archiviste.pyw.")

if __name__ == "__main__":
    main()
