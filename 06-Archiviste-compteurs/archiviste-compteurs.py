import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import subprocess
import importlib.util
import configparser
import shutil
from datetime import datetime

# Liste des dépendances nécessaires
DEPENDENCIES = {
    "matplotlib": "matplotlib",
    "numpy": "numpy",
    "dateutil": "python-dateutil"
}

def check_and_install_dependencies():
    missing = []
    for module_name, package_name in DEPENDENCIES.items():
        if importlib.util.find_spec(module_name) is None:
            missing.append(package_name)
    try:
        import tkinter
    except ImportError:
        messagebox.showerror("Erreur", "Le module tkinter est manquant. Sur Linux, installez-le avec votre gestionnaire de paquets (ex. 'sudo apt install python3-tk' sur Debian/Ubuntu).")
        sys.exit(1)
    if missing:
        response = messagebox.askyesno(
            "Dépendances manquantes",
            f"Les modules suivants sont manquants : {', '.join(missing)}.\nVoulez-vous les installer automatiquement ?"
        )
        if response:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
                for package in missing:
                    print(f"Installation de {package}...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                messagebox.showinfo("Succès", "Les dépendances ont été installées avec succès.")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Erreur", f"Échec de l'installation des dépendances : {e}\nVeuillez les installer manuellement avec 'pip install {' '.join(missing)}'.")
                sys.exit(1)
        else:
            messagebox.showerror("Erreur", f"Les dépendances suivantes sont requises : {', '.join(missing)}. Installez-les manuellement avec 'pip install {' '.join(missing)}'.")
            sys.exit(1)
    return len(missing) == 0

def show_dependencies_ok_window():
    config_path = os.path.join(os.path.dirname(__file__), "config.ini")
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

def auto_backup_db(db_path):
    backup_dir = os.path.join(os.path.dirname(__file__), "backup_db")
    os.makedirs(backup_dir, exist_ok=True)
    current_date = datetime.now()
    backup_filename = f"{current_date.strftime('%Y-%m')}-meters.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    if not os.path.exists(backup_path):
        try:
            shutil.copy2(db_path, backup_path)
            print(f"Sauvegarde automatique effectuée : {backup_path}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde automatique : {e}")
    backups = sorted([f for f in os.listdir(backup_dir) if f.endswith("-meters.db")])
    if len(backups) > 12:
        for old_backup in backups[:-12]:
            try:
                os.remove(os.path.join(backup_dir, old_backup))
                print(f"Sauvegarde ancienne supprimée : {old_backup}")
            except Exception as e:
                print(f"Erreur lors de la suppression de {old_backup} : {e}")

from scripts.db_designer import DBDesigner
from scripts.meter_readings import MeterReadings
from scripts.meter_reports import MeterReports
from scripts.db_manager import DBManager
from scripts.meter_graphs import MeterGraphs
import sqlite3

class ArchivisteCompteurs:
    def __init__(self, root):
        self.root = root
        self.root.title("Archiviste Compteurs")

        style = ttk.Style()
        style.theme_use("clam")

        self.db_path = os.path.join(os.path.dirname(__file__), "db", "meters.db")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.isolation_level = None

        auto_backup_db(self.db_path)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Onglet 1 : Relevés
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="Relevés")
        self.meter_readings = MeterReadings(self.tab2, self.conn)

        # Onglet 2 : Rapports
        self.tab3 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab3, text="Rapports")
        # Crée l'instance de MeterGraphs ici pour la passer à MeterReports
        self.tab5 = ttk.Frame(self.notebook)
        self.meter_graphs = MeterGraphs(self.tab5)
        self.meter_reports = MeterReports(self.tab3, self.conn, self.meter_graphs)

        # Onglet 3 : Graphiques
        self.notebook.add(self.tab5, text="Graphiques")

        # Onglet 4 : Gestion Compteurs
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Gestion Compteurs")
        self.db_designer = DBDesigner(self.tab1, self.conn)

        # Onglet 5 : Gestion Base de Données
        self.tab4 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab4, text="Gestion Base de Données")
        self.db_manager = DBManager(self.tab4, self.conn, self.db_path)
        self.db_manager.import_backup = lambda: self.update_connection_after_import()

    def update_connection_after_import(self):
        self.conn.close()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.isolation_level = None
        self.db_designer.conn = self.conn
        self.db_designer.cursor = self.conn.cursor()
        self.db_designer.update_ui()
        self.meter_readings.conn = self.conn
        self.meter_readings.cursor = self.conn.cursor()
        self.meter_readings.load_meters_to_tree()
        self.meter_reports.conn = self.conn
        self.meter_reports.cursor = self.conn.cursor()
        self.meter_reports.compare_periods()
        self.meter_graphs.conn = self.conn
        self.meter_graphs.cursor = self.conn.cursor()

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    dependencies_ok = check_and_install_dependencies()
    if dependencies_ok:
        root = tk.Tk()
        show_dependencies_ok_window()
        app = ArchivisteCompteurs(root)
        root.mainloop()