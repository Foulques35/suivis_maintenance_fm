import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
import shutil
import subprocess
import platform
import sys
import json
from datetime import datetime

class LibraryManager:
    def __init__(self, parent, conn):
        self.parent = parent
        self.conn = conn
        self.cursor = conn.cursor()
        self.init_db()

        # Dossier pour stocker les fichiers à la racine du projet
        self.files_dir = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "bibliotheque"))
        try:
            os.makedirs(self.files_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de créer le dossier 'bibliotheque' : {e}")

        # Chemin pour les fichiers des nomenclatures et des sites
        self.nomenclatures_file = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "nomenclatures.json"))
        self.sites_file = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "sites.json"))
        self.init_nomenclatures_file()
        self.init_sites_file()

        # Nettoyer les chemins dans la base de données
        self.clean_file_paths()

        # Variables pour les filtres du Treeview 1
        self.year_filter_var = tk.StringVar()
        self.category_filter_var = tk.StringVar()
        self.archives_filter_var = tk.StringVar()
        self.project_filter_var = tk.StringVar()

        # Variables pour le tri
        self.sort_column_name = "Year"
        self.sort_reverse = False
        self.sort_direction = {"Year": False, "Category": False, "Archives": False, "Project": False, "Notes": False}

        # Stocker toutes les données des dossiers et fichiers
        self.all_folders = []
        self.all_files = []  # New: Store file metadata (id, title, year, category, archives, project)

        # Charger les données initiales
        self.load_initial_data()

        # Configurer les styles pour les boutons
        style = ttk.Style()
        style.configure("Add.TButton", background="#90EE90", foreground="black")  # Vert clair
        style.configure("Modify.TButton", background="#FFFFE0", foreground="black")  # Jaune clair
        style.configure("Clear.TButton", background="#ADD8E6", foreground="black")  # Bleu clair
        style.configure("Delete.TButton", background="#FF0000", foreground="#FFFFFF")  # Rouge, texte blanc

        # Configurer les styles pour les lignes alternées
        style.configure("OddRow.Treeview", background="#F5F5F5")
        style.configure("EvenRow.Treeview", background="#FFFFFF")

        # Interface principale avec PanedWindow
        self.paned_window = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True, padx=10, pady=10)

        # Gauche : Treeview 1 (Année, Catégorie, Archives, Projet, Notes) avec filtres
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=3)  # Augmenter la taille du Treeview

        # Filtres pour Treeview 1
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(filter_frame, text="Filtrer Année :").pack(side="left")
        ttk.Entry(filter_frame, textvariable=self.year_filter_var, width=10).pack(side="left", padx=5)
        ttk.Label(filter_frame, text="Catégorie :").pack(side="left")
        ttk.Entry(filter_frame, textvariable=self.category_filter_var, width=15).pack(side="left", padx=5)
        ttk.Label(filter_frame, text="Archives :").pack(side="left")
        ttk.Entry(filter_frame, textvariable=self.archives_filter_var, width=15).pack(side="left", padx=5)
        ttk.Label(filter_frame, text="Projet :").pack(side="left")
        ttk.Entry(filter_frame, textvariable=self.project_filter_var, width=20).pack(side="left", padx=5)
        self.year_filter_var.trace("w", self.filter_folders)
        self.category_filter_var.trace("w", self.filter_folders)
        self.archives_filter_var.trace("w", self.filter_folders)
        self.project_filter_var.trace("w", self.filter_folders)

        self.folder_tree = ttk.Treeview(left_frame, columns=("Year", "Category", "Archives", "Project", "Notes"), show="headings")
        self.folder_tree.heading("Year", text="Année", command=lambda: self.sort_column("Year", self.sort_direction["Year"]))
        self.folder_tree.heading("Category", text="Catégorie", command=lambda: self.sort_column("Category", self.sort_direction["Category"]))
        self.folder_tree.heading("Archives", text="Archives", command=lambda: self.sort_column("Archives", self.sort_direction["Archives"]))
        self.folder_tree.heading("Project", text="Projet", command=lambda: self.sort_column("Project", self.sort_direction["Project"]))
        self.folder_tree.heading("Notes", text="Notes", command=lambda: self.sort_column("Notes", self.sort_direction["Notes"]))
        self.folder_tree.column("Year", width=100)
        self.folder_tree.column("Category", width=150)
        self.folder_tree.column("Archives", width=150)
        self.folder_tree.column("Project", width=200)
        self.folder_tree.column("Notes", width=200)
        self.folder_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.folder_tree.bind("<<TreeviewSelect>>", self.load_folder_to_form)

        # Droite : Formulaires et Treeview 2
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=1)  # Réduire la taille du formulaire

        # Formulaire 1 : Année, Catégorie, Archives, Projet, Notes
        folder_form_frame = ttk.LabelFrame(right_frame, text="Gestion des dossiers")
        folder_form_frame.pack(fill="x", pady=5)

        # Grille pour un formulaire ordonné
        ttk.Label(folder_form_frame, text="Année :").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.folder_year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Entry(folder_form_frame, textvariable=self.folder_year_var, width=10).grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(folder_form_frame, text="Catégorie :").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.folder_category_var = tk.StringVar()
        ttk.Entry(folder_form_frame, textvariable=self.folder_category_var, width=20).grid(row=1, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(folder_form_frame, text="Archives :").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.folder_archives_var = tk.StringVar()
        ttk.Entry(folder_form_frame, textvariable=self.folder_archives_var, width=20).grid(row=2, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(folder_form_frame, text="Projet :").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.folder_project_var = tk.StringVar()
        ttk.Entry(folder_form_frame, textvariable=self.folder_project_var, width=20).grid(row=3, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(folder_form_frame, text="Notes :").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.folder_notes_var = tk.StringVar()
        ttk.Entry(folder_form_frame, textvariable=self.folder_notes_var, width=50).grid(row=4, column=1, padx=5, pady=2, sticky="w")

        folder_button_frame = ttk.Frame(folder_form_frame)
        folder_button_frame.grid(row=5, column=0, columnspan=2, pady=5)
        ttk.Button(folder_button_frame, text="Ajouter dossier", style="Add.TButton", command=self.add_folder).pack(side="left", padx=5)
        ttk.Button(folder_button_frame, text="Modifier dossier", style="Modify.TButton", command=self.modify_folder).pack(side="left", padx=5)
        ttk.Button(folder_button_frame, text="Vider formulaire", style="Clear.TButton", command=self.clear_folder_form).pack(side="left", padx=5)
        ttk.Button(folder_button_frame, text="Supprimer dossier", style="Delete.TButton", command=self.delete_folder).pack(side="left", padx=5)
        ttk.Button(folder_button_frame, text="Supprimer catégorie", style="Delete.TButton", command=self.delete_category).pack(side="left", padx=5)

        # Formulaire 2 : Pièces
        file_form_frame = ttk.LabelFrame(right_frame, text="Gestion des pièces")
        file_form_frame.pack(fill="x", pady=5)

        # Case à cocher pour conserver le nom du fichier
        self.keep_name_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(file_form_frame, text="Conserver le nom du fichier", variable=self.keep_name_var, command=self.toggle_file_fields).grid(row=0, column=0, columnspan=2, pady=2, sticky="w")

        # Case à cocher pour couper/copier
        self.move_file_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(file_form_frame, text="Couper (déplacer) / Copier", variable=self.move_file_var).grid(row=1, column=0, columnspan=2, pady=2, sticky="w")

        ttk.Label(file_form_frame, text="Site :").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.site_var = tk.StringVar()
        self.site_entry = ttk.Entry(file_form_frame, textvariable=self.site_var, width=15)
        self.site_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        ttk.Button(file_form_frame, text="?", command=self.show_sites).grid(row=2, column=2, padx=2, pady=2)

        ttk.Label(file_form_frame, text="Nomenclature :").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.nomenclature_var = tk.StringVar()
        self.nomenclature_entry = ttk.Entry(file_form_frame, textvariable=self.nomenclature_var, width=10)
        self.nomenclature_entry.grid(row=3, column=1, padx=5, pady=2, sticky="w")
        ttk.Button(file_form_frame, text="?", command=self.show_nomenclatures).grid(row=3, column=2, padx=2, pady=2)

        ttk.Label(file_form_frame, text="Émetteur :").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.emetteur_var = tk.StringVar()
        self.emetteur_entry = ttk.Entry(file_form_frame, textvariable=self.emetteur_var, width=15)
        self.emetteur_entry.grid(row=4, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(file_form_frame, text="Objet :").grid(row=5, column=0, padx=5, pady=2, sticky="w")
        self.objet_var = tk.StringVar()
        self.objet_entry = ttk.Entry(file_form_frame, textvariable=self.objet_var, width=20)
        self.objet_entry.grid(row=5, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(file_form_frame, text="Version :").grid(row=6, column=0, padx=5, pady=2, sticky="w")
        self.version_var = tk.StringVar(value="V1")
        self.version_entry = ttk.Entry(file_form_frame, textvariable=self.version_var, width=10)
        self.version_entry.grid(row=6, column=1, padx=5, pady=2, sticky="w")

        file_button_frame = ttk.Frame(file_form_frame)
        file_button_frame.grid(row=7, column=0, columnspan=3, pady=5)
        ttk.Button(file_button_frame, text="Ajouter pièce", style="Add.TButton", command=self.add_file).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Modifier pièce", style="Modify.TButton", command=self.modify_file).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Vider formulaire", style="Clear.TButton", command=self.clear_file_form).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Supprimer pièce", style="Delete.TButton", command=self.delete_file).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Ouvrir pièce", style="Add.TButton", command=self.open_file).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Ouvrir l'emplacement", style="Add.TButton", command=self.open_file_explorer).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Vérifier chemins", style="Modify.TButton", command=self.verify_and_fix_file_paths).pack(side="left", padx=5)

        # Recherche pour le Treeview 2
        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill="x", pady=5)
        ttk.Label(search_frame, text="Rechercher pièces :").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_files)

        # Treeview 2 : Liste des pièces (seulement ID et Titre)
        self.file_tree = ttk.Treeview(right_frame, columns=("ID", "Title"), show="headings")
        self.file_tree.heading("ID", text="ID")
        self.file_tree.heading("Title", text="Titre")
        self.file_tree.column("ID", width=50)
        self.file_tree.column("Title", width=450)
        self.file_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.file_tree.bind("<<TreeviewSelect>>", self.load_file_to_form)

        self.current_file_id = None
        self.current_folder = None
        self.current_selected_folder = None
        self.toggle_file_fields()  # Initialiser l'état des champs
        self.refresh_folder_list()

    def load_initial_data(self):
        """Charge les dossiers et fichiers initiaux depuis la base de données dans les structures en mémoire."""
        # Charger les dossiers
        self.cursor.execute("SELECT DISTINCT year, category, archives, project, notes FROM library WHERE file_path != '' OR title = '[Dossier]'")
        self.all_folders = [(row[0], row[1], row[2] or "", row[3], row[4] or "") for row in self.cursor.fetchall()]
        print(f"Loaded {len(self.all_folders)} folders into self.all_folders")

        # Charger les fichiers
        self.cursor.execute("SELECT id, title, year, category, archives, project FROM library WHERE file_path != ''")
        self.all_files = [(row[0], row[1], row[2], row[3], row[4] or "", row[5]) for row in self.cursor.fetchall()]
        print(f"Loaded {len(self.all_files)} files into self.all_files")

    def init_nomenclatures_file(self):
        if not os.path.exists(self.nomenclatures_file):
            default_nomenclatures = [
                {"code": "DOC", "description": "Document général"},
                {"code": "PLAN", "description": "Plan technique"},
                {"code": "CTR", "description": "Contrat"}
            ]
            try:
                with open(self.nomenclatures_file, "w", encoding="utf-8") as f:
                    json.dump(default_nomenclatures, f, indent=4)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de créer nomenclatures.json : {e}")

    def init_sites_file(self):
        if not os.path.exists(self.sites_file):
            default_sites = [
                {"code": "ALMA", "description": "Site Alma"},
                {"code": "PARIS", "description": "Site Paris"},
                {"code": "LYON", "description": "Site Lyon"}
            ]
            try:
                with open(self.sites_file, "w", encoding="utf-8") as f:
                    json.dump(default_sites, f, indent=4)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de créer sites.json : {e}")

    def show_nomenclatures(self):
        nomenclatures_window = tk.Toplevel(self.parent)
        nomenclatures_window.title("Liste des nomenclatures")
        nomenclatures_window.geometry("400x300")
        nomenclatures_window.transient(self.parent)
        nomenclatures_window.grab_set()

        try:
            with open(self.nomenclatures_file, "r", encoding="utf-8") as f:
                nomenclatures = json.load(f)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les nomenclatures : {e}")
            nomenclatures_window.destroy()
            return

        search_frame = ttk.Frame(nomenclatures_window)
        search_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(search_frame, text="Rechercher :").pack(side="left")
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=5)

        tree = ttk.Treeview(nomenclatures_window, columns=("Code", "Description"), show="headings")
        tree.heading("Code", text="Code")
        tree.heading("Description", text="Description")
        tree.column("Code", width=100)
        tree.column("Description", width=250)
        tree.pack(fill="both", expand=True, padx=5, pady=5)

        def filter_nomenclatures(*args):
            search_term = search_var.get().lower()
            for item in tree.get_children():
                tree.delete(item)
            for nomenclature in nomenclatures:
                if search_term in nomenclature["code"].lower() or search_term in nomenclature["description"].lower():
                    tree.insert("", tk.END, values=(nomenclature["code"], nomenclature["description"]))

        for nomenclature in nomenclatures:
            tree.insert("", tk.END, values=(nomenclature["code"], nomenclature["description"]))

        search_var.trace("w", filter_nomenclatures)

        def apply_nomenclature():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Erreur", "Veuillez sélectionner une nomenclature.")
                return
            code = tree.item(selected[0])["values"][0]
            self.nomenclature_var.set(code)
            nomenclatures_window.destroy()

        ttk.Button(nomenclatures_window, text="Appliquer", command=apply_nomenclature).pack(pady=5)
        ttk.Button(nomenclatures_window, text="Fermer", command=nomenclatures_window.destroy).pack(pady=5)

        nomenclatures_window.update_idletasks()
        width = nomenclatures_window.winfo_width()
        height = nomenclatures_window.winfo_height()
        x = (nomenclatures_window.winfo_screenwidth() // 2) - (width // 2)
        y = (nomenclatures_window.winfo_screenheight() // 2) - (height // 2)
        nomenclatures_window.geometry(f"{width}x{height}+{x}+{y}")

    def show_sites(self):
        sites_window = tk.Toplevel(self.parent)
        sites_window.title("Liste des sites")
        sites_window.geometry("400x300")
        sites_window.transient(self.parent)
        sites_window.grab_set()

        try:
            with open(self.sites_file, "r", encoding="utf-8") as f:
                sites = json.load(f)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les sites : {e}")
            sites_window.destroy()
            return

        search_frame = ttk.Frame(sites_window)
        search_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(search_frame, text="Rechercher :").pack(side="left")
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=5)

        tree = ttk.Treeview(sites_window, columns=("Code", "Description"), show="headings")
        tree.heading("Code", text="Code")
        tree.heading("Description", text="Description")
        tree.column("Code", width=100)
        tree.column("Description", width=250)
        tree.pack(fill="both", expand=True, padx=5, pady=5)

        def filter_sites(*args):
            search_term = search_var.get().lower()
            for item in tree.get_children():
                tree.delete(item)
            for site in sites:
                if search_term in site["code"].lower() or search_term in site["description"].lower():
                    tree.insert("", tk.END, values=(site["code"], site["description"]))

        for site in sites:
            tree.insert("", tk.END, values=(site["code"], site["description"]))

        search_var.trace("w", filter_sites)

        def apply_site():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Erreur", "Veuillez sélectionner un site.")
                return
            code = tree.item(selected[0])["values"][0]
            self.site_var.set(code)
            sites_window.destroy()

        ttk.Button(sites_window, text="Appliquer", command=apply_site).pack(pady=5)
        ttk.Button(sites_window, text="Fermer", command=sites_window.destroy).pack(pady=5)

        sites_window.update_idletasks()
        width = sites_window.winfo_width()
        height = sites_window.winfo_height()
        x = (sites_window.winfo_screenwidth() // 2) - (width // 2)
        y = (sites_window.winfo_screenheight() // 2) - (height // 2)
        sites_window.geometry(f"{width}x{height}+{x}+{y}")

    def init_db(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS library (
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
        self.cursor.execute("PRAGMA table_info(library)")
        columns = [info[1] for info in self.cursor.fetchall()]
        if 'year' not in columns:
            self.cursor.execute("ALTER TABLE library ADD COLUMN year TEXT")
            self.cursor.execute("UPDATE library SET year = ? WHERE year IS NULL", (str(datetime.now().year),))
        if 'category' not in columns:
            self.cursor.execute("ALTER TABLE library ADD COLUMN category TEXT")
        if 'archives' not in columns:
            self.cursor.execute("ALTER TABLE library ADD COLUMN archives TEXT")
        if 'project' not in columns:
            self.cursor.execute("ALTER TABLE library ADD COLUMN project TEXT")
        if 'site' not in columns:
            self.cursor.execute("ALTER TABLE library ADD COLUMN site TEXT")
        if 'nomenclature' not in columns:
            self.cursor.execute("ALTER TABLE library ADD COLUMN nomenclature TEXT")
        if 'emetteur' not in columns:
            self.cursor.execute("ALTER TABLE library ADD COLUMN emetteur TEXT")
        if 'objet' not in columns:
            self.cursor.execute("ALTER TABLE library ADD COLUMN objet TEXT")
        if 'version' not in columns:
            self.cursor.execute("ALTER TABLE library ADD COLUMN version TEXT")
        if 'file_path' not in columns:
            self.cursor.execute("ALTER TABLE library ADD COLUMN file_path TEXT")
        if 'notes' not in columns:
            self.cursor.execute("ALTER TABLE library ADD COLUMN notes TEXT")
        self.conn.commit()
        # Migrer les chemins après l'initialisation du schéma
        self.migrate_file_paths()

    def migrate_file_paths(self):
        """Migre les chemins des fichiers existants vers la nouvelle structure."""
        self.cursor.execute("SELECT id, year, category, archives, project, title, file_path FROM library WHERE file_path != ''")
        files = self.cursor.fetchall()
        for file_id, year, category, archives, project, title, file_path in files:
            # Chemin attendu : year/category/[archives/]project/title
            path_components = [str(year), category]
            if archives:
                path_components.append(archives)
            path_components.append(project)
            path_components.append(title)
            expected_path = os.path.join(*path_components)
            expected_path = expected_path.replace('\\', '/')
            
            # Si le chemin actuel diffère, mettre à jour
            if file_path != expected_path:
                print(f"Migration du chemin pour l'ID {file_id} : {file_path} -> {expected_path}")
                self.cursor.execute("UPDATE library SET file_path = ? WHERE id = ?", (expected_path, file_id))
                # Vérifier si le fichier existe et le déplacer si nécessaire
                old_full_path = os.path.normpath(os.path.join(self.files_dir, file_path))
                new_full_path = os.path.normpath(os.path.join(self.files_dir, expected_path))
                if os.path.exists(old_full_path) and not os.path.exists(new_full_path):
                    try:
                        os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
                        shutil.move(old_full_path, new_full_path)
                    except Exception as e:
                        print(f"Erreur lors du déplacement du fichier pour l'ID {file_id} : {e}")
        self.conn.commit()

    def clean_file_paths(self):
        """Nettoie les chemins dans la base de données en supprimant les redondances."""
        self.cursor.execute("SELECT id, year, category, archives, project, title, file_path FROM library WHERE file_path != ''")
        files = self.cursor.fetchall()
        for file_id, year, category, archives, project, title, file_path in files:
            # Construire le chemin attendu : year/category/[archives/]project/title
            path_components = [str(year), category]
            if archives:
                path_components.append(archives)
            path_components.append(project)
            path_components.append(title)
            expected_path = os.path.join(*path_components)
            expected_path = expected_path.replace('\\', '/')

            # Vérifier si le chemin stocké contient une redondance
            if file_path != expected_path:
                print(f"Chemin incorrect détecté pour l'ID {file_id} : {file_path}")
                print(f"Chemin corrigé : {expected_path}")
                self.cursor.execute("UPDATE library SET file_path = ? WHERE id = ?", (expected_path, file_id))
        self.conn.commit()

    def verify_and_fix_file_paths(self):
        """Vérifie l'existence des fichiers et corrige les chemins dans la base si nécessaire."""
        if not messagebox.askyesno("Confirmation", "Voulez-vous vérifier et corriger les chemins des fichiers ?"):
            return
        self.cursor.execute("SELECT id, year, category, archives, project, title, file_path FROM library WHERE file_path != ''")
        files = self.cursor.fetchall()
        corrected = 0
        missing = 0
        for file_id, year, category, archives, project, title, file_path in files:
            # Construire le chemin attendu
            path_components = [str(year), category]
            if archives:
                path_components.append(archives)
            path_components.append(project)
            path_components.append(title)
            expected_relative_path = os.path.join(*path_components)
            expected_relative_path = expected_relative_path.replace('\\', '/')
            expected_full_path = os.path.normpath(os.path.join(self.files_dir, expected_relative_path))

            # Vérifier si le fichier existe au chemin attendu
            if os.path.exists(expected_full_path):
                if file_path != expected_relative_path:
                    print(f"Corrige le chemin pour l'ID {file_id} : {file_path} -> {expected_relative_path}")
                    self.cursor.execute("UPDATE library SET file_path = ? WHERE id = ?", (expected_relative_path, file_id))
                    corrected += 1
            else:
                print(f"Fichier manquant pour l'ID {file_id} : {expected_full_path}")
                missing += 1

        self.conn.commit()
        messagebox.showinfo("Vérification terminée", f"Chemins corrigés : {corrected}\nFichiers manquants : {missing}")

    def toggle_file_fields(self):
        state = "disabled" if self.keep_name_var.get() else "normal"
        self.site_entry.configure(state=state)
        self.nomenclature_entry.configure(state=state)
        self.emetteur_entry.configure(state=state)
        self.objet_entry.configure(state=state)
        self.version_entry.configure(state=state)

    def load_folder_to_form(self, event):
        selected = self.folder_tree.selection()
        if not selected:
            self.current_selected_folder = None
            self.clear_folder_form()
            self.load_files()
            return
        year, category, archives, project, notes = self.folder_tree.item(selected[0])["values"]
        self.current_selected_folder = (year, category, archives, project, notes)
        self.folder_year_var.set(year)
        self.folder_category_var.set(category)
        self.folder_archives_var.set(archives or "")
        self.folder_project_var.set(project)
        self.folder_notes_var.set(notes or "")
        self.load_files()

    def add_folder(self):
        year = self.folder_year_var.get()
        category = self.folder_category_var.get()
        archives = self.folder_archives_var.get()
        project = self.folder_project_var.get()
        notes = self.folder_notes_var.get()

        if not all([year, category, project]):
            messagebox.showwarning("Erreur", "Les champs Année, Catégorie et Projet doivent être remplis.")
            return

        path_components = [self.files_dir, str(year), category]
        if archives:
            path_components.append(archives)
        path_components.append(project)
        folder_path = os.path.normpath(os.path.join(*path_components))
        try:
            os.makedirs(folder_path, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de créer le dossier : {e}")
            return

        self.cursor.execute('''INSERT INTO library (title, year, category, archives, project, notes, file_path)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                           ("[Dossier]", year, category, archives, project, notes, ""))
        self.conn.commit()
        self.all_folders.append((year, category, archives or "", project, notes or ""))
        print(f"Added folder to self.all_folders: {year}/{category}/{archives}/{project}")
        self.refresh_folder_list()
        self.clear_folder_form()

    def modify_folder(self):
        if not self.current_selected_folder:
            messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier à modifier.")
            return

        new_year = self.folder_year_var.get()
        new_category = self.folder_category_var.get()
        new_archives = self.folder_archives_var.get()
        new_project = self.folder_project_var.get()
        new_notes = self.folder_notes_var.get()

        if not all([new_year, new_category, new_project]):
            messagebox.showwarning("Erreur", "Les champs Année, Catégorie et Projet doivent être remplis.")
            return

        old_year, old_category, old_archives, old_project, old_notes = self.current_selected_folder

        if (old_year, old_category, old_archives, old_project, old_notes) == (new_year, new_category, new_archives, new_project, new_notes):
            messagebox.showinfo("Information", "Aucune modification détectée.")
            return

        if not messagebox.askyesno("Confirmation", "Voulez-vous vraiment modifier ce dossier ?"):
            return

        # Vérifier si le nouveau dossier existe déjà (sauf si c'est le même dossier)
        self.cursor.execute("SELECT 1 FROM library WHERE year=? AND category=? AND (archives=? OR archives IS NULL) AND project=? AND (year != ? OR category != ? OR archives != ? OR project != ?)",
                           (new_year, new_category, new_archives or None, new_project, old_year, old_category, old_archives or None, old_project))
        if self.cursor.fetchone():
            messagebox.showerror("Erreur", "Ce dossier existe déjà.")
            return

        # Déplacer le dossier physique
        old_path_components = [self.files_dir, str(old_year), old_category]
        if old_archives:
            old_path_components.append(old_archives)
        old_path_components.append(old_project)
        old_folder_path = os.path.normpath(os.path.join(*old_path_components))

        new_path_components = [self.files_dir, str(new_year), new_category]
        if new_archives:
            new_path_components.append(new_archives)
        new_path_components.append(new_project)
        new_folder_path = os.path.normpath(os.path.join(*new_path_components))

        if os.path.exists(old_folder_path):
            try:
                os.makedirs(os.path.dirname(new_folder_path), exist_ok=True)
                shutil.move(old_folder_path, new_folder_path)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de déplacer le dossier : {e}")
                return

        # Mettre à jour la base de données
        self.cursor.execute('''UPDATE library SET year=?, category=?, archives=?, project=?, notes=? 
                            WHERE year=? AND category=? AND (archives=? OR archives IS NULL) AND project=?''',
                           (new_year, new_category, new_archives or None, new_project, new_notes, old_year, old_category, old_archives or None, old_project))
        
        # Mettre à jour les chemins des fichiers
        self.cursor.execute("SELECT id, file_path FROM library WHERE year=? AND category=? AND (archives=? OR archives IS NULL) AND project=? AND file_path != ''",
                           (new_year, new_category, new_archives or None, new_project))
        for file_id, file_path in self.cursor.fetchall():
            file_name = os.path.basename(file_path)
            path_components = [str(new_year), new_category]
            if new_archives:
                path_components.append(new_archives)
            path_components.append(new_project)
            path_components.append(file_name)
            new_relative_path = os.path.join(*path_components)
            new_relative_path = new_relative_path.replace('\\', '/')
            self.cursor.execute("UPDATE library SET file_path=? WHERE id=?", (new_relative_path, file_id))
        
        self.conn.commit()

        # Mettre à jour self.all_folders
        self.all_folders = [f for f in self.all_folders if f != (old_year, old_category, old_archives, old_project, old_notes)]
        self.all_folders.append((new_year, new_category, new_archives or "", new_project, new_notes or ""))

        # Mettre à jour self.all_files
        for i, (file_id, title, f_year, f_category, f_archives, f_project) in enumerate(self.all_files):
            if (f_year, f_category, f_archives, f_project) == (old_year, old_category, old_archives, old_project):
                self.all_files[i] = (file_id, title, new_year, new_category, new_archives or "", new_project)

        # Mettre à jour la sélection actuelle
        self.current_selected_folder = (new_year, new_category, new_archives or "", new_project, new_notes or "")
        self.current_folder = self.current_selected_folder
        self.refresh_folder_list()
        self.clear_folder_form()
        self.load_files()

    def delete_folder(self):
        selected = self.folder_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier à supprimer.")
            return
        year, category, archives, project, notes = self.folder_tree.item(selected[0])["values"]
        
        # Compter le nombre de pièces dans le dossier
        num_files = sum(1 for f in self.all_files if f[2] == year and f[3] == category and f[4] == (archives or "") and f[5] == project)
        
        if not messagebox.askyesno("Confirmation", f"Supprimer le dossier {year}/{category}/{archives or ''}/{project} et ses {num_files} pièce(s) ?"):
            return

        path_components = [self.files_dir, str(year), category]
        if archives:
            path_components.append(archives)
        path_components.append(project)
        folder_path = os.path.normpath(os.path.join(*path_components))
        self.cursor.execute("SELECT file_path FROM library WHERE year=? AND category=? AND (archives=? OR archives IS NULL) AND project=?", 
                           (year, category, archives or None, project))
        for row in self.cursor.fetchall():
            file_path = row[0]
            if file_path:
                full_path = os.path.normpath(os.path.join(self.files_dir, file_path))
                try:
                    if os.path.exists(full_path):
                        os.remove(full_path)
                except Exception as e:
                    pass
        try:
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
        except Exception as e:
            pass
        self.cursor.execute("DELETE FROM library WHERE year=? AND category=? AND (archives=? OR archives IS NULL) AND project=?", 
                           (year, category, archives or None, project))
        self.conn.commit()

        # Mettre à jour self.all_folders et self.all_files
        self.all_folders = [f for f in self.all_folders if f != (year, category, archives or "", project, notes or "")]
        self.all_files = [f for f in self.all_files if not (f[2] == year and f[3] == category and f[4] == (archives or "") and f[5] == project)]

        # Vérifier si la catégorie est vide
        self.cursor.execute("SELECT 1 FROM library WHERE category=?", (category,))
        if not self.cursor.fetchone():
            messagebox.showinfo("Information", f"La catégorie '{category}' est vide et a été supprimée.")
            for year_dir in os.listdir(self.files_dir):
                category_path = os.path.normpath(os.path.join(self.files_dir, year_dir, category))
                try:
                    if os.path.exists(category_path):
                        shutil.rmtree(category_path)
                except Exception as e:
                    pass
            
        self.refresh_folder_list()
        self.clear_folder_form()
        self.load_files()

    def delete_category(self):
        if not self.current_selected_folder:
            messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier pour supprimer sa catégorie.")
            return
        _, category, _, _, _ = self.current_selected_folder
        
        # Compter le nombre de dossiers et de pièces dans la catégorie
        num_folders = sum(1 for f in self.all_folders if f[1] == category)
        num_files = sum(1 for f in self.all_files if f[3] == category)

        if not messagebox.askyesno("Confirmation", f"Supprimer la catégorie '{category}' ? Cela supprimera {num_folders} dossier(s) et {num_files} pièce(s)."):
            return

        self.cursor.execute("SELECT DISTINCT year, archives, project FROM library WHERE category=?", (category,))
        for year, archives, project in self.cursor.fetchall():
            path_components = [self.files_dir, str(year), category]
            if archives:
                path_components.append(archives)
            path_components.append(project)
            folder_path = os.path.normpath(os.path.join(*path_components))
            self.cursor.execute("SELECT file_path FROM library WHERE year=? AND category=? AND (archives=? OR archives IS NULL) AND project=?", 
                               (year, category, archives or None, project))
            for row in self.cursor.fetchall():
                file_path = row[0]
                if file_path:
                    full_path = os.path.normpath(os.path.join(self.files_dir, file_path))
                    try:
                        if os.path.exists(full_path):
                            os.remove(full_path)
                    except Exception as e:
                        pass
            try:
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
            except Exception as e:
                pass
        for year_dir in os.listdir(self.files_dir):
            category_path = os.path.normpath(os.path.join(self.files_dir, year_dir, category))
            try:
                if os.path.exists(category_path):
                    shutil.rmtree(category_path)
            except Exception as e:
                pass
        self.cursor.execute("DELETE FROM library WHERE category=?", (category,))
        self.conn.commit()

        # Mettre à jour self.all_folders et self.all_files
        self.all_folders = [f for f in self.all_folders if f[1] != category]
        self.all_files = [f for f in self.all_files if f[3] != category]

        self.refresh_folder_list()
        self.clear_folder_form()
        self.load_files()

    def add_file(self):
        selected = self.folder_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier dans le premier Treeview.")
            return

        year, category, archives, project, notes = self.folder_tree.item(selected[0])["values"]
        print(f"Adding file to folder: {year}/{category}/{archives}/{project}")
        file_path = filedialog.askopenfilename(
            filetypes=[("Tous les fichiers", "*.*")],
            title="Sélectionner un fichier"
        )
        if not file_path:
            return

        keep_name = self.keep_name_var.get()
        move_file = self.move_file_var.get()
        if move_file:
            if not messagebox.askyesno("Confirmation", "Voulez-vous vraiment déplacer (couper) ce fichier ?"):
                return
        if keep_name:
            title = os.path.basename(file_path)
            site = None
            nomenclature = None
            emetteur = None
            objet = None
            version = None
        else:
            site = self.site_var.get()
            nomenclature = self.nomenclature_var.get()
            emetteur = self.emetteur_var.get()
            objet = self.objet_var.get()
            version = self.version_var.get()
            if not all([site, nomenclature, emetteur, objet, version]):
                messagebox.showwarning("Erreur", "Tous les champs de la pièce doivent être remplis si le renommage est activé.")
                return
            title = f"{year}-{site}-{nomenclature}-{emetteur}-{objet}-{version}{os.path.splitext(file_path)[1]}"

        # Construire le chemin de destination
        path_components = [str(year), category]
        if archives:
            path_components.append(archives)
        path_components.append(project)
        relative_dest_dir = os.path.join(*path_components)
        relative_dest_dir = relative_dest_dir.replace('\\', '/')
        dest_dir = os.path.normpath(os.path.join(self.files_dir, relative_dest_dir))
        try:
            os.makedirs(dest_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de créer le dossier de destination : {e}")
            return
        relative_dest_path = os.path.join(relative_dest_dir, title)
        relative_dest_path = relative_dest_path.replace('\\', '/')
        dest_path = os.path.normpath(os.path.join(self.files_dir, relative_dest_path))

        if os.path.exists(dest_path):
            if not messagebox.askyesno("Confirmation", f"Le fichier {title} existe déjà. Voulez-vous l'écraser ?"):
                return

        try:
            if move_file:
                shutil.move(file_path, dest_path)
            else:
                shutil.copy2(file_path, dest_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de {'déplacer' if move_file else 'copier'} le fichier : {e}")
            return

        self.cursor.execute('''INSERT INTO library (title, year, category, archives, project, site, nomenclature, emetteur, objet, version, file_path, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (title, year, category, archives, project, site, nomenclature, emetteur, objet, version, relative_dest_path, notes))
        self.conn.commit()

        # Récupérer l'ID du fichier inséré
        self.cursor.execute("SELECT last_insert_rowid()")
        file_id = self.cursor.fetchone()[0]

        # Ajouter le fichier à self.all_files
        self.all_files.append((file_id, title, year, category, archives or "", project))
        print(f"Added file to self.all_files: ID={file_id}, Title={title}")

        # Mettre à jour la sélection actuelle
        self.current_selected_folder = (year, category, archives or "", project, notes or "")
        self.current_folder = self.current_selected_folder
        print(f"Set current_selected_folder: {self.current_selected_folder}")

        # Rafraîchir la liste des dossiers
        self.refresh_folder_list()

        # Sélectionner explicitement le dossier dans le Treeview
        for item in self.folder_tree.get_children():
            values = self.folder_tree.item(item)["values"]
            if (values[0] == year and 
                values[1] == category and 
                values[2] == (archives or "") and 
                values[3] == project):
                self.folder_tree.selection_set(item)
                self.folder_tree.focus(item)
                self.folder_tree.see(item)
                print(f"Selected folder in folder_tree: {values}")
                break
        else:
            print("Warning: Could not re-select folder in folder_tree")

        # Recharger les fichiers pour le dossier sélectionné
        self.load_files()

    def modify_file(self):
        if not self.current_file_id:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce à modifier.")
            return

        if not messagebox.askyesno("Confirmation", "Voulez-vous vraiment modifier cette pièce ?"):
            return

        selected = self.folder_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier dans le premier Treeview.")
            return

        year, category, archives, project, notes = self.folder_tree.item(selected[0])["values"]
        keep_name = self.keep_name_var.get()
        if keep_name:
            self.cursor.execute("SELECT title FROM library WHERE id=?", (self.current_file_id,))
            title = self.cursor.fetchone()[0]
            site = None
            nomenclature = None
            emetteur = None
            objet = None
            version = None
        else:
            site = self.site_var.get()
            nomenclature = self.nomenclature_var.get()
            emetteur = self.emetteur_var.get()
            objet = self.objet_var.get()
            version = self.version_var.get()
            if not all([site, nomenclature, emetteur, objet, version]):
                messagebox.showwarning("Erreur", "Tous les champs de la pièce doivent être remplis si le renommage est activé.")
                return
            self.cursor.execute("SELECT file_path FROM library WHERE id=?", (self.current_file_id,))
            old_path = os.path.normpath(os.path.join(self.files_dir, self.cursor.fetchone()[0]))
            title = f"{year}-{site}-{nomenclature}-{emetteur}-{objet}-{version}{os.path.splitext(old_path)[1]}"

        self.cursor.execute("SELECT file_path FROM library WHERE id=?", (self.current_file_id,))
        old_relative_path = self.cursor.fetchone()[0]
        old_path = os.path.normpath(os.path.join(self.files_dir, old_relative_path))

        # Construire le nouveau chemin
        path_components = [str(year), category]
        if archives:
            path_components.append(archives)
        path_components.append(project)
        relative_dest_dir = os.path.join(*path_components)
        relative_dest_dir = relative_dest_dir.replace('\\', '/')
        dest_dir = os.path.normpath(os.path.join(self.files_dir, relative_dest_dir))
        try:
            os.makedirs(dest_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de créer le dossier de destination : {e}")
            return
        new_relative_path = os.path.join(relative_dest_dir, title)
        new_relative_path = new_relative_path.replace('\\', '/')
        new_path = os.path.normpath(os.path.join(self.files_dir, new_relative_path))

        if new_path != old_path:
            if os.path.exists(new_path):
                if not messagebox.askyesno("Confirmation", f"Le fichier {title} existe déjà. Voulez-vous l'écraser ?"):
                    return
            try:
                shutil.move(old_path, new_path)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de renommer/déplacer le fichier : {e}")
                return

        self.cursor.execute('''UPDATE library SET title=?, year=?, category=?, archives=?, project=?, site=?, nomenclature=?, emetteur=?, objet=?, version=?, file_path=?, notes=?
                            WHERE id=?''',
                           (title, year, category, archives, project, site, nomenclature, emetteur, objet, version, new_relative_path, notes, self.current_file_id))
        self.conn.commit()

        # Mettre à jour self.all_files
        for i, (file_id, _, f_year, f_category, f_archives, f_project) in enumerate(self.all_files):
            if file_id == self.current_file_id:
                self.all_files[i] = (file_id, title, year, category, archives or "", project)
                print(f"Updated file in self.all_files: ID={file_id}, Title={title}")
                break

        self.current_selected_folder = (year, category, archives or "", project, notes or "")
        self.current_folder = self.current_selected_folder
        self.refresh_folder_list()
        self.load_files()

    def delete_file(self):
        selected = self.file_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce à supprimer.")
            return
        file_id = self.file_tree.item(selected[0])["values"][0]
        self.cursor.execute("SELECT title FROM library WHERE id=?", (file_id,))
        file_title = self.cursor.fetchone()[0]
        if not messagebox.askyesno("Confirmation", f"Supprimer la pièce '{file_title}' de la bibliothèque ?"):
            return
        self.cursor.execute("SELECT file_path FROM library WHERE id=?", (file_id,))
        relative_path = self.cursor.fetchone()[0]
        file_path = os.path.normpath(os.path.join(self.files_dir, relative_path))
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            pass
        self.cursor.execute("DELETE FROM library WHERE id=?", (file_id,))
        self.conn.commit()

        # Mettre à jour self.all_files
        self.all_files = [f for f in self.all_files if f[0] != file_id]
        print(f"Deleted file from self.all_files: ID={file_id}, Title={file_title}")

        self.refresh_folder_list()
        self.clear_file_form()
        self.load_files()

    def open_file(self):
        selected = self.file_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce à ouvrir.")
            return
        file_id = self.file_tree.item(selected[0])["values"][0]
        self.cursor.execute("SELECT year, category, archives, project, title, file_path FROM library WHERE id=?", (file_id,))
        result = self.cursor.fetchone()
        if not result:
            messagebox.showerror("Erreur", f"Aucune entrée trouvée pour l'ID {file_id}.")
            return
        
        year, category, archives, project, title, stored_file_path = result

        # Construire le chemin attendu
        path_components = [str(year), category]
        if archives:
            path_components.append(archives)
        path_components.append(project)
        path_components.append(title)
        expected_relative_path = os.path.join(*path_components)
        expected_relative_path = expected_relative_path.replace('\\', '/')
        expected_file_path = os.path.normpath(os.path.join(self.files_dir, expected_relative_path))

        # Vérifier si le fichier existe avec le chemin reconstruit
        if os.path.exists(expected_file_path):
            file_path = expected_file_path
            print(f"Ouverture du fichier avec le chemin reconstruit : {file_path}")
        else:
            # Si le fichier n'existe pas au chemin attendu, essayer le chemin stocké
            stored_file_path = stored_file_path.replace('\\', '/')
            file_path = os.path.normpath(os.path.join(self.files_dir, stored_file_path))
            print(f"Fichier non trouvé au chemin reconstruit, tentative avec le chemin stocké : {file_path}")
            if not os.path.exists(file_path):
                messagebox.showerror("Erreur", f"Le fichier n'existe pas :\nChemin attendu : {expected_file_path}\nChemin stocké : {file_path}\nVérifiez si le fichier a été déplacé ou supprimé.")
                return

        # Vérifier les permissions de lecture
        if not os.access(file_path, os.R_OK):
            messagebox.showerror("Erreur", f"Le fichier '{file_path}' n'a pas les permissions de lecture.")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Linux":
                result = subprocess.run(
                    ["xdg-open", file_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if result.stderr:
                    messagebox.showwarning("Avertissement", f"Erreur lors de l'ouverture avec xdg-open : {result.stderr}")
            else:
                subprocess.run(["open", file_path], check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erreur", f"Échec de l'ouverture du fichier : {e.stderr}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier : {str(e)}")

    def open_file_explorer(self):
        selected = self.file_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce pour ouvrir son emplacement.")
            return
        file_id = self.file_tree.item(selected[0])["values"][0]
        self.cursor.execute("SELECT year, category, archives, project, title, file_path FROM library WHERE id=?", (file_id,))
        result = self.cursor.fetchone()
        if not result:
            messagebox.showerror("Erreur", f"Aucune entrée trouvée pour l'ID {file_id}.")
            return
        
        year, category, archives, project, title, stored_file_path = result

        # Construire le chemin attendu
        path_components = [str(year), category]
        if archives:
            path_components.append(archives)
        path_components.append(project)
        path_components.append(title)
        expected_relative_path = os.path.join(*path_components)
        expected_relative_path = expected_relative_path.replace('\\', '/')
        expected_file_path = os.path.normpath(os.path.join(self.files_dir, expected_relative_path))

        # Vérifier si le fichier existe au chemin reconstruit
        if os.path.exists(expected_file_path):
            file_path = expected_file_path
        else:
            # Sinon, utiliser le chemin stocké
            stored_file_path = stored_file_path.replace('\\', '/')
            file_path = os.path.normpath(os.path.join(self.files_dir, stored_file_path))
            if not os.path.exists(file_path):
                messagebox.showerror("Erreur", f"Le fichier n'existe pas pour ouvrir son emplacement :\nChemin attendu : {expected_file_path}\nChemin stocké : {file_path}")
                return

        # Obtenir le dossier parent du fichier
        folder_path = os.path.dirname(file_path)

        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", folder_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", folder_path])
            else:
                subprocess.run(["open", folder_path])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'explorateur de fichiers : {str(e)}")

    def load_file_to_form(self, event):
        selected = self.file_tree.selection()
        if not selected:
            return
        file_id = self.file_tree.item(selected[0])["values"][0]
        self.current_file_id = file_id
        self.cursor.execute("SELECT title, site, nomenclature, emetteur, objet, version FROM library WHERE id=?", (file_id,))
        result = self.cursor.fetchone()
        if result:
            title, site, nomenclature, emetteur, objet, version = result
            self.site_var.set(site or "")
            self.nomenclature_var.set(nomenclature or "")
            self.emetteur_var.set(emetteur or "")
            self.objet_var.set(objet or "")
            self.version_var.set(version or "")
            self.keep_name_var.set(not all([site, nomenclature, emetteur, objet, version]))
            self.toggle_file_fields()

    def clear_folder_form(self):
        self.current_selected_folder = None
        self.folder_year_var.set(str(datetime.now().year))
        self.folder_category_var.set("")
        self.folder_archives_var.set("")
        self.folder_project_var.set("")
        self.folder_notes_var.set("")

    def clear_file_form(self):
        self.current_file_id = None
        self.site_var.set("")
        self.nomenclature_var.set("")
        self.emetteur_var.set("")
        self.objet_var.set("")
        self.version_var.set("V1")
        self.keep_name_var.set(False)
        self.move_file_var.set(False)
        self.toggle_file_fields()

    def sort_column(self, col, reverse):
        self.sort_column_name = col
        self.sort_reverse = reverse
        self.sort_direction[col] = not reverse
        self.refresh_folder_list()
        self.folder_tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def refresh_folder_list(self):
        selected = self.folder_tree.selection()
        selected_values = None
        selected_iid = None
        if selected:
            selected_iid = selected[0]
            selected_values = self.folder_tree.item(selected_iid)["values"]

        # Filtrer les données en mémoire avec recherche partielle
        year_filter = self.year_filter_var.get().strip().lower()
        category_filter = self.category_filter_var.get().strip().lower()
        archives_filter = self.archives_filter_var.get().strip().lower()
        project_filter = self.project_filter_var.get().strip().lower()

        filtered_folders = [
            row for row in self.all_folders
            if (not year_filter or year_filter in str(row[0]).lower())
            and (not category_filter or category_filter in str(row[1]).lower())
            and (not archives_filter or archives_filter in str(row[2] or "").lower())
            and (not project_filter or project_filter in str(row[3]).lower())
        ]

        # Vider le Treeview
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)

        # Appliquer le tri sur les données filtrées
        col_index = {"Year": 0, "Category": 1, "Archives": 2, "Project": 3, "Notes": 4}
        sort_index = col_index[self.sort_column_name]
        filtered_folders.sort(
            key=lambda x: str(x[sort_index] or "").lower(),
            reverse=self.sort_reverse
        )

        # Insérer les données filtrées et triées dans le Treeview avec couleurs alternées
        items = []
        for index, row in enumerate(filtered_folders):
            # Normaliser les valeurs, en particulier archives
            normalized_row = (str(row[0]), str(row[1]), str(row[2] or ""), str(row[3]), str(row[4] or ""))
            tag = "OddRow" if index % 2 else "EvenRow"
            item = self.folder_tree.insert("", tk.END, values=normalized_row, tags=(tag,))
            items.append((item, normalized_row))

        # Restaurer la sélection
        if selected_values and self.current_selected_folder:
            normalized_selected = (
                str(self.current_selected_folder[0]), 
                str(self.current_selected_folder[1]), 
                str(self.current_selected_folder[2] or ""), 
                str(self.current_selected_folder[3]), 
                str(self.current_selected_folder[4] or "")
            )
            found = False
            for item, values in items:
                if values == normalized_selected:
                    self.folder_tree.selection_set(item)
                    self.folder_tree.see(item)
                    found = True
                    break
            if not found:
                if items:
                    first_item, first_values = items[0]
                    self.folder_tree.selection_set(first_item)
                    self.current_selected_folder = first_values
                    self.current_folder = first_values
                    self.folder_tree.see(first_item)

    def filter_folders(self, *args):
        self.refresh_folder_list()

    def load_files(self):
        """Charge les fichiers du dossier sélectionné dans le Treeview des pièces en utilisant self.all_files."""
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        if not self.current_selected_folder:
            self.current_folder = None
            print("No folder selected, clearing file_tree")
            return
        
        self.current_folder = self.current_selected_folder
        year, category, archives, project, notes = self.current_folder
        print(f"Loading files for folder: {year}/{category}/{archives}/{project}")

        # Filtrer les fichiers correspondant au dossier sélectionné
        matching_files = [
            (file_id, title) for file_id, title, f_year, f_category, f_archives, f_project in self.all_files
            if f_year == year and f_category == category and f_archives == (archives or "") and f_project == project
        ]

        print(f"Found {len(matching_files)} files for folder: {matching_files}")

        # Peupler le Treeview
        for index, (file_id, title) in enumerate(matching_files):
            tag = "OddRow" if index % 2 else "EvenRow"
            self.file_tree.insert("", tk.END, values=(file_id, title), tags=(tag,))

    def filter_files(self, event=None):
        """Filtre les fichiers dans le Treeview des pièces en fonction du terme de recherche."""
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        if not self.current_folder:
            print("No folder selected for filtering files")
            return
        
        search_term = self.search_var.get().lower()
        year, category, archives, project, notes = self.current_folder
        print(f"Filtering files for folder: {year}/{category}/{archives}/{project}, search_term: {search_term}")

        # Filtrer les fichiers correspondant au dossier et au terme de recherche
        matching_files = [
            (file_id, title) for file_id, title, f_year, f_category, f_archives, f_project in self.all_files
            if f_year == year and f_category == category and f_archives == (archives or "") and f_project == project
            and search_term in title.lower()
        ]

        print(f"Found {len(matching_files)} filtered files: {matching_files}")

        # Peupler le Treeview
        for index, (file_id, title) in enumerate(matching_files):
            tag = "OddRow" if index % 2 else "EvenRow"
            self.file_tree.insert("", tk.END, values=(file_id, title), tags=(tag,))