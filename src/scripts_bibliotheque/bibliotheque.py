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

        # Variables pour les filtres du Treeview 1
        self.year_filter_var = tk.StringVar()
        self.category_filter_var = tk.StringVar()
        self.project_filter_var = tk.StringVar()

        # Configurer les styles pour les boutons
        style = ttk.Style()
        style.configure("Add.TButton", background="#90EE90", foreground="black")  # Vert clair
        style.configure("Modify.TButton", background="#FFFFE0", foreground="black")  # Jaune clair
        style.configure("Clear.TButton", background="#ADD8E6", foreground="black")  # Bleu clair
        style.configure("Delete.TButton", background="#FF0000", foreground="#FFFFFF")  # Rouge, texte blanc

        # Interface principale avec PanedWindow
        self.paned_window = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True, padx=10, pady=10)

        # Gauche : Treeview 1 (Année, Catégorie, Projet) avec filtres
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=1)

        # Filtres pour Treeview 1
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(filter_frame, text="Filtrer Année :").pack(side="left")
        ttk.Entry(filter_frame, textvariable=self.year_filter_var, width=10).pack(side="left", padx=5)
        ttk.Label(filter_frame, text="Catégorie :").pack(side="left")
        ttk.Entry(filter_frame, textvariable=self.category_filter_var, width=15).pack(side="left", padx=5)
        ttk.Label(filter_frame, text="Projet :").pack(side="left")
        ttk.Entry(filter_frame, textvariable=self.project_filter_var, width=20).pack(side="left", padx=5)
        self.year_filter_var.trace("w", self.filter_folders)
        self.category_filter_var.trace("w", self.filter_folders)
        self.project_filter_var.trace("w", self.filter_folders)

        self.folder_tree = ttk.Treeview(left_frame, columns=("Year", "Category", "Project"), show="headings")
        self.folder_tree.heading("Year", text="Année", command=lambda: self.sort_column("Year", False))
        self.folder_tree.heading("Category", text="Catégorie", command=lambda: self.sort_column("Category", False))
        self.folder_tree.heading("Project", text="Projet", command=lambda: self.sort_column("Project", False))
        self.folder_tree.column("Year", width=100)
        self.folder_tree.column("Category", width=150)
        self.folder_tree.column("Project", width=200)
        self.folder_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.folder_tree.bind("<<TreeviewSelect>>", self.load_folder_to_form)

        # Droite : Formulaires et Treeview 2
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=3)

        # Formulaire 1 : Année, Catégorie, Projet
        folder_form_frame = ttk.LabelFrame(right_frame, text="Gestion des dossiers")
        folder_form_frame.pack(fill="x", pady=5)

        ttk.Label(folder_form_frame, text="Année :").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.folder_year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Entry(folder_form_frame, textvariable=self.folder_year_var, width=10).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(folder_form_frame, text="Catégorie :").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.folder_category_var = tk.StringVar()
        ttk.Entry(folder_form_frame, textvariable=self.folder_category_var, width=15).grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(folder_form_frame, text="Projet :").grid(row=0, column=4, padx=5, pady=2, sticky="w")
        self.folder_project_var = tk.StringVar()
        ttk.Entry(folder_form_frame, textvariable=self.folder_project_var, width=20).grid(row=0, column=5, padx=5, pady=2)

        folder_button_frame = ttk.Frame(folder_form_frame)
        folder_button_frame.grid(row=1, column=0, columnspan=7, pady=5)
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
        ttk.Checkbutton(file_form_frame, text="Conserver le nom du fichier", variable=self.keep_name_var, command=self.toggle_file_fields).grid(row=0, column=0, columnspan=6, pady=2, sticky="w")

        # Case à cocher pour couper/copier
        self.move_file_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(file_form_frame, text="Couper (déplacer) / Copier", variable=self.move_file_var).grid(row=1, column=0, columnspan=6, pady=2, sticky="w")

        ttk.Label(file_form_frame, text="Site :").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.site_var = tk.StringVar()
        self.site_entry = ttk.Entry(file_form_frame, textvariable=self.site_var, width=15)
        self.site_entry.grid(row=2, column=1, padx=5, pady=2)
        ttk.Button(file_form_frame, text="?", command=self.show_sites).grid(row=2, column=2, padx=2, pady=2)

        ttk.Label(file_form_frame, text="Nomenclature :").grid(row=2, column=3, padx=5, pady=2, sticky="w")
        self.nomenclature_var = tk.StringVar()
        self.nomenclature_entry = ttk.Entry(file_form_frame, textvariable=self.nomenclature_var, width=10)
        self.nomenclature_entry.grid(row=2, column=4, padx=5, pady=2)
        ttk.Button(file_form_frame, text="?", command=self.show_nomenclatures).grid(row=2, column=5, padx=2, pady=2)

        ttk.Label(file_form_frame, text="Émetteur :").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.emetteur_var = tk.StringVar()
        self.emetteur_entry = ttk.Entry(file_form_frame, textvariable=self.emetteur_var, width=15)
        self.emetteur_entry.grid(row=3, column=1, padx=5, pady=2)

        ttk.Label(file_form_frame, text="Objet :").grid(row=3, column=2, padx=5, pady=2, sticky="w")
        self.objet_var = tk.StringVar()
        self.objet_entry = ttk.Entry(file_form_frame, textvariable=self.objet_var, width=20)
        self.objet_entry.grid(row=3, column=3, padx=5, pady=2)

        ttk.Label(file_form_frame, text="Version :").grid(row=3, column=4, padx=5, pady=2, sticky="w")
        self.version_var = tk.StringVar(value="V1")
        self.version_entry = ttk.Entry(file_form_frame, textvariable=self.version_var, width=10)
        self.version_entry.grid(row=3, column=5, padx=5, pady=2)

        file_button_frame = ttk.Frame(file_form_frame)
        file_button_frame.grid(row=4, column=0, columnspan=6, pady=5)
        ttk.Button(file_button_frame, text="Ajouter pièce", style="Add.TButton", command=self.add_file).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Modifier pièce", style="Modify.TButton", command=self.modify_file).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Vider formulaire", style="Clear.TButton", command=self.clear_file_form).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Supprimer pièce", style="Delete.TButton", command=self.delete_file).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Ouvrir pièce", style="Add.TButton", command=self.open_file).pack(side="left", padx=5)

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
        self.sort_direction = {}
        self.toggle_file_fields()  # Initialiser l'état des champs
        self.refresh_folder_list()

    def init_nomenclatures_file(self):
        # Créer un fichier nomenclatures.json avec des valeurs par défaut s'il n'existe pas
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
                print(f"Erreur lors de la création de nomenclatures.json : {e}")

    def init_sites_file(self):
        # Créer un fichier sites.json avec des valeurs par défaut s'il n'existe pas
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
                print(f"Erreur lors de la création de sites.json : {e}")

    def show_nomenclatures(self):
        # Ouvrir une fenêtre pour afficher les nomenclatures
        nomenclatures_window = tk.Toplevel(self.parent)
        nomenclatures_window.title("Liste des nomenclatures")
        nomenclatures_window.geometry("400x300")
        nomenclatures_window.transient(self.parent)
        nomenclatures_window.grab_set()

        # Charger les nomenclatures depuis le fichier
        try:
            with open(self.nomenclatures_file, "r", encoding="utf-8") as f:
                nomenclatures = json.load(f)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les nomenclatures : {e}")
            nomenclatures_window.destroy()
            return

        # Barre de recherche
        search_frame = ttk.Frame(nomenclatures_window)
        search_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(search_frame, text="Rechercher :").pack(side="left")
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Treeview pour afficher les nomenclatures
        tree = ttk.Treeview(nomenclatures_window, columns=("Code", "Description"), show="headings")
        tree.heading("Code", text="Code")
        tree.heading("Description", text="Description")
        tree.column("Code", width=100)
        tree.column("Description", width=250)
        tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Fonction pour filtrer les nomenclatures
        def filter_nomenclatures(*args):
            search_term = search_var.get().lower()
            for item in tree.get_children():
                tree.delete(item)
            for nomenclature in nomenclatures:
                if search_term in nomenclature["code"].lower() or search_term in nomenclature["description"].lower():
                    tree.insert("", tk.END, values=(nomenclature["code"], nomenclature["description"]))

        # Initialiser le Treeview avec toutes les nomenclatures
        for nomenclature in nomenclatures:
            tree.insert("", tk.END, values=(nomenclature["code"], nomenclature["description"]))

        # Lier la recherche au Treeview
        search_var.trace("w", filter_nomenclatures)

        def apply_nomenclature():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Erreur", "Veuillez sélectionner une nomenclature.")
                return
            code = tree.item(selected[0])["values"][0]
            self.nomenclature_var.set(code)
            nomenclatures_window.destroy()

        # Bouton pour appliquer la nomenclature sélectionnée
        ttk.Button(nomenclatures_window, text="Appliquer", command=apply_nomenclature).pack(pady=5)
        ttk.Button(nomenclatures_window, text="Fermer", command=nomenclatures_window.destroy).pack(pady=5)

        # Centrer la fenêtre
        nomenclatures_window.update_idletasks()
        width = nomenclatures_window.winfo_width()
        height = nomenclatures_window.winfo_height()
        x = (nomenclatures_window.winfo_screenwidth() // 2) - (width // 2)
        y = (nomenclatures_window.winfo_screenheight() // 2) - (height // 2)
        nomenclatures_window.geometry(f"{width}x{height}+{x}+{y}")

    def show_sites(self):
        # Ouvrir une fenêtre pour afficher les sites
        sites_window = tk.Toplevel(self.parent)
        sites_window.title("Liste des sites")
        sites_window.geometry("400x300")
        sites_window.transient(self.parent)
        sites_window.grab_set()

        # Charger les sites depuis le fichier
        try:
            with open(self.sites_file, "r", encoding="utf-8") as f:
                sites = json.load(f)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les sites : {e}")
            sites_window.destroy()
            return

        # Barre de recherche
        search_frame = ttk.Frame(sites_window)
        search_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(search_frame, text="Rechercher :").pack(side="left")
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Treeview pour afficher les sites
        tree = ttk.Treeview(sites_window, columns=("Code", "Description"), show="headings")
        tree.heading("Code", text="Code")
        tree.heading("Description", text="Description")
        tree.column("Code", width=100)
        tree.column("Description", width=250)
        tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Fonction pour filtrer les sites
        def filter_sites(*args):
            search_term = search_var.get().lower()
            for item in tree.get_children():
                tree.delete(item)
            for site in sites:
                if search_term in site["code"].lower() or search_term in site["description"].lower():
                    tree.insert("", tk.END, values=(site["code"], site["description"]))

        # Initialiser le Treeview avec tous les sites
        for site in sites:
            tree.insert("", tk.END, values=(site["code"], site["description"]))

        # Lier la recherche au Treeview
        search_var.trace("w", filter_sites)

        def apply_site():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Erreur", "Veuillez sélectionner un site.")
                return
            code = tree.item(selected[0])["values"][0]
            self.site_var.set(code)
            sites_window.destroy()

        # Bouton pour appliquer le site sélectionné
        ttk.Button(sites_window, text="Appliquer", command=apply_site).pack(pady=5)
        ttk.Button(sites_window, text="Fermer", command=sites_window.destroy).pack(pady=5)

        # Centrer la fenêtre
        sites_window.update_idletasks()
        width = sites_window.winfo_width()
        height = sites_window.winfo_height()
        x = (sites_window.winfo_screenwidth() // 2) - (width // 2)
        y = (sites_window.winfo_screenheight() // 2) - (height // 2)
        sites_window.geometry(f"{width}x{height}+{x}+{y}")

    def init_db(self):
        # Créer la table si elle n'existe pas
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            year TEXT,
            category TEXT,
            project TEXT,
            site TEXT,
            nomenclature TEXT,
            emetteur TEXT,
            objet TEXT,
            version TEXT,
            file_path TEXT
        )''')
        # Vérifier et ajouter les colonnes manquantes
        self.cursor.execute("PRAGMA table_info(library)")
        columns = [info[1] for info in self.cursor.fetchall()]
        if 'year' not in columns:
            self.cursor.execute("ALTER TABLE library ADD COLUMN year TEXT")
            self.cursor.execute("UPDATE library SET year = ? WHERE year IS NULL", (str(datetime.now().year),))
        if 'category' not in columns:
            self.cursor.execute("ALTER TABLE library ADD COLUMN category TEXT")
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
        self.conn.commit()

    def toggle_file_fields(self):
        # Activer ou désactiver les champs du formulaire en fonction de la case à cocher
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
            self.load_files(None)
            return
        year, category, project = self.folder_tree.item(selected[0])["values"]
        self.current_selected_folder = (year, category, project)
        self.folder_year_var.set(year)
        self.folder_category_var.set(category)
        self.folder_project_var.set(project)
        self.load_files(event)

    def add_folder(self):
        year = self.folder_year_var.get()
        category = self.folder_category_var.get()
        project = self.folder_project_var.get()

        if not all([year, category, project]):
            messagebox.showwarning("Erreur", "Tous les champs du dossier doivent être remplis.")
            return

        # Créer le dossier physique
        folder_path = os.path.normpath(os.path.join(self.files_dir, str(year), category, project))
        try:
            os.makedirs(folder_path, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de créer le dossier : {e}")
            return

        # Insérer dans la base de données (enregistrement fictif pour le dossier)
        self.cursor.execute('''INSERT INTO library (title, year, category, project, file_path)
                            VALUES (?, ?, ?, ?, ?)''',
                           ("[Dossier]", year, category, project, ""))
        self.conn.commit()
        self.refresh_folder_list()
        self.clear_folder_form()

    def modify_folder(self):
        if not self.current_selected_folder:
            messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier à modifier.")
            return

        new_year = self.folder_year_var.get()
        new_category = self.folder_category_var.get()
        new_project = self.folder_project_var.get()

        if not all([new_year, new_category, new_project]):
            messagebox.showwarning("Erreur", "Tous les champs du dossier doivent être remplis.")
            return

        old_year, old_category, old_project = self.current_selected_folder

        if (old_year, old_category, old_project) == (new_year, new_category, new_project):
            messagebox.showinfo("Information", "Aucune modification détectée.")
            return

        # Vérifier si le nouveau dossier existe
        self.cursor.execute("SELECT 1 FROM library WHERE year=? AND category=? AND project=?", (new_year, new_category, new_project))
        if self.cursor.fetchone():
            messagebox.showerror("Erreur", "Ce dossier existe déjà.")
            return

        # Déplacer le dossier physique
        old_folder_path = os.path.normpath(os.path.join(self.files_dir, str(old_year), old_category, old_project))
        new_folder_path = os.path.normpath(os.path.join(self.files_dir, str(new_year), new_category, new_project))
        if os.path.exists(old_folder_path):
            try:
                shutil.move(old_folder_path, new_folder_path)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de déplacer le dossier : {e}")
                return

        # Mettre à jour la base de données
        self.cursor.execute('''UPDATE library SET year=?, category=?, project=? 
                            WHERE year=? AND category=? AND project=?''',
                           (new_year, new_category, new_project, old_year, old_category, old_project))
        # Mettre à jour les chemins des fichiers
        self.cursor.execute("SELECT id, file_path FROM library WHERE year=? AND category=? AND project=? AND file_path != ''",
                           (new_year, new_category, new_project))
        for file_id, file_path in self.cursor.fetchall():
            old_relative_path = file_path
            new_relative_path = os.path.join(str(new_year), new_category, new_project, os.path.basename(file_path))
            self.cursor.execute("UPDATE library SET file_path=? WHERE id=?", (new_relative_path, file_id))
        self.conn.commit()
        self.refresh_folder_list()
        self.clear_folder_form()
        self.load_files(None)

    def delete_folder(self):
        selected = self.folder_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier à supprimer.")
            return
        year, category, project = self.folder_tree.item(selected[0])["values"]
        if messagebox.askyesno("Confirmation", f"Supprimer le dossier {year}/{category}/{project} et toutes ses pièces ?"):
            folder_path = os.path.normpath(os.path.join(self.files_dir, str(year), category, project))
            self.cursor.execute("SELECT file_path FROM library WHERE year=? AND category=? AND project=?", (year, category, project))
            for row in self.cursor.fetchall():
                file_path = row[0]
                if file_path:
                    full_path = os.path.normpath(os.path.join(self.files_dir, file_path))
                    try:
                        if os.path.exists(full_path):
                            os.remove(full_path)
                    except Exception as e:
                        print(f"Erreur lors de la suppression du fichier : {e}")
            try:
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
            except Exception as e:
                print(f"Erreur lors de la suppression du dossier : {e}")
            self.cursor.execute("DELETE FROM library WHERE year=? AND category=? AND project=?", (year, category, project))
            
            # Vérifier si la catégorie est vide
            self.cursor.execute("SELECT 1 FROM library WHERE category=?", (category,))
            if not self.cursor.fetchone():
                messagebox.showinfo("Information", f"La catégorie '{category}' est vide et a été supprimée.")
                # Supprimer les dossiers physiques de la catégorie pour toutes les années
                for year_dir in os.listdir(self.files_dir):
                    category_path = os.path.normpath(os.path.join(self.files_dir, year_dir, category))
                    try:
                        if os.path.exists(category_path):
                            shutil.rmtree(category_path)
                    except Exception as e:
                        print(f"Erreur lors de la suppression du dossier de catégorie : {e}")
            
            self.conn.commit()
            self.refresh_folder_list()
            self.clear_folder_form()
            self.load_files(None)

    def delete_category(self):
        if not self.current_selected_folder:
            messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier pour supprimer sa catégorie.")
            return
        _, category, _ = self.current_selected_folder
        if messagebox.askyesno("Confirmation", f"Supprimer la catégorie '{category}' et tous ses dossiers et pièces ?"):
            self.cursor.execute("SELECT DISTINCT year, project FROM library WHERE category=?", (category,))
            for year, project in self.cursor.fetchall():
                folder_path = os.path.normpath(os.path.join(self.files_dir, str(year), category, project))
                self.cursor.execute("SELECT file_path FROM library WHERE year=? AND category=? AND project=?", (year, category, project))
                for row in self.cursor.fetchall():
                    file_path = row[0]
                    if file_path:
                        full_path = os.path.normpath(os.path.join(self.files_dir, file_path))
                        try:
                            if os.path.exists(full_path):
                                os.remove(full_path)
                        except Exception as e:
                            print(f"Erreur lors de la suppression du fichier : {e}")
                try:
                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path)
                except Exception as e:
                    print(f"Erreur lors de la suppression du dossier : {e}")
            # Supprimer le dossier de catégorie pour toutes les années
            for year_dir in os.listdir(self.files_dir):
                category_path = os.path.normpath(os.path.join(self.files_dir, year_dir, category))
                try:
                    if os.path.exists(category_path):
                        shutil.rmtree(category_path)
                except Exception as e:
                    print(f"Erreur lors de la suppression du dossier de catégorie : {e}")
            self.cursor.execute("DELETE FROM library WHERE category=?", (category,))
            self.conn.commit()
            self.refresh_folder_list()
            self.clear_folder_form()
            self.load_files(None)

    def add_file(self):
        selected = self.folder_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier dans le premier Treeview.")
            return

        year, category, project = self.folder_tree.item(selected[0])["values"]
        file_path = filedialog.askopenfilename(
            filetypes=[("Tous les fichiers", "*.*")],
            title="Sélectionner un fichier"
        )
        if not file_path:
            return

        keep_name = self.keep_name_var.get()
        move_file = self.move_file_var.get()
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

        # Créer le dossier de destination
        relative_dest_dir = os.path.join(str(year), category, project)
        dest_dir = os.path.normpath(os.path.join(self.files_dir, relative_dest_dir))
        try:
            os.makedirs(dest_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de créer le dossier de destination : {e}")
            return
        relative_dest_path = os.path.join(relative_dest_dir, title)
        dest_path = os.path.normpath(os.path.join(self.files_dir, relative_dest_path))

        # Vérifier si le fichier existe déjà
        if os.path.exists(dest_path):
            if not messagebox.askyesno("Confirmation", f"Le fichier {title} existe déjà. Voulez-vous l'écraser ?"):
                return

        # Copier ou déplacer le fichier
        try:
            if move_file:
                shutil.move(file_path, dest_path)
            else:
                shutil.copy2(file_path, dest_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de {'déplacer' if move_file else 'copier'} le fichier : {e}")
            return

        # Insérer dans la base de données (stocker le chemin relatif)
        self.cursor.execute('''INSERT INTO library (title, year, category, project, site, nomenclature, emetteur, objet, version, file_path)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (title, year, category, project, site, nomenclature, emetteur, objet, version, relative_dest_path))
        self.conn.commit()
        self.refresh_folder_list()

        # Simuler un événement pour recharger les pièces sans perdre le focus
        class FakeEvent:
            pass
        fake_event = FakeEvent()
        self.load_files(fake_event)

    def modify_file(self):
        if not self.current_file_id:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce à modifier.")
            return

        selected = self.folder_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier dans le premier Treeview.")
            return

        year, category, project = self.folder_tree.item(selected[0])["values"]
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

        # Récupérer l'ancien fichier
        self.cursor.execute("SELECT file_path FROM library WHERE id=?", (self.current_file_id,))
        old_relative_path = self.cursor.fetchone()[0]
        old_path = os.path.normpath(os.path.join(self.files_dir, old_relative_path))

        # Créer le nouveau chemin
        relative_dest_dir = os.path.join(str(year), category, project)
        dest_dir = os.path.normpath(os.path.join(self.files_dir, relative_dest_dir))
        try:
            os.makedirs(dest_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de créer le dossier de destination : {e}")
            return
        new_relative_path = os.path.join(relative_dest_dir, title)
        new_path = os.path.normpath(os.path.join(self.files_dir, new_relative_path))

        # Vérifier si le nouveau chemin est différent
        if new_path != old_path:
            if os.path.exists(new_path):
                if not messagebox.askyesno("Confirmation", f"Le fichier {title} existe déjà. Voulez-vous l'écraser ?"):
                    return
            try:
                shutil.move(old_path, new_path)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de renommer/déplacer le fichier : {e}")
                return

        # Mettre à jour la base de données
        self.cursor.execute('''UPDATE library SET title=?, year=?, category=?, project=?, site=?, nomenclature=?, emetteur=?, objet=?, version=?, file_path=?
                            WHERE id=?''',
                           (title, year, category, project, site, nomenclature, emetteur, objet, version, new_relative_path, self.current_file_id))
        self.conn.commit()
        self.refresh_folder_list()

        # Simuler un événement pour recharger les pièces sans perdre le focus
        class FakeEvent:
            pass
        fake_event = FakeEvent()
        self.load_files(fake_event)

    def delete_file(self):
        selected = self.file_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce à supprimer.")
            return
        if messagebox.askyesno("Confirmation", "Supprimer cette pièce de la bibliothèque ?"):
            file_id = self.file_tree.item(selected[0])["values"][0]
            self.cursor.execute("SELECT file_path FROM library WHERE id=?", (file_id,))
            relative_path = self.cursor.fetchone()[0]
            file_path = os.path.normpath(os.path.join(self.files_dir, relative_path))
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier : {e}")
            self.cursor.execute("DELETE FROM library WHERE id=?", (file_id,))
            self.conn.commit()
            self.refresh_folder_list()
            self.clear_file_form()
            self.load_files(None)

    def open_file(self):
        selected = self.file_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce à ouvrir.")
            return
        file_id = self.file_tree.item(selected[0])["values"][0]
        self.cursor.execute("SELECT file_path FROM library WHERE id=?", (file_id,))
        relative_path = self.cursor.fetchone()[0]
        file_path = os.path.normpath(os.path.join(self.files_dir, relative_path))
        if not os.path.exists(file_path):
            messagebox.showerror("Erreur", "Le fichier n'existe plus.")
            return
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            else:
                subprocess.run(["xdg-open", file_path], check=True)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier : {e}")

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
            # Activer le renommage si les champs sont remplis, sinon conserver le nom
            self.keep_name_var.set(not all([site, nomenclature, emetteur, objet, version]))
            self.toggle_file_fields()

    def clear_folder_form(self):
        self.current_selected_folder = None
        self.folder_year_var.set(str(datetime.now().year))
        self.folder_category_var.set("")
        self.folder_project_var.set("")

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
        items = [(self.folder_tree.set(item, col), item) for item in self.folder_tree.get_children()]
        items.sort(key=lambda x: x[0].lower(), reverse=reverse)
        for index, (value, item) in enumerate(items):
            self.folder_tree.move(item, "", index)
        self.sort_direction[col] = not reverse
        self.folder_tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def refresh_folder_list(self):
        # Mémoriser la sélection actuelle
        selected = self.folder_tree.selection()
        selected_values = None
        selected_iid = None
        if selected:
            selected_iid = selected[0]
            selected_values = self.folder_tree.item(selected_iid)["values"]
            print(f"Before refresh: Selected values = {selected_values}, IID = {selected_iid}")

        # Rafraîchir la liste
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)

        query = "SELECT DISTINCT year, category, project FROM library WHERE file_path != '' OR title = '[Dossier]'"
        params = []
        year_filter = self.year_filter_var.get().lower()
        category_filter = self.category_filter_var.get().lower()
        project_filter = self.project_filter_var.get().lower()
        conditions = []
        if year_filter:
            conditions.append("LOWER(year) LIKE ?")
            params.append(f"%{year_filter}%")
        if category_filter:
            conditions.append("LOWER(category) LIKE ?")
            params.append(f"%{category_filter}%")
        if project_filter:
            conditions.append("LOWER(project) LIKE ?")
            params.append(f"%{project_filter}%")
        if conditions:
            query += " AND " + " AND ".join(conditions)
        self.cursor.execute(query, params)

        # Réinsérer les éléments
        items = []
        for row in self.cursor.fetchall():
            # Convertir toutes les valeurs en chaînes pour éviter les problèmes de type
            normalized_row = (str(row[0]), str(row[1]), str(row[2]))
            item = self.folder_tree.insert("", tk.END, values=normalized_row)
            items.append((item, normalized_row))
            print(f"Inserted item: IID = {item}, values = {normalized_row}")

        # Restaurer la sélection
        if selected_values:
            # Normaliser les valeurs sélectionnées pour la comparaison
            normalized_selected = (str(selected_values[0]), str(selected_values[1]), str(selected_values[2]))
            found = False
            for item, values in items:
                if values == normalized_selected:
                    self.folder_tree.selection_set(item)
                    self.current_selected_folder = values
                    self.folder_tree.see(item)  # S'assurer que l'élément est visible
                    found = True
                    print(f"After refresh: Restored selection to IID = {item}, values = {values}")
                    break
            if not found:
                print(f"After refresh: Could not restore selection, no matching values found for {normalized_selected}")
                # Si la sélection n'est pas trouvée, sélectionner le premier élément par défaut
                if items:
                    first_item, first_values = items[0]
                    self.folder_tree.selection_set(first_item)
                    self.current_selected_folder = first_values
                    self.folder_tree.see(first_item)
                    print(f"After refresh: Selected first item as fallback: IID = {first_item}, values = {first_values}")
        else:
            print("After refresh: No selection to restore.")

    def filter_folders(self, *args):
        self.refresh_folder_list()

    def load_files(self, event):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        selected = self.folder_tree.selection()
        if not selected:
            self.current_folder = None
            print("Load files: No folder selected.")
            return
        self.current_folder = self.folder_tree.item(selected[0])["values"]
        year, category, project = self.current_folder
        query = "SELECT id, title FROM library WHERE year=? AND category=? AND project=? AND file_path != ''"
        self.cursor.execute(query, (year, category, project))
        for row in self.cursor.fetchall():
            self.file_tree.insert("", tk.END, values=row)
        print(f"Load files: Loaded files for {year}/{category}/{project}")

    def filter_files(self, event=None):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        if not self.current_folder:
            return
        search_term = self.search_var.get().lower()
        year, category, project = self.current_folder
        query = '''SELECT id, title FROM library 
                   WHERE year=? AND category=? AND project=? AND file_path != ''
                   AND LOWER(title) LIKE ?'''
        self.cursor.execute(query, (year, category, project, f"%{search_term}%"))
        for row in self.cursor.fetchall():
            self.file_tree.insert("", tk.END, values=row)