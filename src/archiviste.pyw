import os
import sys
import importlib.util
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import configparser
import shutil

# Ajouter le répertoire racine du projet au sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Importation des modules ---
# Tâches et Bibliothèque
from scripts_bibliotheque.archiviste_taches import TaskManager
from scripts_bibliotheque.bibliotheque import LibraryManager
# Recherche Globale
from global_search import GlobalSearch
# Compteurs
from scripts_compteurs.db_designer_compteur import DBDesigner as CompteursDBDesigner
from scripts_compteurs.meter_readings_compteur import MeterReadings as CompteursMeterReadings
from scripts_compteurs.meter_reports_compteur import MeterReports as CompteursMeterReports
from scripts_compteurs.meter_graphs_compteur import MeterGraphs as CompteursMeterGraphs
# Gestion DB
from scripts_releves.db_manager import DBManager


# Gérer les chemins pour PyInstaller
def resource_path(relative_path):
    """Retourne le chemin absolu pour les fichiers inclus dans l'exécutable PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# Chemin pour les fichiers de données (bases de données, sauvegardes)
DATA_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
DB_DIR = os.path.join(DATA_DIR, "db")
BACKUP_DIR = os.path.join(DATA_DIR, "db_backup")

DEPENDENCIES = {
    "matplotlib": "matplotlib",
    "numpy": "numpy",
    "dateutil": "python-dateutil",
    "tkcalendar" : "tkcalendar"
}

def check_dependencies():
    missing = []
    for module_name, package_name in DEPENDENCIES.items():
        if importlib.util.find_spec(module_name) is None:
            missing.append(package_name)
    try:
        import tkinter
    except ImportError:
        missing.append("tkinter")
    if missing:
        error_message = (
            f"Modules manquants : {', '.join(missing)}.\n"
            "Exécutez avec l'environnement 'archiviste_audit_env_python'.\n"
            "Windows : archiviste_audit_env_python\\Scripts\\python.exe archiviste.pyw\n"
            "Linux : ./archiviste_audit_env_python/bin/python archiviste.pyw"
        )
        print(error_message)
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Erreur", error_message)
            root.destroy()
        except:
            pass
        sys.exit(1)

check_dependencies()


def show_dependencies_ok_window():
    config_path = os.path.join(DATA_DIR, "config.ini")
    config = configparser.ConfigParser()
    if os.path.exists(config_path):
        config.read(config_path)
        if config.getboolean("Settings", "hide_dependencies_message", fallback=False):
            return
    window = tk.Toplevel()
    window.title("Vérification des dépendances")
    window.geometry("300x150")
    window.resizable(False, False)
    window.transient()
    window.grab_set()
    label = ttk.Label(window, text="Les dépendances sont satisfaites.", justify="center")
    label.pack(pady=20)
    hide_var = tk.BooleanVar(value=False)
    checkbox = ttk.Checkbutton(window, text="Ne plus afficher ce message", variable=hide_var)
    checkbox.pack(pady=10)
    def on_ok():
        if hide_var.get():
            config["Settings"] = {"hide_dependencies_message": "True"}
            with open(config_path, "w") as configfile:
                config.write(configfile)
        window.destroy()
    ok_button = ttk.Button(window, text="OK", command=on_ok)
    ok_button.pack(pady=10)
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.wait_window()

class CustomNotebook:
    def __init__(self, parent):
        self.parent = parent
        self.tabs = []
        self.frames = []
        self.current_tab = None

        self.tab_frame = tk.Frame(parent, bg="#D3D3D3")
        self.tab_frame.pack(fill="x")

        self.content_frame = tk.Frame(parent)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def add(self, frame, text, bg_color, fg_color):
        btn = tk.Button(
            self.tab_frame,
            text=text,
            bg=bg_color,
            fg=fg_color,
            font=("Arial", 10, "bold"),
            relief="raised",
            borderwidth=2,
            command=lambda: self.select_tab(frame)
        )
        btn.pack(side="left", padx=2, pady=2)
        self.tabs.append(btn)
        self.frames.append(frame)
        frame.pack_forget()
        if not self.current_tab:
            self.select_tab(frame)

    def select_tab(self, frame):
        if self.current_tab:
            self.current_tab.pack_forget()
        self.current_tab = frame
        self.current_tab.pack(fill="both", expand=True)
        for btn, frm in zip(self.tabs, self.frames):
            if frm == frame:
                btn.config(relief="sunken")
            else:
                btn.config(relief="raised")

class ArchivisteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Archiviste")
        self.root.geometry("1600x900")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Créer le dossier db si nécessaire
        os.makedirs(DB_DIR, exist_ok=True)

        # --- Chemins et Connexions aux DBs ---
        # Note: 'audit.db' est commenté car les modules associés le sont aussi dans le code fourni
        # self.db_path_audit = os.path.join(DB_DIR, "audit.db") 
        self.db_path_compteurs = os.path.join(DB_DIR, "meters.db")
        self.db_path_tasks = os.path.join(DB_DIR, "tasks.db")
        self.db_path_library = os.path.join(DB_DIR, "library.db")

        # self.conn_audit = sqlite3.connect(self.db_path_audit, check_same_thread=False)
        self.conn_compteurs = sqlite3.connect(self.db_path_compteurs, check_same_thread=False)
        self.conn_tasks = sqlite3.connect(self.db_path_tasks, check_same_thread=False)
        self.conn_library = sqlite3.connect(self.db_path_library, check_same_thread=False)

        # Création des tables si elles n'existent pas
        self.create_tables_compteurs(self.conn_compteurs.cursor())
        self.create_tables_tasks(self.conn_tasks.cursor())
        self.create_tables_library(self.conn_library.cursor())
        self.conn_compteurs.commit()
        self.conn_tasks.commit()
        self.conn_library.commit()

        # --- Création du Notebook personnalisé ---
        self.notebook = CustomNotebook(self.root)

        # --- Création des onglets (frames) ---
        self.tab_global_search = tk.Frame(self.notebook.content_frame)
        self.tab_tasks = tk.Frame(self.notebook.content_frame)
        self.tab_library = tk.Frame(self.notebook.content_frame)
        self.tab_db_manager = tk.Frame(self.notebook.content_frame)
        self.tab_compteurs_readings = tk.Frame(self.notebook.content_frame)
        self.tab_compteurs_reports = tk.Frame(self.notebook.content_frame)
        self.tab_compteurs_graphs = tk.Frame(self.notebook.content_frame)
        self.tab_compteurs_design = tk.Frame(self.notebook.content_frame)

        # --- Ajout des onglets au Notebook ---
        # NOTE: L'ordre ici définit l'ordre d'affichage des boutons
        self.notebook.add(self.tab_global_search, text="Recherche", bg_color="#FFA500", fg_color="black")
        self.notebook.add(self.tab_tasks, text="Tâches", bg_color="#98FB98", fg_color="black")
        self.notebook.add(self.tab_library, text="Bibliothèque", bg_color="#FFB6C1", fg_color="black")
        self.notebook.add(self.tab_compteurs_readings, text="Compteurs", bg_color="#FFFFE0", fg_color="black")
        self.notebook.add(self.tab_compteurs_reports, text="Synthèse compteurs", bg_color="#FFFFE0", fg_color="black")
        self.notebook.add(self.tab_compteurs_graphs, text="Graphique compteurs", bg_color="#FFFFE0", fg_color="black")
        self.notebook.add(self.tab_compteurs_design, text="Gestion compteurs", bg_color="#FFD700", fg_color="black")
        self.notebook.add(self.tab_db_manager, text="Sauvegardes", bg_color="#000000", fg_color="white")

        # --- Initialisation des modules dans leurs onglets respectifs ---
        
        # Bibliothèque (initialisée d'abord car nécessaire pour Tâches et Recherche)
        self.library_manager = LibraryManager(self.tab_library, self.conn_library)
        
        # Recherche Globale
        self.global_search_manager = GlobalSearch(self.tab_global_search, self.conn_tasks, self.conn_library, self.library_manager)
        
        # Tâches
        self.task_manager = TaskManager(self.tab_tasks, self.conn_tasks, self.conn_library, self.library_manager)

        # Compteurs
        self.db_designer_compteurs = CompteursDBDesigner(self.tab_compteurs_design, self.conn_compteurs)
        self.meter_readings_compteurs = CompteursMeterReadings(self.tab_compteurs_readings, self.conn_compteurs)
        self.meter_graphs_compteurs = CompteursMeterGraphs(self.tab_compteurs_graphs)
        self.meter_reports_compteurs = CompteursMeterReports(self.tab_compteurs_reports, self.conn_compteurs, self.meter_graphs_compteurs)
        
        # Gestionnaire de bases de données
        self.db_manager = DBManager(
            self.tab_db_manager,
            None, None, # conn_audit et db_path_audit sont désactivés
            self.conn_compteurs, self.db_path_compteurs,
            self.conn_tasks, self.db_path_tasks,
            self.conn_library, self.db_path_library,
            self.update_connection_after_import
        )

        # Mettre à jour les connexions si nécessaire
        self.update_connection_after_import(None, self.conn_compteurs, self.conn_tasks, self.conn_library)

    def create_tables_compteurs(self, cursor):
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
            meter_id INTEGER PRIMARY KEY,
            base_index INTEGER NOT NULL,
            FOREIGN KEY (meter_id) REFERENCES meters(id)
        )''')
        try:
            cursor.execute("ALTER TABLE readings ADD COLUMN consumption INTEGER DEFAULT 0")
        except:
            pass

    def create_tables_tasks(self, cursor):
        cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            priority TEXT DEFAULT 'Moyenne',
            status TEXT DEFAULT 'En cours',
            recurrence TEXT DEFAULT 'Aucune'
        )''')
        # Ajout de la table des sous-tâches si elle n'est pas déjà dans le module
        cursor.execute('''CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'En cours',
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )''')

    def create_tables_library(self, cursor):
        cursor.execute('''CREATE TABLE IF NOT EXISTS library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            year TEXT,
            category TEXT,
            archives TEXT,
            project TEXT,
            site TEXT,
            nomenclature TEXT,
            emetteur TEXT,
            objet TEXT,
            version TEXT,
            file_path TEXT,
            notes TEXT
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS task_file_link (
            task_id INTEGER,
            file_id INTEGER,
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (file_id) REFERENCES library(id),
            PRIMARY KEY (task_id, file_id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS reading_file_link (
            reading_id INTEGER,
            file_id INTEGER,
            FOREIGN KEY (file_id) REFERENCES library(id),
            PRIMARY KEY (reading_id, file_id)
        )''')
        # Vérifier et ajouter la colonne archives si elle n'existe pas
        cursor.execute("PRAGMA table_info(library)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'archives' not in columns:
            cursor.execute("ALTER TABLE library ADD COLUMN archives TEXT")

    def update_connection_after_import(self, conn_audit, conn_compteurs, conn_tasks, conn_library):
        # Cette méthode est appelée par DBManager, on peut l'utiliser pour s'assurer
        # que toutes les instances ont les bonnes connexions si une DB est importée.
        # Pour l'instant, on se contente de réassigner les connexions existantes.
        self.conn_compteurs = conn_compteurs
        self.conn_tasks = conn_tasks
        self.conn_library = conn_library

        # Mise à jour des modules Compteurs
        self.db_designer_compteurs.conn = self.conn_compteurs
        self.db_designer_compteurs.cursor = self.conn_compteurs.cursor()
        self.db_designer_compteurs.update_ui()
        
        self.meter_readings_compteurs.conn = self.conn_compteurs
        self.meter_readings_compteurs.cursor = self.conn_compteurs.cursor()
        self.meter_readings_compteurs.load_meters_to_tree()
        
        self.meter_reports_compteurs.conn = self.conn_compteurs
        self.meter_reports_compteurs.cursor = self.conn_compteurs.cursor()
        
        # self.meter_graphs_compteurs.conn = self.conn_compteurs
        # self.meter_graphs_compteurs.cursor = self.conn_compteurs.cursor()

        # Mise à jour des modules Tâches
        self.task_manager.conn = self.conn_tasks
        self.task_manager.conn_library = self.conn_library
        self.task_manager.cursor = self.conn_tasks.cursor()
        self.task_manager.cursor_library = self.conn_library.cursor()
        self.task_manager.refresh_task_list()
        
        # Mise à jour des modules Bibliothèque
        self.library_manager.conn = self.conn_library
        self.library_manager.cursor = self.conn_library.cursor()
        self.library_manager.refresh_folder_list()
        
        # Mise à jour du module de Recherche
        self.global_search_manager.conn_tasks = self.conn_tasks
        self.global_search_manager.conn_library = self.conn_library
        self.global_search_manager.cursor_tasks = self.conn_tasks.cursor()
        self.global_search_manager.cursor_library = self.conn_library.cursor()


    def on_closing(self):
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter ?"):
            # if hasattr(self, 'conn_audit'):
            #     self.conn_audit.close()
            #     print("Connexion SQLite (Audit) fermée.")
            if hasattr(self, 'conn_compteurs'):
                self.conn_compteurs.close()
                print("Connexion SQLite (Compteurs) fermée.")
            if hasattr(self, 'conn_tasks'):
                self.conn_tasks.close()
                print("Connexion SQLite (Tâches) fermée.")
            if hasattr(self, 'conn_library'):
                self.conn_library.close()
                print("Connexion SQLite (Bibliothèque) fermée.")
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    show_dependencies_ok_window()
    app = ArchivisteApp(root)
    root.mainloop()
