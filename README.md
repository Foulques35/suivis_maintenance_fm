# Archiviste 📚

![Linux](https://img.shields.io/badge/Linux-Fedora_41-blue)
![Windows](https://img.shields.io/badge/Windows-10%2F11-blue)
![Version](https://img.shields.io/badge/Version-1.0.0-green)

**Archiviste** est une application intuitive et multi-plateforme conçue pour gérer efficacement des relevés techniques, des compteurs, des tâches, et une bibliothèque de fichiers. Développée avec Python et une interface graphique (Tkinter), elle offre une solution complète pour organiser vos données et documents, que vous soyez sur Linux ou Windows.

## Aperçu

Archiviste regroupe quatre modules principaux pour répondre à vos besoins d’organisation et de gestion :

- **Relevés** : Suivez et analysez vos relevés techniques avec des graphiques interactifs.
- **Compteurs** : Gérez vos compteurs (électricité, eau, etc.) avec des rapports détaillés.
- **Tâches** : Planifiez vos activités avec un agenda et liez des documents associés.
- **Bibliothèque** : Organisez vos fichiers dans une arborescence personnalisée.

Que vous soyez un technicien, un gestionnaire de projet ou un particulier, Archiviste simplifie la gestion de vos données et documents avec une interface claire et accessible.

## Fonctionnalités principales

### 📊 Gestion des relevés et compteurs
- Saisie et suivi des relevés techniques et des compteurs.
- Génération de graphiques (via Matplotlib) pour visualiser les tendances.
- Exportation des données sous format CSV pour une analyse externe.

### 📅 Gestion des tâches avec agenda
- Création et gestion de tâches avec prise en charge de la récurrence (quotidienne, hebdomadaire, mensuelle, etc.).
- Vue agenda intégrée pour planifier vos échéances.
- Possibilité de lier des fichiers à vos tâches pour une meilleure organisation.

### 🗂️ Bibliothèque de fichiers
- Organisation des fichiers dans une arborescence (année/catégorie/projet).
- Options de nommage personnalisées (avec nomenclature) ou conservation des noms d’origine.
- Gestion des sites et nomenclatures via les fichiers `sites.json` et `nomenclatures.json`.

### ⚙️ Compatibilité et personnalisation
- Compatible avec **Linux** (testé sur Fedora 41) et **Windows** (10/11).
- Interface graphique légère et intuitive (Tkinter).
- Personnalisation via des fichiers de configuration (`sites.json`& `nomenclatures.json`).

## Installation

### Prérequis
- **Linux** :
  - Dépendances système :
    ```
    sudo dnf install libX11 freetype libpng  # Fedora
    sudo apt-get install libx11-6 libfreetype6 libpng16-16  # Ubuntu
    ```
- **Windows** :
  - Placer l'éxécutable dans le dossier ou vous souhaitez avoir l'application et lancez la.

### Téléchargement et exécution
1. Téléchargez le dossier src.
2. Placez l’application dans un dossier où vous avez les permissions d’écriture.
3. Lancez l’application :
   - **Windows & Linux** :
     - Lancez `setup_env.pyw`. Une fois terminé, l'environnement virtuel python avec les dépendances sont instalés.
     - Lancez `archiviste.pyw` pour lancer l'application.

### Note sur les alertes antivirus (Windows)
Sous Windows, Microsoft Defender peut signaler `Archiviste.exe` comme un malware (faux positif dû à PyInstaller). Pour l’autoriser :
1. Dans **Sécurité Windows**, allez dans "Protection contre les virus et menaces".
2. Sous l’alerte, cliquez sur "Actions" > "Autoriser".
3. Si nécessaire, ajoutez une exclusion dans "Paramètres de protection contre les virus et menaces" > "Exclusions".

Une signature numérique sera ajoutée dans une prochaine version pour éliminer ces alertes.

## Configuration
- **Sites et nomenclatures** : Éditez les fichiers `sites.json` et `nomenclatures.json` (situés à la racine de l’application) pour personnaliser les options de la Bibliothèque.
- **Préférences** : Le fichier `config.ini` permet de sauvegarder certaines préférences (par exemple, masquer les messages de dépendances).

## Développement
- Développé sous **Linux - Fedora 41**.
- Construit avec **Python** (Tkinter, Matplotlib, Tkcalendar).
- Testé sur Linux (Fedora 41) et Windows (10/11). Des différences mineures dans les couleurs de l’interface peuvent apparaître selon le système.

## Remerciements
Merci d’essayer Archiviste ! Ce projet tente de simplifier votre gestion quotidienne. 🚀
- Python : https://www.python.org/downloads/ 
- IDE : Thonny - https://thonny.org/ 
- Discord : https://discord.gg/MFk2kUhD

