import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
from datetime import datetime, timedelta
import sqlite3
import zipfile
import sys

class DBManager:

    def __init__(self, parent, conn_audit, db_path_audit, conn_compteurs, db_path_compteurs, conn_tasks, db_path_tasks, conn_library, db_path_library, update_callback=None):
            self.parent = parent
            self.conn_audit = conn_audit
            self.db_path_audit = db_path_audit
            self.conn_compteurs = conn_compteurs
            self.db_path_compteurs = db_path_compteurs
            self.conn_tasks = conn_tasks
            self.db_path_tasks = db_path_tasks
            self.conn_library = conn_library
            self.db_path_library = db_path_library
            self.update_callback = update_callback

            # Définir le chemin de base comme le dossier de l'exécutable
            self.project_root = os.path.dirname(os.path.abspath(sys.argv[0]))
            
            # Définir les chemins relatifs pour les dossiers et fichiers
            self.config_file = os.path.join(self.project_root, "config.ini")
            self.nomenclatures_file = os.path.join(self.project_root, "nomenclatures.json")
            self.sites_file = os.path.join(self.project_root, "sites.json")
            self.last_export_file = os.path.join(self.project_root, "last_export.txt")

            # Frame principale
            self.main_frame = ttk.LabelFrame(self.parent, text="Gestion des Bases de Données")
            self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Section pour Audit
            ttk.Label(self.main_frame, text="Base de données Audit", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
            
            # Ligne Corrigée : On vérifie si db_path_audit n'est pas None
            audit_path_text = f"Emplacement actuel : {os.path.dirname(self.db_path_audit)}" if self.db_path_audit else "Emplacement actuel : Désactivé"
            self.current_path_label_audit = ttk.Label(self.main_frame, text=audit_path_text)
            self.current_path_label_audit.pack(anchor="w", pady=2)

            ttk.Separator(self.main_frame, orient="horizontal").pack(fill="x", pady=10)

            # Section pour Compteurs
            ttk.Label(self.main_frame, text="Base de données Compteurs", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
            compteurs_path_text = f"Emplacement actuel : {os.path.dirname(self.db_path_compteurs)}" if self.db_path_compteurs else "Emplacement actuel : Désactivé"
            self.current_path_label_compteurs = ttk.Label(self.main_frame, text=compteurs_path_text)
            self.current_path_label_compteurs.pack(anchor="w", pady=2)

            ttk.Separator(self.main_frame, orient="horizontal").pack(fill="x", pady=10)

            # Section pour Tâches
            ttk.Label(self.main_frame, text="Base de données Tâches", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
            tasks_path_text = f"Emplacement actuel : {os.path.dirname(self.db_path_tasks)}" if self.db_path_tasks else "Emplacement actuel : Non défini"
            self.current_path_label_tasks = ttk.Label(self.main_frame, text=tasks_path_text)
            self.current_path_label_tasks.pack(anchor="w", pady=2)

            ttk.Separator(self.main_frame, orient="horizontal").pack(fill="x", pady=10)

            # Section pour Bibliothèque
            ttk.Label(self.main_frame, text="Base de données Bibliothèque", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
            library_path_text = f"Emplacement actuel : {os.path.dirname(self.db_path_library)}" if self.db_path_library else "Emplacement actuel : Non défini"
            self.current_path_label_library = ttk.Label(self.main_frame, text=library_path_text)
            self.current_path_label_library.pack(anchor="w", pady=2)

            ttk.Separator(self.main_frame, orient="horizontal").pack(fill="x", pady=10)

            # Afficher la date du dernier export
            last_export_date = self.get_last_export_date()
            if last_export_date:
                last_export_label = ttk.Label(self.main_frame, text=f"Dernier export global : {last_export_date.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                last_export_label = ttk.Label(self.main_frame, text="Aucun export global effectué.")
            last_export_label.pack(anchor="w", pady=5)

            # Bouton pour exporter tout en .zip
            ttk.Button(self.main_frame, text="Exporter Tout (.zip)", command=self.export_all_to_zip).pack(pady=5)

            ttk.Separator(self.main_frame, orient="horizontal").pack(fill="x", pady=10)

            # Bouton pour réinitialiser les préférences "Ne plus demander"
            ttk.Button(self.main_frame, text="Réinitialiser 'Ne plus demander'", command=self.reset_skip_preferences).pack(pady=10)

            # Vérifier si un rappel d'export est nécessaire
            self.check_export_reminder()

            # Mettre à jour la structure de la table parameters pour ajouter les colonnes manquantes
            self.migrate_parameters_table()
        
    def migrate_parameters_table(self):
        """Ajoute les colonnes manquantes à la table parameters si elles n'existent pas."""
        if self.conn_audit:
            cursor = self.conn_audit.cursor()
            # Vérifier si la table parameters existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parameters'")
            if cursor.fetchone():
                # Vérifier les colonnes existantes
                cursor.execute("PRAGMA table_info(parameters)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Ajouter la colonne target si elle n'existe pas
                if "target" not in columns:
                    cursor.execute("ALTER TABLE parameters ADD COLUMN target REAL")
                    print("Colonne 'target' ajoutée à la table parameters.")
                
                # Ajouter la colonne max_value si elle n'existe pas
                if "max_value" not in columns:
                    cursor.execute("ALTER TABLE parameters ADD COLUMN max_value REAL")
                    print("Colonne 'max_value' ajoutée à la table parameters.")
                
                self.conn_audit.commit()

    def get_last_export_date(self):
        """Récupère la date du dernier export global à partir du fichier last_export.txt."""
        if os.path.exists(self.last_export_file):
            with open(self.last_export_file, "r") as f:
                date_str = f.read().strip()
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return None
        return None

    def save_last_export_date(self):
        """Sauvegarde la date actuelle comme étant celle du dernier export global."""
        with open(self.last_export_file, "w") as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def check_export_reminder(self):
        """Vérifie si un rappel d'export est nécessaire (plus de 30 jours depuis le dernier export)."""
        last_export_date = self.get_last_export_date()
        if last_export_date:
            days_since_last_export = (datetime.now() - last_export_date).days
            if days_since_last_export > 30:
                messagebox.showwarning(
                    "Rappel d'export",
                    f"Attention : cela fait {days_since_last_export} jours que vous n'avez pas exporté vos données.\n"
                    "Il est recommandé d'exporter vos données régulièrement pour éviter toute perte.\n"
                    "Voulez-vous exporter maintenant ?",
                    type=messagebox.YESNO
                )
                if messagebox.YES:
                    self.export_all_to_zip()
        else:
            messagebox.showinfo(
                "Premier export",
                "Aucun export global n'a été effectué.\n"
                "Il est recommandé d'exporter vos données pour éviter toute perte.\n"
                "Voulez-vous exporter maintenant ?",
                type=messagebox.YESNO
            )
            if messagebox.YES:
                self.export_all_to_zip()

    def export_all_to_zip(self):
        """Exporte toutes les bases de données, les dossiers de fichiers et les fichiers de config dans un fichier .zip."""
        # Demander à l'utilisateur où sauvegarder le fichier .zip
        zip_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
            title="Choisir l'emplacement pour exporter toutes les données"
        )
        if not zip_path:
            return

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # 1. Ajouter le dossier 'db' et ses fichiers
                db_dir = os.path.join(self.project_root, "db")
                if os.path.exists(db_dir):
                    for root, dirs, files in os.walk(db_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Calculer le chemin relatif dans le .zip
                            arcname = os.path.relpath(file_path, os.path.dirname(db_dir))
                            zipf.write(file_path, arcname)
                else:
                    print(f"Dossier 'db' introuvable, ignoré.")

                # 2. Ajouter le dossier 'fichiers' et ses sous-dossiers/fichiers
                files_dir = os.path.join(self.project_root, "fichiers")
                if os.path.exists(files_dir):
                    for root, dirs, files in os.walk(files_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Calculer le chemin relatif dans le .zip
                            arcname = os.path.relpath(file_path, os.path.dirname(files_dir))
                            zipf.write(file_path, arcname)
                else:
                    print(f"Dossier 'fichiers' introuvable, ignoré.")

                # 3. Ajouter le dossier 'bibliotheque' et ses sous-dossiers/fichiers
                library_dir = os.path.join(self.project_root, "bibliotheque")
                if os.path.exists(library_dir):
                    for root, dirs, files in os.walk(library_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Calculer le chemin relatif dans le .zip
                            arcname = os.path.relpath(file_path, os.path.dirname(library_dir))
                            zipf.write(file_path, arcname)
                else:
                    print(f"Dossier 'bibliotheque' introuvable, ignoré.")

                # 4. Ajouter les fichiers de configuration (config.ini, nomenclatures.json, sites.json)
                config_files = [
                    ("config.ini", self.config_file),
                    ("nomenclatures.json", self.nomenclatures_file),
                    ("sites.json", self.sites_file)
                ]
                for config_name, config_path in config_files:
                    if os.path.exists(config_path):
                        zipf.write(config_path, os.path.basename(config_path))
                    else:
                        print(f"Fichier de configuration '{config_name}' introuvable, ignoré.")

            # Sauvegarder la date de l'export
            self.save_last_export_date()

            messagebox.showinfo("Succès", f"Toutes les données ont été exportées avec succès vers {zip_path}.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'exportation en .zip : {str(e)}")

    def reset_skip_preferences(self):
        """Supprime le fichier config.ini pour réinitialiser les préférences."""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                messagebox.showinfo("Succès", "Le fichier de configuration a été supprimé.\nLes préférences seront réinitialisées au prochain démarrage.")
            else:
                messagebox.showinfo("Succès", "Aucun fichier de configuration n'existe.\nLes préférences sont déjà réinitialisées.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la suppression du fichier de configuration : {str(e)}")

    def create_tables_audit(self, cursor):
        """Crée les tables pour la base Audit."""
        cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            x_pos REAL DEFAULT 20,
            y_pos REAL DEFAULT 20,
            width REAL DEFAULT 150,
            height REAL DEFAULT 50,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS meters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            note TEXT,
            category_id INTEGER,
            x_pos REAL DEFAULT 20,
            y_pos REAL DEFAULT 60,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS parameters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meter_id INTEGER,
            name TEXT NOT NULL,
            target REAL,
            max_value REAL,
            unit TEXT,
            FOREIGN KEY (meter_id) REFERENCES meters(id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meter_id INTEGER,
            parameter_id INTEGER,
            date TEXT NOT NULL,
            value REAL NOT NULL,
            note TEXT,
            attachment_path TEXT,
            FOREIGN KEY (meter_id) REFERENCES meters(id),
            FOREIGN KEY (parameter_id) REFERENCES parameters(id)
        )''')

    def create_tables_compteurs(self, cursor):
        """Crée les tables pour la base Compteurs."""
        cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            x_pos REAL DEFAULT 20,
            y_pos REAL DEFAULT 20,
            width REAL DEFAULT 150,
            height REAL DEFAULT 50,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS meters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            note TEXT,
            category_id INTEGER,
            x_pos REAL DEFAULT 20,
            y_pos REAL DEFAULT 60,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meter_id INTEGER,
            date TEXT NOT NULL,
            meter_index INTEGER NOT NULL,
            consumption INTEGER DEFAULT 0,
            note TEXT,
            FOREIGN KEY (meter_id) REFERENCES meters(id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS base_indices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meter_id INTEGER,
            base_index INTEGER NOT NULL,
            FOREIGN KEY (meter_id) REFERENCES meters(id)
        )''')
        try:
            cursor.execute("ALTER TABLE readings ADD COLUMN consumption INTEGER DEFAULT 0")
        except:
            pass

    def create_tables_tasks(self, cursor):
        """Crée les tables pour la base Tâches."""
        cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            priority TEXT DEFAULT 'Moyenne',
            status TEXT DEFAULT 'En cours',
            recurrence TEXT DEFAULT 'Aucune'
        )''')

    def create_tables_library(self, cursor):
        """Crée les tables pour la base Bibliothèque."""
        cursor.execute('''CREATE TABLE IF NOT EXISTS library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT,
            file_path TEXT NOT NULL
        )''')
