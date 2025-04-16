import os
import sys
import importlib.util
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import json
import configparser
import shutil

# Ajouter le répertoire racine du projet au sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Gérer les chemins pour PyInstaller
def resource_path(relative_path):
    """Retourne le chemin absolu pour les fichiers inclus dans l'exécutable PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # Chemin temporaire où PyInstaller extrait les fichiers
        base_path = sys._MEIPASS
    else:
        # Chemin normal lors de l'exécution du script Python
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# Chemin pour les fichiers de données (bases de données, sauvegardes, config.json)
# Ces fichiers doivent être dans le répertoire de l'exécutable
DATA_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))

DEPENDENCIES = {
    "matplotlib": "matplotlib",
    "numpy": "numpy",
    "dateutil": "python-dateutil"
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

# Imports mis à jour avec les nouveaux noms
from scripts_releves.db_designer_releves import DBDesigner as AuditDBDesigner
from scripts_releves.meter_readings_releves import MeterReadings as AuditMeterReadings
from scripts_releves.meter_reports_releves import MeterReports as AuditMeterReports
from scripts_releves.meter_graphs_releves import MeterGraphs as AuditMeterGraphs

from scripts_compteurs.db_designer_compteur import DBDesigner as CompteursDBDesigner
from scripts_compteurs.meter_readings_compteur import MeterReadings as CompteursMeterReadings
from scripts_compteurs.meter_reports_compteur import MeterReports as CompteursMeterReports
from scripts_compteurs.meter_graphs_compteur import MeterGraphs as CompteursMeterGraphs

from scripts_releves.db_manager import DBManager

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

def auto_backup_db(db_path, backup_dir_name="backup_db"):
    backup_dir = os.path.join(DATA_DIR, backup_dir_name)
    os.makedirs(backup_dir, exist_ok=True)
    current_date = datetime.now()
    backup_filename = f"{current_date.strftime('%Y-%m')}-{os.path.basename(db_path)}"
    backup_path = os.path.join(backup_dir, backup_filename)
    if not os.path.exists(backup_path):
        try:
            shutil.copy2(db_path, backup_path)
            print(f"Sauvegarde effectuée : {backup_path}")
        except Exception as e:
            print(f"Erreur sauvegarde : {e}")
    backups = sorted([f for f in os.listdir(backup_dir) if f.endswith(f"-{os.path.basename(db_path)}")])
    if len(backups) > 12:
        for old_backup in backups[:-12]:
            try:
                os.remove(os.path.join(backup_dir, old_backup))
                print(f"Ancienne sauvegarde supprimée : {old_backup}")
            except Exception as e:
                print(f"Erreur suppression : {e}")

class CustomNotebook:
    def __init__(self, parent):
        self.parent = parent
        self.tabs = []
        self.frames = []
        self.current_tab = None

        # Frame pour les onglets (boutons)
        self.tab_frame = tk.Frame(parent, bg="#D3D3D3")
        self.tab_frame.pack(fill="x")

        # Frame pour le contenu des onglets
        self.content_frame = tk.Frame(parent)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def add(self, frame, text, bg_color, fg_color):
        # Créer un bouton pour l'onglet
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

        # Cacher le frame par défaut
        frame.pack_forget()

        # Sélectionner le premier onglet par défaut
        if not self.current_tab:
            self.select_tab(frame)

    def select_tab(self, frame):
        if self.current_tab:
            self.current_tab.pack_forget()
        self.current_tab = frame
        self.current_tab.pack(fill="both", expand=True)

        # Mettre à jour l'apparence des boutons
        for btn, frm in zip(self.tabs, self.frames):
            if frm == frame:
                btn.config(relief="sunken")
            else:
                btn.config(relief="raised")

class ArchivisteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Archiviste")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Charger ou définir l’emplacement des dossiers db
        self.config_file = os.path.join(DATA_DIR, "config.json")
        self.db_dir_audit = self.load_db_dir("audit")
        self.db_dir_compteurs = self.load_db_dir("compteurs")

        # Demander à l'utilisateur de sélectionner ou confirmer l’emplacement des dossiers db
        self.db_dir_audit = self.select_db_dir("Audit", self.db_dir_audit)
        if not self.db_dir_audit:
            messagebox.showerror("Erreur", "Aucun dossier de base de données pour Audit sélectionné. L'application va se fermer.")
            self.root.destroy()
            return
        os.makedirs(self.db_dir_audit, exist_ok=True)
        self.save_db_dir("audit", self.db_dir_audit)

        self.db_dir_compteurs = self.select_db_dir("Compteurs", self.db_dir_compteurs)
        if not self.db_dir_compteurs:
            messagebox.showerror("Erreur", "Aucun dossier de base de données pour Compteurs sélectionné. L'application va se fermer.")
            self.root.destroy()
            return
        os.makedirs(self.db_dir_compteurs, exist_ok=True)
        self.save_db_dir("compteurs", self.db_dir_compteurs)

        # Demander à l'utilisateur de sélectionner une base de données pour Audit
        self.db_path_audit = self.select_db("Audit", self.db_dir_audit, "audit.db")
        if not self.db_path_audit:
            messagebox.showerror("Erreur", "Aucune base de données pour Audit sélectionnée. L'application va se fermer.")
            self.root.destroy()
            return

        # Demander à l'utilisateur de sélectionner une base de données pour Compteurs
        self.db_path_compteurs = self.select_db("Compteurs", self.db_dir_compteurs, "meters.db")
        if not self.db_path_compteurs:
            messagebox.showerror("Erreur", "Aucune base de données pour Compteurs sélectionnée. L'application va se fermer.")
            self.root.destroy()
            return

        # Initialisation des connexions
        self.conn_audit = sqlite3.connect(self.db_path_audit, check_same_thread=False)
        self.conn_audit.isolation_level = None
        self.create_tables_audit(self.conn_audit.cursor())
        self.conn_audit.commit()

        self.conn_compteurs = sqlite3.connect(self.db_path_compteurs, check_same_thread=False)
        self.conn_compteurs.isolation_level = None
        self.create_tables_compteurs(self.conn_compteurs.cursor())
        self.conn_compteurs.commit()

        # Sauvegarde automatique des bases
        auto_backup_db(self.db_path_audit, "backup_db_audit")
        auto_backup_db(self.db_path_compteurs, "backup_db_compteurs")

        # Créer le Notebook personnalisé
        self.notebook = CustomNotebook(self.root)

        # Création des onglets dans l'ordre demandé
        # 1. Relevés techniques (Audit) - Bleu clair
        self.tab2_audit = tk.Frame(self.notebook.content_frame)
        self.notebook.add(self.tab2_audit, text="Relevés techniques", bg_color="#ADD8E6", fg_color="black")
        
        # 2. Compteurs (Compteurs) - Jaune clair
        self.tab2_compteurs = tk.Frame(self.notebook.content_frame)
        self.notebook.add(self.tab2_compteurs, text="Compteurs", bg_color="#FFFFE0", fg_color="black")
        
        # 3. Synthèse relevés (Audit) - Bleu clair
        self.tab3_audit = tk.Frame(self.notebook.content_frame)
        self.notebook.add(self.tab3_audit, text="Synthèse relevés", bg_color="#ADD8E6", fg_color="black")
        
        # 4. Graphique relevés (Audit) - Bleu clair
        self.tab4_audit = tk.Frame(self.notebook.content_frame)
        self.notebook.add(self.tab4_audit, text="Graphique relevés", bg_color="#ADD8E6", fg_color="black")
        
        # 5. Synthèse compteurs (Compteurs) - Jaune clair
        self.tab3_compteurs = tk.Frame(self.notebook.content_frame)
        self.notebook.add(self.tab3_compteurs, text="Synthèse compteurs", bg_color="#FFFFE0", fg_color="black")
        
        # 6. Graphique compteurs (Compteurs) - Jaune clair
        self.tab4_compteurs = tk.Frame(self.notebook.content_frame)
        self.notebook.add(self.tab4_compteurs, text="Graphique compteurs", bg_color="#FFFFE0", fg_color="black")
        
        # 7. Gestion relevés (Audit) - Bleu foncé, texte blanc
        self.tab1_audit = tk.Frame(self.notebook.content_frame)
        self.notebook.add(self.tab1_audit, text="Gestion relevés", bg_color="#4682B4", fg_color="white")
        
        # 8. Gestion compteurs (Compteurs) - Jaune foncé
        self.tab1_compteurs = tk.Frame(self.notebook.content_frame)
        self.notebook.add(self.tab1_compteurs, text="Gestion compteurs", bg_color="#FFD700", fg_color="black")
        
        # 9. Sauvegardes - Noir, texte blanc
        self.tab_db_manager = tk.Frame(self.notebook.content_frame)
        self.notebook.add(self.tab_db_manager, text="Sauvegardes", bg_color="#000000", fg_color="white")

        # Initialisation des modules pour Audit
        self.db_designer_audit = AuditDBDesigner(self.tab1_audit, self.conn_audit)
        self.meter_readings_audit = AuditMeterReadings(self.tab2_audit, self.conn_audit)
        self.meter_graphs_audit = AuditMeterGraphs(self.tab4_audit)
        self.meter_reports_audit = AuditMeterReports(self.tab3_audit, self.conn_audit, self.meter_graphs_audit)

        # Initialisation des modules pour Compteurs
        self.db_designer_compteurs = CompteursDBDesigner(self.tab1_compteurs, self.conn_compteurs)
        self.meter_readings_compteurs = CompteursMeterReadings(self.tab2_compteurs, self.conn_compteurs)
        self.meter_graphs_compteurs = CompteursMeterGraphs(self.tab4_compteurs)
        self.meter_reports_compteurs = CompteursMeterReports(self.tab3_compteurs, self.conn_compteurs, self.meter_graphs_compteurs)

        # Initialisation du gestionnaire de bases de données
        self.db_manager = DBManager(self.tab_db_manager, self.conn_audit, self.db_path_audit, self.conn_compteurs, self.db_path_compteurs, self.update_connection_after_import)

        # Mettre à jour les connexions pour les modules
        self.update_connection_after_import(self.conn_audit, self.conn_compteurs)

        # Charger les listes déroulantes après l'initialisation
        self.meter_graphs_audit.update_meters_to_combobox()

    def load_db_dir(self, section):
        """Charge l’emplacement du dossier db depuis le fichier de configuration."""
        default_dir = os.path.join(DATA_DIR, f"db-{section}")
        if not os.path.exists(self.config_file):
            return default_dir
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)
            return config.get(f"db_dir_{section}", default_dir)
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration pour {section} : {e}")
            return default_dir

    def save_db_dir(self, section, db_dir):
        """Sauvegarde l’emplacement du dossier db dans le fichier de configuration."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
            else:
                config = {}
            config[f"db_dir_{section}"] = db_dir
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration pour {section} : {e}")

    def select_db_dir(self, section, default_dir):
        """Demande à l'utilisateur de sélectionner ou confirmer l’emplacement du dossier db."""
        if messagebox.askyesno(f"Emplacement des bases de données ({section})", f"Voulez-vous utiliser cet emplacement pour les bases de données ({section}) ?\n{default_dir}\n\n(Si non, vous pourrez choisir un autre dossier)"):
            return default_dir
        return filedialog.askdirectory(
            title=f"Sélectionner l’emplacement des bases de données ({section})",
            initialdir=default_dir
        )

    def select_db(self, section, db_dir, default_db_name):
        """Demande à l'utilisateur de sélectionner une base de données, ou en crée une vierge si nécessaire."""
        db_files = [f for f in os.listdir(db_dir) if f.endswith(".db")]
        
        if not db_files:
            if messagebox.askyesno(
                f"Aucune base de données trouvée ({section})",
                f"Aucun fichier .db n’a été trouvé dans le dossier {db_dir}.\nVoulez-vous créer une nouvelle base vierge ({default_db_name}) ?"
            ):
                default_db_path = os.path.join(db_dir, default_db_name)
                temp_conn = sqlite3.connect(default_db_path)
                temp_cursor = temp_conn.cursor()
                if section == "Audit":
                    self.create_tables_audit(temp_cursor)
                else:
                    self.create_tables_compteurs(temp_cursor)
                temp_conn.commit()
                temp_conn.close()
                return default_db_path
            else:
                messagebox.showinfo("Information", "Veuillez sélectionner une base de données existante ou choisir un autre dossier.")
        
        file_path = filedialog.askopenfilename(
            filetypes=[("SQLite Database", "*.db")],
            title=f"Sélectionner une base de données ({section})",
            initialdir=db_dir
        )
        return file_path

    def create_tables_audit(self, cursor):
        """Crée les tables nécessaires pour Audit si elles n'existent pas."""
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
        """Crée les tables nécessaires pour Compteurs si elles n'existent pas."""
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

    def update_connection_after_import(self, conn_audit, conn_compteurs):
        self.conn_audit = conn_audit
        self.conn_compteurs = conn_compteurs
        # Mise à jour des modules Audit
        self.db_designer_audit.conn = self.conn_audit
        self.db_designer_audit.cursor = self.conn_audit.cursor()
        self.db_designer_audit.update_ui()
        self.meter_readings_audit.conn = self.conn_audit
        self.meter_readings_audit.cursor = self.conn_audit.cursor()
        self.meter_readings_audit.load_meters_to_tree()
        self.meter_reports_audit.conn = self.conn_audit
        self.meter_reports_audit.cursor = self.conn_audit.cursor()
        self.meter_graphs_audit.conn = self.conn_audit
        self.meter_graphs_audit.cursor = self.conn_audit.cursor()
        # Mise à jour des modules Compteurs
        self.db_designer_compteurs.conn = self.conn_compteurs
        self.db_designer_compteurs.cursor = self.conn_compteurs.cursor()
        self.db_designer_compteurs.update_ui()
        self.meter_readings_compteurs.conn = self.conn_compteurs
        self.meter_readings_compteurs.cursor = self.conn_compteurs.cursor()
        self.meter_readings_compteurs.load_meters_to_tree()
        self.meter_reports_compteurs.conn = self.conn_compteurs
        self.meter_reports_compteurs.cursor = self.conn_compteurs.cursor()
        self.meter_graphs_compteurs.conn = self.conn_compteurs
        self.meter_graphs_compteurs.cursor = self.conn_compteurs.cursor()

    def on_closing(self):
        if hasattr(self, 'conn_audit'):
            self.conn_audit.close()
            print("Connexion SQLite (Audit) fermée.")
        if hasattr(self, 'conn_compteurs'):
            self.conn_compteurs.close()
            print("Connexion SQLite (Compteurs) fermée.")
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    show_dependencies_ok_window()
    app = ArchivisteApp(root)
    root.mainloop()