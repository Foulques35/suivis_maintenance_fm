Projet Archiviste

Projet personnel pour la gestion de données et l'archivage de documents.
Créer principalement pour le suivis des activités de maintenance d'un ou plusieurs bâtiments.

La première application : Registre sert à archiver des activité et événements.
La seconde application : Archiviste sert à manipuler des fichiers pour les renommer selon une nomenclatures.
La troisième application : P2-commande sert à suivre et archiver ses commandes.

Le code est généré par IA (GPT4), des adapations sont faites à la main selon les besoins.

Les dépendances nécessaires pour exécuter le code sont :

Python 3.12
tkinter : La bibliothèque pour créer des interfaces graphiques en Python.
tkcalendar : Un module basé sur tkinter qui fournit des widgets de calendrier et de sélection de dates.
sqlite3 : Une bibliothèque intégrée dans Python pour interagir avec une base de données SQLite.
locale : Un module intégré pour gérer la configuration de la langue et du format de date.
datetime : Une bibliothèque intégrée pour gérer les dates et les heures.
os : Un module intégré pour les interactions avec le système de fichiers.
webbrowser : Un module intégré permettant d'ouvrir des URLs dans un navigateur web.
tkinter.ttk : La sous-bibliothèque ttk de tkinter pour des widgets à l'apparence plus moderne.
filedialog (partie de tkinter) : Permet d'ouvrir des boîtes de dialogue pour la sélection de fichiers.
messagebox (partie de tkinter) : Utilisé pour afficher des boîtes de message (erreurs, avertissements, succès, etc.).
Flask : utiliser pour le serveur webhook.
Request : utiliser pour envoyer des données via webhook.

Installation des dépendances :
Pour les bibliothèques intégrées comme sqlite3, locale, datetime, os, et webbrowser, il n'y a pas besoin d'installation supplémentaire. 
Cependant, il faudra installer tkcalendar s'il n'est pas déjà disponible dans l'environnement.

**installation de tkcalendar : pip install tkcalendar**


**Installation de requests + flask : pip install Flask requests**


