import os
import subprocess
import sys
import venv

# Chemin vers le dossier du projet
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
ENV_DIR = os.path.join(PROJECT_DIR, 'archiviste_env')

def create_virtual_environment():
    # Créer l'environnement virtuel
    venv.create(ENV_DIR, with_pip=True)
    print(f"Environnement virtuel créé dans {ENV_DIR}")

def install_dependencies():
    # Installer les dépendances nécessaires
    subprocess.check_call([os.path.join(ENV_DIR, 'bin', 'pip'), 'install', 'matplotlib', 'numpy', 'python-dateutil', 'tkcalendar'])
    print("Dépendances installées.")

def modify_main_script():
    # Modifier le script principal pour utiliser l'environnement virtuel
    main_script_path = os.path.join(PROJECT_DIR, 'archiviste.pyw')
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

def main():
    create_virtual_environment()
    install_dependencies()
    modify_main_script()
    print("Configuration terminée. Vous pouvez maintenant exécuter archiviste.pyw.")

if __name__ == "__main__":
    main()
