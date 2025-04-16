Archiviste
Archiviste est une application de gestion des relevés techniques et des compteurs, conçue pour organiser et analyser les données de manière intuitive. Elle offre une interface graphique avec des onglets colorés pour différencier les types de relevés (techniques et compteurs), ainsi que des fonctionnalités pour sauvegarder et importer des bases de données.
Fonctionnalités

Relevés techniques (bleu clair) : Gestion des relevés techniques avec paramètres personnalisés.
Compteurs (jaune clair) : Gestion des relevés de compteurs avec calcul de consommation.
Synthèse relevés (bleu clair) : Rapports détaillés des relevés techniques.
Graphique relevés (bleu clair) : Visualisation graphique des relevés techniques.
Synthèse compteurs (jaune clair) : Rapports détaillés des compteurs.
Graphique compteurs (jaune clair) : Visualisation graphique des compteurs.
Gestion relevés (bleu foncé) : Gestion des compteurs et catégories pour les relevés techniques.
Gestion compteurs (jaune foncé) : Gestion des compteurs et catégories pour les relevés de compteurs.
Sauvegardes (noir) : Gestion des bases de données (sauvegarde, import, changement d’emplacement).

Utilisation avec l’exécutable (Linux)
Un exécutable autonome est disponible pour Linux, ce qui permet de lancer l’application sans installer Python ou les dépendances.
Prérequis

Un système Linux avec les bibliothèques graphiques nécessaires (comme libtk pour Tkinter, généralement déjà présentes sur la plupart des distributions modernes).

Instructions

Télécharger l’exécutable :

Obtiens le fichier archiviste (fourni par le développeur).


Rendre l’exécutable exécutable :
chmod +x archiviste


Lancer l’application :
./archiviste


Utilisation :

L’application s’ouvrira avec une interface à onglets.
Les bases de données (audit.db pour les relevés techniques, meters.db pour les compteurs) seront créées dans le répertoire où l’exécutable est exécuté.
Utilise l’onglet "Sauvegardes" pour sauvegarder, importer, ou changer les emplacements des bases de données.



Utilisation avec les scripts Python (développeurs)
Si tu préfères exécuter les scripts Python directement, voici comment procéder.
Prérequis

Python 3.6 ou supérieur.
Les dépendances suivantes : matplotlib, numpy, python-dateutil.

Installation des dépendances

Crée un environnement virtuel :
cd /chemin/vers/Archiviste
python3 -m venv python-env


Active l’environnement virtuel :
source python-env/bin/activate


Installe les dépendances :
pip install matplotlib numpy python-dateutil



Lancer l’application

Depuis le répertoire de l’application :
cd /chemin/vers/Archiviste
./python-env/bin/python archiviste.pyw


Utilisation :

L’application s’ouvrira avec une interface à onglets.
Les bases de données (audit.db, meters.db) seront créées dans des dossiers par défaut (db-audit, db-compteurs) ou dans les emplacements configurés via config.json.



Gestion des bases de données

Changer les emplacements :

Dans l’onglet "Sauvegardes", utilise les boutons "Changer l’emplacement (Audit)" ou "Changer l’emplacement (Compteurs)" pour sélectionner de nouveaux dossiers pour les bases de données.
Si une base existe déjà dans le nouvel emplacement, tu peux choisir de l’utiliser ou de la remplacer par la base actuelle.


Sauvegarder :

Clique sur "Sauvegarder la base Audit" ou "Sauvegarder la base Compteurs" pour créer une sauvegarde manuelle.


Importer :

Clique sur "Afficher les sauvegardes Audit" ou "Afficher les sauvegardes Compteurs" pour voir la liste des sauvegardes et en importer une.



Structure du projet
/chemin/vers/Archiviste/
├── archiviste.pyw          # Script principal
├── python-env/             # Environnement virtuel (optionnel)
├── config.json             # Fichier de configuration (créé au premier lancement)
├── scripts_releves/        # Modules pour les relevés techniques
│   ├── db_designer.py
│   ├── meter_readings.py
│   ├── meter_reports.py
│   ├── meter_graphs.py
│   └── db_manager.py
└── scripts_compteurs/      # Modules pour les compteurs
    ├── db_designer.py
    ├── meter_readings.py
    ├── meter_reports.py
    └── meter_graphs.py

Support
Pour toute question ou problème, contacte le développeur ou consulte les issues sur le dépôt Git (si disponible).

Développé par Maxime Bousquet - Avril 2025

