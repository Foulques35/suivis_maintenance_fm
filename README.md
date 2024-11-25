## Projet Archiviste

Le code est généré par IA (GPT4), des adapations sont faites à la main selon les besoins.

Projet personnel pour la gestion de données et l'archivage de documents. \
Créer principalement pour le suivis des activités de maintenance d'un ou plusieurs bâtiments. 

**- 00** : Registre sert à archiver des activité et événements avec liaison de fichiers. \
**- 01** : P2-commande sert à suivre et archiver ses commandes avec liaisons de fichiers. \
**- 02** : P5-travaux sert à suivre les devis avec archivage des documents avec liaisons de fichiers. \
**- 03** à pour but de regrouper divers petites applications html autonomes (pour la compatibilité avec avec les supports mobiles) permettant de créer des rapports techniques simples. \
**- 04** : Archives-mails sert à stocker des fichiers eml et msg avec la possibilité de lire les mails et les pièces jointes. \
**- 05** : Archivision sert à créer des comptes rendu basé sur les images, avec l'ajout de repères et une architecture type "poupées russes". \
**- 06** : Version complète est une version des logiciels qui regroupe tous dans un dossier unique. Les fichiers sont dans "attachment", les bases de données dans le dossier db. Un lanceur unique est présent pour lancer les applications. \
**- Archiviste.py** :  sert à manipuler des fichiers pour les renommer selon une nomenclatures. \

### Les dépendances nécessaires pour exécuter le code sont :

**Python 3.12** \
**tkinter** : La bibliothèque pour créer des interfaces graphiques en Python. \
**tkcalendar** : Un module basé sur tkinter qui fournit des widgets de calendrier et de sélection de dates. \
**Sqlite3** : Une bibliothèque intégrée dans Python pour interagir avec une base de données SQLite. \
**locale** : Un module intégré pour gérer la configuration de la langue et du format de date. \
**datetime** : Une bibliothèque intégrée pour gérer les dates et les heures. \
**os** : Un module intégré pour les interactions avec le système de fichiers. \
**webbrowser** : Un module intégré permettant d'ouvrir des URLs dans un navigateur web. \
**tkinter.ttk** : La sous-bibliothèque ttk de tkinter pour des widgets à l'apparence plus moderne. \
**filedialog (partie de tkinter)** : Permet d'ouvrir des boîtes de dialogue pour la sélection de fichiers. \
**messagebox (partie de tkinter)** : Utilisé pour afficher des boîtes de message (erreurs, avertissements, succès, etc.). \
**Pillow** : pour ajouter des repères sur un canva. \
**Reportlab** : pour la création de documents PDF. \
**extract-msg** : pour lire les fichier eml et msg. \

### Installation des dépendances :
Pour les bibliothèques intégrées comme sqlite3, locale, datetime, os, et webbrowser, il n'y a pas besoin d'installation supplémentaire. \
Cependant, il faudra installer tkcalendar s'il n'est pas déjà disponible dans l'environnement. \

**installation de tkcalendar : pip install tkcalendar** \
**Installation de Pillow : pip install pillow** \
**Installation de Reportlab : pip install Reportlab** \
**Installation de extract-msg : pip install extract-msg** 

IDE : Thonny - https://thonny.org/
Discord : https://discord.gg/MFk2kUhD
