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
        self.files_dir = os.path.normpath(os.path.join(os.path.dirname(sys.argv[0]), "bibliotheque"))
        os.makedirs(self.files_dir, exist_ok=True)
        self.nomenclatures_file = os.path.normpath(os.path.join(os.path.dirname(sys.argv[0]), "nomenclatures.json"))
        self.sites_file = os.path.normpath(os.path.join(os.path.dirname(sys.argv[0]), "sites.json"))
        self.init_nomenclatures_file()
        self.init_sites_file()
        self.init_db()
        self.year_filter_var = tk.StringVar()
        self.category_filter_var = tk.StringVar()
        self.archives_filter_var = tk.StringVar()
        self.project_filter_var = tk.StringVar()
        self.sort_column_name = "year"
        self.sort_reverse = False
        self.sort_direction = {"year": False, "category": False, "archives": False, "project": False, "notes": False}
        self.all_folders = []
        self.all_files = []
        self.load_initial_data()
        style = ttk.Style()
        style.theme_use("alt")
        style.configure("Add.TButton", background="#90EE90", foreground="black")
        style.configure("Modify.TButton", background="#FFFFE0", foreground="black")
        style.configure("Clear.TButton", background="#ADD8E6", foreground="black")
        style.configure("Delete.TButton", background="#FF0000", foreground="#FFFFFF")
        style.configure("OddRow.Treeview", background="#F5F5F5")
        style.configure("EvenRow.Treeview", background="#FFFFFF")
        self.paned_window = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True, padx=10, pady=10)
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=3)
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
        self.year_filter_var.trace("w", self.on_filter_change)
        self.category_filter_var.trace("w", self.on_filter_change)
        self.archives_filter_var.trace("w", self.on_filter_change)
        self.project_filter_var.trace("w", self.on_filter_change)
        self.folder_tree = ttk.Treeview(left_frame, columns=("Year", "Category", "Archives", "Project", "Notes"), show="headings")
        self.folder_tree.heading("Year", text="Année", command=lambda: self.sort_column("year", self.sort_direction["year"]))
        self.folder_tree.heading("Category", text="Catégorie", command=lambda: self.sort_column("category", self.sort_direction["category"]))
        self.folder_tree.heading("Archives", text="Archives", command=lambda: self.sort_column("archives", self.sort_direction["archives"]))
        self.folder_tree.heading("Project", text="Projet", command=lambda: self.sort_column("project", self.sort_direction["project"]))
        self.folder_tree.heading("Notes", text="Notes", command=lambda: self.sort_column("notes", self.sort_direction["notes"]))
        self.folder_tree.column("Year", width=100)
        self.folder_tree.column("Category", width=150)
        self.folder_tree.column("Archives", width=150)
        self.folder_tree.column("Project", width=200)
        self.folder_tree.column("Notes", width=200)
        self.folder_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.folder_tree.bind("<<TreeviewSelect>>", self.load_folder_to_form)
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=1)
        folder_form_frame = ttk.LabelFrame(right_frame, text="Gestion des dossiers")
        folder_form_frame.pack(fill="x", pady=5)
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
        ttk.Button(folder_button_frame, text="Vider formulaire", style="Clear.TButton", command=self.clear_folder).pack(side="left", padx=5)
        ttk.Button(folder_button_frame, text="Supprimer anciens dossiers", style="Delete.TButton", command=self.delete_old_folders).pack(side="left", padx=5)
        ttk.Button(folder_button_frame, text="Supprimer dossier", style="Delete.TButton", command=self.delete_folder).pack(side="right", padx=5)
        ttk.Button(folder_button_frame, text="Supprimer catégorie", style="Delete.TButton", command=self.delete_category).pack(side="right", padx=5)
        file_form_frame = ttk.LabelFrame(right_frame, text="Gestion des pièces")
        file_form_frame.pack(fill="x", pady=5)
        self.keep_name_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(file_form_frame, text="Conserver le nom du fichier", variable=self.keep_name_var, command=self.toggle_file_fields).grid(row=0, column=0, columnspan=2, pady=2, sticky="w")
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
        ttk.Button(file_button_frame, text="Ouvrir pièce", style="Add.TButton", command=self.open_file).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Ouvrir l'emplacement", style="Add.TButton", command=self.open_file_explorer).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Modifier pièce", style="Modify.TButton", command=self.modify_file).pack(side="left", padx=15)
        ttk.Button(file_button_frame, text="Vider formulaire", style="Clear.TButton", command=self.clear_file_form).pack(side="left", padx=5)
        ttk.Button(file_button_frame, text="Supprimer pièce", style="Delete.TButton", command=self.delete_file).pack(side="right", padx=5)
        ttk.Button(file_button_frame, text="Vérifier chemins", style="Modify.TButton", command=self.verify_and_fix_file_paths).pack(side="right", padx=5)
        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill="x", pady=5)
        ttk.Label(search_frame, text="Rechercher pièces :").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_files)
        self.file_tree = ttk.Treeview(right_frame, columns=("ID", "Title"), show="headings")
        self.file_tree.heading("ID", text="ID")
        self.file_tree.heading("Title", text="Titre")
        self.file_tree.column("ID", width=50)
        self.file_tree.column("Title", width=450)
        self.file_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.file_tree.bind("<<TreeviewSelect>>", self.load_file_to_form)
        self.parent.bind("<Control-a>", lambda event: self.add_folder())
        self.parent.bind("<Control-o>", lambda event: self.open_file())
        self.current_file_id = None
        self.current_folder = None
        self.current_selected_folder = None
        self.toggle_file_fields()
        self.refresh_folder_list()

    def init_db(self):
        try:
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
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_year ON library (year)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON library (category)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_archives ON library (archives)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_project ON library (project)")
            self.conn.commit()
            self.migrate_file_paths()
        except sqlite3.Error as e:
            messagebox.showerror("Erreur", f"Échec de l'initialisation de la base de données : {str(e)}")

    def load_initial_data(self):
        try:
            self.cursor.execute("SELECT DISTINCT year, category, archives, project, notes FROM library WHERE file_path != '' OR title = '[Dossier]'")
            raw_folders = self.cursor.fetchall()
            self.all_folders = []
            for row in raw_folders:
                year = str(row[0]).strip() if row[0] is not None else ""
                category = str(row[1]).strip() if row[1] is not None else ""
                archives = str(row[2]).strip() if row[2] is not None else ""
                project = str(row[3]).strip() if row[3] is not None else ""
                notes = str(row[4]).strip() if row[4] is not None else ""
                self.all_folders.append((year, category, archives, project, notes))

            self.cursor.execute("SELECT id, title, year, category, archives, project FROM library WHERE file_path != ''")
            raw_files = self.cursor.fetchall()
            self.all_files = []
            for row in raw_files:
                file_id = row[0]
                title = str(row[1]).strip() if row[1] is not None else ""
                year = str(row[2]).strip() if row[2] is not None else ""
                category = str(row[3]).strip() if row[3] is not None else ""
                archives = str(row[4]).strip() if row[4] is not None else ""
                project = str(row[5]).strip() if row[5] is not None else ""
                self.all_files.append((file_id, title, year, category, archives, project))
        except sqlite3.Error as e:
            messagebox.showerror("Erreur", f"Échec du chargement des données initiales : {str(e)}")

    def init_nomenclatures_file(self):
        try:
            if not os.path.exists(self.nomenclatures_file):
                default_nomenclatures = [{"code": "DOC", "description": "Document général"}, {"code": "PLAN", "description": "Plan technique"}, {"code": "CTR", "description": "Contrat"}]
                with open(self.nomenclatures_file, "w", encoding="utf-8") as f:
                    json.dump(default_nomenclatures, f, indent=4)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'initialisation des nomenclatures : {str(e)}")

    def init_sites_file(self):
        try:
            if not os.path.exists(self.sites_file):
                default_sites = [{"code": "ALMA", "description": "Site Alma"}, {"code": "PARIS", "description": "Site Paris"}, {"code": "LYON", "description": "Site Lyon"}]
                with open(self.sites_file, "w", encoding="utf-8") as f:
                    json.dump(default_sites, f, indent=4)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'initialisation des sites : {str(e)}")

    def show_nomenclatures(self):
        try:
            window = tk.Toplevel(self.parent)
            window.title("Liste des nomenclatures")
            window.geometry("400x300")
            window.transient(self.parent)
            window.grab_set()
            with open(self.nomenclatures_file, "r", encoding="utf-8") as f:
                nomenclatures = json.load(f)
            search_frame = ttk.Frame(window)
            search_frame.pack(fill="x", padx=5, pady=5)
            ttk.Label(search_frame, text="Rechercher :").pack(side="left")
            search_var = tk.StringVar()
            ttk.Entry(search_frame, textvariable=search_var).pack(side="left", fill="x", expand=True, padx=5)
            tree = ttk.Treeview(window, columns=("Code", "Description"), show="headings")
            tree.heading("Code", text="Code")
            tree.heading("Description", text="Description")
            tree.column("Code", width=100)
            tree.column("Description", width=250)
            tree.pack(fill="both", expand=True, padx=5, pady=5)
            def filter_nomenclatures(*args):
                for item in tree.get_children():
                    tree.delete(item)
                for nomenclature in nomenclatures:
                    if search_var.get().lower() in nomenclature["code"].lower() or search_var.get().lower() in nomenclature["description"].lower():
                        tree.insert("", tk.END, values=(nomenclature["code"], nomenclature["description"]))
            for nomenclature in nomenclatures:
                tree.insert("", tk.END, values=(nomenclature["code"], nomenclature["description"]))
            search_var.trace("w", filter_nomenclatures)
            def apply_nomenclature():
                selected = tree.selection()
                if selected:
                    self.nomenclature_var.set(tree.item(selected[0])["values"][0])
                    window.destroy()
            ttk.Button(window, text="Appliquer", command=apply_nomenclature).pack(pady=5)
            ttk.Button(window, text="Fermer", command=window.destroy).pack(pady=5)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'affichage des nomenclatures : {str(e)}")

    def show_sites(self):
        try:
            window = tk.Toplevel(self.parent)
            window.title("Liste des sites")
            window.geometry("400x300")
            window.transient(self.parent)
            window.grab_set()
            with open(self.sites_file, "r", encoding="utf-8") as f:
                sites = json.load(f)
            search_frame = ttk.Frame(window)
            search_frame.pack(fill="x", padx=5, pady=5)
            ttk.Label(search_frame, text="Rechercher :").pack(side="left")
            search_var = tk.StringVar()
            ttk.Entry(search_frame, textvariable=search_var).pack(side="left", fill="x", expand=True, padx=5)
            tree = ttk.Treeview(window, columns=("Code", "Description"), show="headings")
            tree.heading("Code", text="Code")
            tree.heading("Description", text="Description")
            tree.column("Code", width=100)
            tree.column("Description", width=250)
            tree.pack(fill="both", expand=True, padx=5, pady=5)
            def filter_sites(*args):
                for item in tree.get_children():
                    tree.delete(item)
                for site in sites:
                    if search_var.get().lower() in site["code"].lower() or search_var.get().lower() in site["description"].lower():
                        tree.insert("", tk.END, values=(site["code"], site["description"]))
            for site in sites:
                tree.insert("", tk.END, values=(site["code"], site["description"]))
            search_var.trace("w", filter_sites)
            def apply_site():
                selected = tree.selection()
                if selected:
                    self.site_var.set(tree.item(selected[0])["values"][0])
                    window.destroy()
            ttk.Button(window, text="Appliquer", command=apply_site).pack(pady=5)
            ttk.Button(window, text="Fermer", command=window.destroy).pack(pady=5)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'affichage des sites : {str(e)}")

    def migrate_file_paths(self):
        try:
            self.cursor.execute("SELECT id, year, category, archives, project, title, file_path FROM library WHERE file_path != ''")
            for file_id, year, category, archives, project, title, file_path in self.cursor.fetchall():
                year = str(year).strip() or str(datetime.now().year)
                category = str(category).strip() or "Unknown"
                archives = str(archives).strip() if archives else ""
                project = str(project).strip() or "Unknown"
                title = str(title).strip()
                path_components = [year, category] + ([archives] if archives else []) + [project, title]
                expected_path = os.path.join(*path_components).replace('\\', '/')
                if file_path != expected_path:
                    self.cursor.execute("UPDATE library SET file_path = ? WHERE id = ?", (expected_path, file_id))
                    old_full_path = os.path.normpath(os.path.join(self.files_dir, file_path))
                    new_full_path = os.path.normpath(os.path.join(self.files_dir, expected_path))
                    if os.path.exists(old_full_path) and not os.path.exists(new_full_path):
                        os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
                        shutil.move(old_full_path, new_full_path)
            self.conn.commit()
        except (sqlite3.Error, OSError) as e:
            messagebox.showerror("Erreur", f"Échec de la migration des chemins : {str(e)}")

    def verify_and_fix_file_paths(self):
        try:
            if not messagebox.askyesno("Confirmation", "Voulez-vous vérifier et corriger les chemins et métadonnées ?"):
                return
            self.cursor.execute("SELECT id, year, category, archives, project, title, file_path FROM library WHERE file_path != ''")
            files = self.cursor.fetchall()
            corrected_paths = 0
            corrected_metadata = 0
            missing_files = 0
            files_to_remove = []

            for file_id, year, category, archives, project, title, file_path in files:
                db_year = str(year).strip() or str(datetime.now().year)
                db_category = str(category).strip() or "Unknown"
                db_archives = str(archives).strip() if archives else ""
                db_project = str(project).strip() or "Unknown"
                db_title = str(title).strip()
                db_file_path = str(file_path).strip().replace('\\', '/')

                path_components = [db_year, db_category] + ([db_archives] if db_archives else []) + [db_project, db_title]
                expected_path = os.path.join(*path_components).replace('\\', '/')
                expected_full_path = os.path.normpath(os.path.join(self.files_dir, expected_path))

                current_full_path = os.path.normpath(os.path.join(self.files_dir, db_file_path))
                if not os.path.exists(current_full_path):
                    missing_files += 1
                    files_to_remove.append(file_id)
                    continue

                path_parts = db_file_path.split('/')
                if len(path_parts) < (5 if db_archives else 4):
                    continue
                path_year = path_parts[0]
                path_category = path_parts[1]
                path_archives = path_parts[2] if db_archives else ""
                path_project = path_parts[-2]
                path_title = path_parts[-1]

                metadata_updated = False
                if db_year != path_year:
                    self.cursor.execute("UPDATE library SET year = ? WHERE id = ?", (path_year, file_id))
                    db_year = path_year
                    metadata_updated = True
                    corrected_metadata += 1
                if db_category != path_category:
                    self.cursor.execute("UPDATE library SET category = ? WHERE id = ?", (path_category, file_id))
                    db_category = path_category
                    metadata_updated = True
                    corrected_metadata += 1
                if db_archives != path_archives:
                    self.cursor.execute("UPDATE library SET archives = ? WHERE id = ?", (path_archives if path_archives else None, file_id))
                    db_archives = path_archives
                    metadata_updated = True
                    corrected_metadata += 1
                if db_project != path_project:
                    self.cursor.execute("UPDATE library SET project = ? WHERE id = ?", (path_project, file_id))
                    db_project = path_project
                    metadata_updated = True
                    corrected_metadata += 1
                if db_title != path_title:
                    self.cursor.execute("UPDATE library SET title = ? WHERE id = ?", (path_title, file_id))
                    db_title = path_title
                    metadata_updated = True
                    corrected_metadata += 1

                if metadata_updated:
                    path_components = [db_year, db_category] + ([db_archives] if db_archives else []) + [db_project, db_title]
                    expected_path = os.path.join(*path_components).replace('\\', '/')
                    expected_full_path = os.path.normpath(os.path.join(self.files_dir, expected_path))

                if db_file_path != expected_path:
                    self.cursor.execute("UPDATE library SET file_path = ? WHERE id = ?", (expected_path, file_id))
                    corrected_paths += 1
                    if os.path.exists(current_full_path) and not os.path.exists(expected_full_path):
                        os.makedirs(os.path.dirname(expected_full_path), exist_ok=True)
                        shutil.move(current_full_path, expected_full_path)

            if files_to_remove and messagebox.askyesno("Fichiers manquants", f"{len(files_to_remove)} fichiers sont manquants. Voulez-vous supprimer leurs entrées de la base de données ?"):
                for file_id in files_to_remove:
                    self.cursor.execute("DELETE FROM library WHERE id=?", (file_id,))
                self.conn.commit()
                self.load_initial_data()

            self.conn.commit()
            self.refresh_folder_list()
            messagebox.showinfo("Vérification terminée", f"Chemins corrigés: {corrected_paths}\nMétadonnées corrigées: {corrected_metadata}\nFichiers manquants: {missing_files}")
        except (sqlite3.Error, OSError) as e:
            messagebox.showerror("Erreur", f"Échec de la vérification des chemins : {str(e)}")

    def toggle_file_fields(self):
        try:
            state = "disabled" if self.keep_name_var.get() else "normal"
            self.site_entry.configure(state=state)
            self.nomenclature_entry.configure(state=state)
            self.emetteur_entry.configure(state=state)
            self.objet_entry.configure(state=state)
            self.version_entry.configure(state=state)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la bascule des champs : {str(e)}")

    def load_folder_to_form(self, event):
        try:
            selected = self.folder_tree.selection()
            if not selected:
                self.current_selected_folder = None
                self.clear_folder()
                self.load_files()
                return
            year, category, archives, project, notes = self.folder_tree.item(selected[0])["values"]
            self.current_selected_folder = (str(year).strip(), str(category).strip(), str(archives).strip(), str(project).strip(), str(notes).strip())
            self.folder_year_var.set(year)
            self.folder_category_var.set(category)
            self.folder_archives_var.set(archives if archives else "")
            self.folder_project_var.set(project)
            self.folder_notes_var.set(notes if notes else "")
            self.load_files()
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec du chargement du dossier : {str(e)}")

    def add_folder(self):
        try:
            year = self.folder_year_var.get().strip()
            category = self.folder_category_var.get().strip()
            archives = self.folder_archives_var.get().strip()
            project = self.folder_project_var.get().strip()
            notes = self.folder_notes_var.get().strip()
            if not all([year, category, project]):
                messagebox.showwarning("Erreur", "Année, Catégorie et Projet sont obligatoires.")
                return
            path_components = [self.files_dir, year, category] + ([archives] if archives else []) + [project]
            folder_path = os.path.normpath(os.path.join(*path_components))
            os.makedirs(folder_path, exist_ok=True)
            self.cursor.execute('''INSERT INTO library (title, year, category, archives, project, notes, file_path)
                                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                               ("[Dossier]", year, category, archives if archives else None, project, notes, ""))
            self.conn.commit()
            self.all_folders.append((year, category, archives if archives else "", project, notes if notes else ""))
            self.refresh_folder_list()
            self.clear_folder()
            messagebox.showinfo("Succès", "Dossier ajouté avec succès.")
        except (sqlite3.Error, OSError) as e:
            messagebox.showerror("Erreur", f"Échec de l'ajout du dossier : {str(e)}")

    def copy_folder(self, old_year, old_category, old_archives, old_project, new_year, new_category, new_archives, new_project, log_message):
        try:
            old_path_components = [self.files_dir, old_year, old_category]
            if old_archives:
                old_path_components.append(old_archives)
            old_path_components.append(old_project)
            old_folder_path = os.path.normpath(os.path.join(*old_path_components))

            new_path_components = [self.files_dir, new_year, new_category]
            if new_archives:
                new_path_components.append(new_archives)
            new_path_components.append(new_project)
            new_folder_path = os.path.normpath(os.path.join(*new_path_components))

            log_message(f"Étape 1 : Création du nouveau dossier {new_folder_path}")
            os.makedirs(new_folder_path, exist_ok=True)
            log_message(f"Dossier créé : {new_folder_path}")

            log_message("Étape 2 : Mise à jour des chemins dans la base de données...")
            self.cursor.execute("SELECT id, file_path FROM library WHERE year=? AND category=? AND (archives=? OR (archives IS NULL AND ?='')) AND project=? AND file_path != ''",
                               (old_year, old_category, old_archives, old_archives, old_project))
            files_to_update = self.cursor.fetchall()
            updated_files = []

            for file_id, file_path in files_to_update:
                if not file_path:
                    log_message(f"Fichier ID {file_id} a un file_path vide, ignoré.")
                    continue

                old_full_path = os.path.normpath(os.path.join(self.files_dir, file_path))
                if not os.path.exists(old_full_path):
                    log_message(f"Fichier ID {file_id} manquant sur le disque : {old_full_path}, ignoré.")
                    continue

                file_name = os.path.basename(file_path)
                new_path_components_for_file = [new_year, new_category] + ([new_archives] if new_archives else []) + [new_project, file_name]
                new_relative_path = os.path.join(*new_path_components_for_file).replace('\\', '/')
                new_full_path = os.path.normpath(os.path.join(self.files_dir, new_relative_path))

                if os.path.exists(new_full_path):
                    log_message(f"Le fichier {new_relative_path} existe déjà à la destination. Ignoré.")
                    continue

                os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
                shutil.move(old_full_path, new_full_path)
                if not os.path.exists(new_full_path):
                    log_message(f"Échec du déplacement du fichier ID {file_id} vers {new_full_path}")
                    continue
                log_message(f"Fichier déplacé : {new_full_path}")

                self.cursor.execute('''UPDATE library SET year=?, category=?, archives=?, project=?, file_path=?
                                    WHERE id=?''',
                                   (new_year, new_category, new_archives if new_archives else None, new_project, new_relative_path, file_id))
                updated_files.append(file_id)
                log_message(f"Chemin mis à jour pour le fichier ID {file_id} : {new_relative_path}")

            self.conn.commit()
            return old_folder_path, updated_files
        except (sqlite3.Error, OSError) as e:
            log_message(f"Erreur lors de la copie du dossier : {str(e)}")
            return False

    def delete_old_folders(self):
        try:
            log_window = tk.Toplevel(self.parent)
            log_window.title("Suppression des anciens dossiers")
            log_window.geometry("500x400")
            log_window.transient(self.parent)
            log_window.grab_set()
            log_text = tk.Text(log_window, height=20, width=60)
            log_text.pack(pady=10, padx=10)

            def log_message(message):
                log_text.config(state='normal')
                log_text.insert(tk.END, message + "\n")
                log_text.see(tk.END)
                log_text.update()
                log_text.config(state='disabled')

            log_message("Recherche des dossiers orphelins...")

            self.cursor.execute("SELECT DISTINCT year, category, archives, project FROM library")
            active_folders = set()
            for row in self.cursor.fetchall():
                year = str(row[0]).strip()
                category = str(row[1]).strip()
                archives = str(row[2]).strip() if row[2] else ""
                project = str(row[3]).strip()
                active_folders.add((year, category, archives, project))

            orphan_folders = []
            for year_dir in os.listdir(self.files_dir):
                year_path = os.path.join(self.files_dir, year_dir)
                if not os.path.isdir(year_path):
                    continue
                for category_dir in os.listdir(year_path):
                    category_path = os.path.join(year_path, category_dir)
                    if not os.path.isdir(category_path):
                        continue
                    for dir_name in os.listdir(category_path):
                        dir_path = os.path.join(category_path, dir_name)
                        if not os.path.isdir(dir_path):
                            continue
                        archives = ""
                        project = dir_name
                        folder_tuple = (year_dir, category_dir, archives, project)
                        if folder_tuple not in active_folders:
                            has_referenced_files = False
                            for root, _, files in os.walk(dir_path):
                                for file in files:
                                    file_path = os.path.normpath(os.path.join(root, file))
                                    relative_path = os.path.relpath(file_path, self.files_dir).replace('\\', '/')
                                    self.cursor.execute("SELECT 1 FROM library WHERE file_path=?", (relative_path,))
                                    if self.cursor.fetchone():
                                        has_referenced_files = True
                                        break
                                if has_referenced_files:
                                    break
                            if not has_referenced_files:
                                orphan_folders.append(os.path.join(year_dir, category_dir, project))
                        for sub_dir in os.listdir(dir_path):
                            sub_dir_path = os.path.join(dir_path, sub_dir)
                            if not os.path.isdir(sub_dir_path):
                                continue
                            archives = dir_name
                            project = sub_dir
                            folder_tuple = (year_dir, category_dir, archives, project)
                            if folder_tuple not in active_folders:
                                has_referenced_files = False
                                for root, _, files in os.walk(sub_dir_path):
                                    for file in files:
                                        file_path = os.path.normpath(os.path.join(root, file))
                                        relative_path = os.path.relpath(file_path, self.files_dir).replace('\\', '/')
                                        self.cursor.execute("SELECT 1 FROM library WHERE file_path=?", (relative_path,))
                                        if self.cursor.fetchone():
                                            has_referenced_files = True
                                            break
                                    if has_referenced_files:
                                        break
                                if not has_referenced_files:
                                    orphan_folders.append(os.path.join(year_dir, category_dir, archives, project))

            if not orphan_folders:
                log_message("Aucun dossier orphelin trouvé.")
                ttk.Button(log_window, text="Fermer", command=log_window.destroy).pack(pady=5)
                return

            log_message(f"{len(orphan_folders)} dossiers orphelins trouvés :\n" + "\n".join(orphan_folders))
            if not messagebox.askyesno("Confirmation", f"Voulez-vous supprimer {len(orphan_folders)} dossiers orphelins ?"):
                log_message("Suppression annulée par l'utilisateur.")
                ttk.Button(log_window, text="Fermer", command=log_window.destroy).pack(pady=5)
                return

            deleted_count = 0
            for folder in orphan_folders:
                folder_path = os.path.normpath(os.path.join(self.files_dir, folder))
                if not os.path.exists(folder_path):
                    log_message(f"Dossier {folder_path} n'existe plus.")
                    continue

                try:
                    for root, _, files in os.walk(folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if not os.access(file_path, os.W_OK):
                                log_message(f"Erreur : Permissions insuffisantes pour {file_path}")
                                continue
                    shutil.rmtree(folder_path)
                    log_message(f"Dossier supprimé : {folder_path}")
                    deleted_count += 1
                except Exception as e:
                    log_message(f"Erreur lors de la suppression de {folder_path} : {str(e)}")

            for year_dir in os.listdir(self.files_dir):
                year_path = os.path.join(self.files_dir, year_dir)
                if not os.path.isdir(year_path):
                    continue
                for category_dir in os.listdir(year_path):
                    category_path = os.path.join(year_path, category_dir)
                    if not os.path.isdir(category_path):
                        continue
                    if not os.listdir(category_path):
                        try:
                            shutil.rmtree(category_path)
                            log_message(f"Dossier vide supprimé : {category_path}")
                            deleted_count += 1
                        except Exception as e:
                            log_message(f"Erreur lors de la suppression de {category_path} : {str(e)}")
                if not os.listdir(year_path):
                    try:
                        shutil.rmtree(year_path)
                        log_message(f"Dossier vide supprimé : {year_path}")
                        deleted_count += 1
                    except Exception as e:
                        log_message(f"Erreur lors de la suppression de {year_path} : {str(e)}")

            log_message(f"Suppression terminée : {deleted_count} dossiers supprimés.")
            ttk.Button(log_window, text="Valider", command=log_window.destroy).pack(pady=5)
        except Exception as e:
            log_message(f"Erreur lors de la suppression des dossiers orphelins : {str(e)}")
            ttk.Button(log_window, text="Fermer", command=log_window.destroy).pack(pady=5)

    def modify_folder(self):
        try:
            if not self.current_selected_folder:
                messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier à modifier.")
                return
            new_year = self.folder_year_var.get().strip()
            new_category = self.folder_category_var.get().strip()
            new_archives = self.folder_archives_var.get().strip()
            new_project = self.folder_project_var.get().strip()
            new_notes = self.folder_notes_var.get().strip()

            if not all([new_year, new_category, new_project]):
                messagebox.showwarning("Erreur", "Année, Catégorie et Projet sont obligatoires.")
                return

            invalid_chars = '<>:"/\\|?*'
            for field, value in [("Année", new_year), ("Catégorie", new_category), ("Archives", new_archives), ("Projet", new_project)]:
                if any(char in value for char in invalid_chars):
                    messagebox.showwarning("Erreur", f"Le champ {field} contient des caractères invalides : {invalid_chars}")
                    return

            old_year, old_category, old_archives, old_project, old_notes = self.current_selected_folder
            old_archives = old_archives if old_archives else ""
            new_archives = new_archives if new_archives else ""

            if (old_year, old_category, old_archives, old_project, old_notes) == (new_year, new_category, new_archives, new_project, new_notes):
                messagebox.showinfo("Information", "Aucune modification détectée.")
                return

            if not messagebox.askyesno("Confirmation", "Voulez-vous vraiment modifier ce dossier ?"):
                return

            self.cursor.execute("SELECT 1 FROM library WHERE year=? AND category=? AND (archives=? OR (archives IS NULL AND ?='')) AND project=? AND (year != ? OR category != ? OR archives != ? OR project != ?)",
                               (new_year, new_category, new_archives, new_archives, new_project, old_year, old_category, old_archives if old_archives else "", old_project))
            if self.cursor.fetchone():
                messagebox.showerror("Erreur", "Ce dossier existe déjà.")
                return

            self.verify_and_fix_file_paths()

            log_window = tk.Toplevel(self.parent)
            log_window.title("Suivi de la modification")
            log_window.geometry("500x400")
            log_window.transient(self.parent)
            log_window.grab_set()
            log_text = tk.Text(log_window, height=20, width=60)
            log_text.pack(pady=10, padx=10)
            def log_message(message):
                log_text.config(state='normal')
                log_text.insert(tk.END, message + "\n")
                log_text.see(tk.END)
                log_text.update()
                log_text.config(state='disabled')
            log_message("Début de la modification du dossier...")

            path_changed = (old_year != new_year or old_category != new_category or 
                            old_archives != new_archives or old_project != new_project)
            old_folder_path = None
            updated_files = []

            if path_changed:
                result = self.copy_folder(old_year, old_category, old_archives, old_project, 
                                         new_year, new_category, new_archives, new_project, log_message)
                if not result:
                    raise Exception("Échec de la copie du dossier")
                old_folder_path, updated_files = result
            else:
                log_message("Aucun changement de chemin nécessaire (seules les notes ont été modifiées).")

            log_message("Mise à jour des métadonnées dans la base de données...")
            self.cursor.execute('''UPDATE library SET year=?, category=?, archives=?, project=?, notes=? 
                                WHERE year=? AND category=? AND (archives=? OR (archives IS NULL AND ?='')) AND project=? AND title=?''',
                               (new_year, new_category, new_archives if new_archives else None, new_project, 
                                new_notes if new_notes else "", old_year, old_category, 
                                old_archives if old_archives else None, old_archives, old_project, "[Dossier]"))
            log_message("Métadonnées du dossier mises à jour.")
            self.conn.commit()

            self.all_folders = [f for f in self.all_folders if f != (old_year, old_category, old_archives, old_project, old_notes)]
            self.all_folders.append((new_year, new_category, new_archives if new_archives else "", new_project, new_notes if new_notes else ""))
            for i, (file_id, title, f_year, f_category, f_archives, f_project) in enumerate(self.all_files):
                if (f_year, f_category, f_archives, f_project) == (old_year, old_category, old_archives, old_project):
                    self.all_files[i] = (file_id, title, new_year, new_category, new_archives if new_archives else "", new_project)

            if old_folder_path and updated_files:
                log_message(f"Ancien dossier {old_folder_path} conservé. Utilisez 'Supprimer anciens dossiers' pour le supprimer ultérieurement.")

            self.current_selected_folder = (new_year, new_category, new_archives if new_archives else "", new_project, new_notes if new_notes else "")
            self.current_folder = self.current_selected_folder
            self.refresh_folder_list()
            self.clear_folder()
            self.load_files()
            log_message("Modification terminée avec succès !")
            ttk.Button(log_window, text="Valider", command=log_window.destroy).pack(pady=5)
        except Exception as e:
            log_message(f"Erreur lors de la modification : {str(e)}")
            self.conn.rollback()
            messagebox.showerror("Erreur", f"Échec de la modification : {str(e)}")
            ttk.Button(log_window, text="Fermer", command=log_window.destroy).pack(pady=5)

    def delete_folder(self):
        try:
            selected = self.folder_tree.selection()
            if not selected:
                messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier à supprimer.")
                return
            year, category, archives, project, notes = self.folder_tree.item(selected[0])["values"]
            year = str(year).strip()
            category = str(category).strip()
            archives = str(archives).strip()
            project = str(project).strip()
            notes = str(notes).strip()
            num_files = sum(1 for f in self.all_files if f[2].lower() == year.lower() and f[3].lower() == category.lower() and f[4].lower() == archives.lower() and f[5].lower() == project.lower())
            if not messagebox.askyesno("Confirmation", f"Supprimer le dossier {year}/{category}/{archives}/{project} et ses {num_files} pièce(s) ?"):
                return
            path_components = [self.files_dir, year, category] + ([archives] if archives else []) + [project]
            folder_path = os.path.normpath(os.path.join(*path_components))
            self.cursor.execute("SELECT file_path FROM library WHERE year=? AND category=? AND (archives=? OR archives IS NULL) AND project=?", 
                               (year, category, archives if archives else None, project))
            for row in self.cursor.fetchall():
                file_path = row[0]
                if file_path:
                    full_path = os.path.normpath(os.path.join(self.files_dir, file_path))
                    if os.path.exists(full_path):
                        try:
                            os.remove(full_path)
                        except OSError as e:
                            messagebox.showerror("Erreur", f"Impossible de supprimer un fichier dans le dossier : {str(e)}")
                            return
            if os.path.exists(folder_path):
                try:
                    shutil.rmtree(folder_path)
                except OSError as e:
                    messagebox.showerror("Erreur", f"Impossible de supprimer le dossier : {str(e)}")
                    return
            self.cursor.execute("DELETE FROM library WHERE year=? AND category=? AND (archives=? OR archives IS NULL) AND project=?", 
                               (year, category, archives if archives else None, project))
            self.conn.commit()
            self.all_folders = [f for f in self.all_folders if f != (year, category, archives, project, notes)]
            self.all_files = [f for f in self.all_files if not (f[2].lower() == year.lower() and f[3].lower() == category.lower() and f[4].lower() == archives.lower() and f[5].lower() == project.lower())]
            self.cursor.execute("SELECT 1 FROM library WHERE category=?", (category,))
            if not self.cursor.fetchone():
                for year_dir in os.listdir(self.files_dir):
                    category_path = os.path.normpath(os.path.join(self.files_dir, year_dir, category))
                    if os.path.exists(category_path):
                        try:
                            shutil.rmtree(category_path)
                        except OSError as e:
                            messagebox.showerror("Erreur", f"Impossible de supprimer la catégorie : {str(e)}")
            self.refresh_folder_list()
            self.clear_folder()
            self.load_files()
            messagebox.showinfo("Succès", "Dossier supprimé avec succès.")
        except (sqlite3.Error, OSError) as e:
            messagebox.showerror("Erreur", f"Échec de la suppression du dossier : {str(e)}")

    def delete_category(self):
        try:
            if not self.current_selected_folder:
                messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier pour supprimer sa catégorie.")
                return
            _, category, _, _, _ = self.current_selected_folder
            category = str(category).strip()
            num_folders = sum(1 for f in self.all_folders if f[1].lower() == category.lower())
            num_files = sum(1 for f in self.all_files if f[3].lower() == category.lower())
            if not messagebox.askyesno("Confirmation", f"Supprimer la catégorie '{category}' ? Cela supprimera {num_folders} dossier(s) et {num_files} pièce(s)."):
                return
            self.cursor.execute("SELECT DISTINCT year, archives, project FROM library WHERE category=?", (category,))
            for year, archives, project in self.cursor.fetchall():
                year = str(year).strip()
                archives = str(archives).strip() if archives else ""
                project = str(project).strip()
                path_components = [self.files_dir, year, category] + ([archives] if archives else []) + [project]
                folder_path = os.path.normpath(os.path.join(*path_components))
                self.cursor.execute("SELECT file_path FROM library WHERE year=? AND category=? AND (archives=? OR archives IS NULL) AND project=?", 
                                   (year, category, archives if archives else None, project))
                for row in self.cursor.fetchall():
                    file_path = row[0]
                    if file_path:
                        full_path = os.path.normpath(os.path.join(self.files_dir, file_path))
                        if os.path.exists(full_path):
                            try:
                                os.remove(full_path)
                            except OSError as e:
                                messagebox.showerror("Erreur", f"Impossible de supprimer un fichier : {str(e)}")
                                return
                if os.path.exists(folder_path):
                    try:
                        shutil.rmtree(folder_path)
                    except OSError as e:
                        messagebox.showerror("Erreur", f"Impossible de supprimer le dossier : {str(e)}")
                        return
            for year_dir in os.listdir(self.files_dir):
                category_path = os.path.normpath(os.path.join(self.files_dir, year_dir, category))
                if os.path.exists(category_path):
                    try:
                        shutil.rmtree(category_path)
                    except OSError as e:
                        messagebox.showerror("Erreur", f"Impossible de supprimer la catégorie : {str(e)}")
                        return
            self.cursor.execute("DELETE FROM library WHERE category=?", (category,))
            self.conn.commit()
            self.all_folders = [f for f in self.all_folders if f[1].lower() != category.lower()]
            self.all_files = [f for f in self.all_files if f[3].lower() != category.lower()]
            self.refresh_folder_list()
            self.clear_folder()
            self.load_files()
            messagebox.showinfo("Succès", "Catégorie supprimée avec succès.")
        except (sqlite3.Error, OSError) as e:
            messagebox.showerror("Erreur", f"Échec de la suppression de la catégorie : {str(e)}")

    def add_file(self):
        try:
            selected = self.folder_tree.selection()
            if not selected:
                messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier.")
                return
            year, category, archives, project, notes = self.folder_tree.item(selected[0])["values"]
            year = str(year).strip()
            category = str(category).strip()
            archives = str(archives).strip() if archives else ""
            project = str(project).strip()
            notes = str(notes).strip() if notes else ""
            file_path = filedialog.askopenfilename(filetypes=[("Tous les fichiers", "*.*")], title="Sélectionner un fichier")
            if not file_path:
                return
            keep_name = self.keep_name_var.get()
            move_file = self.move_file_var.get()
            if move_file and not messagebox.askyesno("Confirmation", "Voulez-vous déplacer ce fichier ?"):
                return
            if keep_name:
                title = os.path.basename(file_path)
                site = None
                nomenclature = None
                emetteur = None
                objet = None
                version = None
            else:
                site = self.site_var.get().strip()
                nomenclature = self.nomenclature_var.get().strip()
                emetteur = self.emetteur_var.get().strip()
                objet = self.objet_var.get().strip()
                version = self.version_var.get().strip()
                if not all([site, nomenclature, emetteur, objet, version]):
                    messagebox.showwarning("Erreur", "Tous les champs de la pièce sont obligatoires.")
                    return
                title = f"{year}-{site}-{nomenclature}-{emetteur}-{objet}-{version}{os.path.splitext(file_path)[1]}"
            path_components = [year, category] + ([archives] if archives else []) + [project]
            relative_dest_dir = os.path.join(*path_components).replace('\\', '/')
            dest_dir = os.path.normpath(os.path.join(self.files_dir, relative_dest_dir))
            os.makedirs(dest_dir, exist_ok=True)
            relative_dest_path = os.path.join(relative_dest_dir, title).replace('\\', '/')
            dest_path = os.path.normpath(os.path.join(self.files_dir, relative_dest_path))
            if os.path.exists(dest_path):
                if not messagebox.askyesno("Confirmation", f"Le fichier {title} existe déjà. Voulez-vous l'écraser ?"):
                    return
            if move_file:
                shutil.move(file_path, dest_path)
            else:
                shutil.copy2(file_path, dest_path)
            self.cursor.execute('''INSERT INTO library (title, year, category, archives, project, site, nomenclature, emetteur, objet, version, file_path, notes)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (title, year, category, archives if archives else None, project, site, nomenclature, emetteur, objet, version, relative_dest_path, notes))
            self.conn.commit()
            self.cursor.execute("SELECT last_insert_rowid()")
            file_id = self.cursor.fetchone()[0]
            self.all_files.append((file_id, title, year, category, archives, project))
            self.current_selected_folder = (year, category, archives, project, notes)
            self.current_folder = self.current_selected_folder
            self.refresh_folder_list()
            for item in self.folder_tree.get_children():
                values = self.folder_tree.item(item)["values"]
                if (str(values[0]).strip().lower() == year.lower() and 
                    str(values[1]).strip().lower() == category.lower() and 
                    str(values[2]).strip().lower() == archives.lower() and 
                    str(values[3]).strip().lower() == project.lower()):
                    self.folder_tree.selection_set(item)
                    self.folder_tree.focus(item)
                    self.folder_tree.see(item)
                    break
            self.load_files()
            messagebox.showinfo("Succès", "Fichier ajouté avec succès.")
        except (sqlite3.Error, OSError) as e:
            messagebox.showerror("Erreur", f"Échec de l'ajout du fichier : {str(e)}")

    def modify_file(self):
        try:
            if not self.current_file_id:
                messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce à modifier.")
                return
            if not messagebox.askyesno("Confirmation", "Voulez-vous vraiment modifier cette pièce ?"):
                return
            selected = self.folder_tree.selection()
            if not selected:
                messagebox.showwarning("Erreur", "Veuillez sélectionner un dossier.")
                return

            year, category, archives, project, notes = self.folder_tree.item(selected[0])["values"]
            year = str(year).strip()
            category = str(category).strip()
            archives = str(archives).strip() if archives else ""
            project = str(project).strip()
            notes = str(notes).strip() if notes else ""

            keep_name = self.keep_name_var.get()
            if keep_name:
                self.cursor.execute("SELECT title FROM library WHERE id=?", (self.current_file_id,))
                title = self.cursor.fetchone()[0].strip()
                site = None
                nomenclature = None
                emetteur = None
                objet = None
                version = None
            else:
                site = self.site_var.get().strip()
                nomenclature = self.nomenclature_var.get().strip()
                emetteur = self.emetteur_var.get().strip()
                objet = self.objet_var.get().strip()
                version = self.version_var.get().strip()

                if not all([site, nomenclature, emetteur, objet, version]):
                    messagebox.showwarning("Erreur", "Tous les champs de la pièce sont obligatoires.")
                    return

                self.cursor.execute("SELECT file_path FROM library WHERE id=?", (self.current_file_id,))
                old_path = os.path.normpath(os.path.join(self.files_dir, self.cursor.fetchone()[0]))
                title = f"{year}-{site}-{nomenclature}-{emetteur}-{objet}-{version}{os.path.splitext(old_path)[1]}"

            self.cursor.execute("SELECT file_path FROM library WHERE id=?", (self.current_file_id,))
            old_relative_path = self.cursor.fetchone()[0].strip().replace('\\', '/')
            old_path = os.path.normpath(os.path.join(self.files_dir, old_relative_path))

            path_components = [year, category] + ([archives] if archives else []) + [project]
            relative_dest_dir = os.path.join(*path_components).replace('\\', '/')
            dest_dir = os.path.normpath(os.path.join(self.files_dir, relative_dest_dir))
            os.makedirs(dest_dir, exist_ok=True)
            new_relative_path = os.path.join(relative_dest_dir, title).replace('\\', '/')
            new_path = os.path.normpath(os.path.join(self.files_dir, new_relative_path))

            if new_path != old_path:
                if os.path.exists(new_path):
                    if not messagebox.askyesno("Confirmation", f"Le fichier {title} existe déjà. Voulez-vous l'écraser ?"):
                        return
                shutil.move(old_path, new_path)

            self.cursor.execute('''UPDATE library SET title=?, year=?, category=?, archives=?, project=?, site=?, nomenclature=?, emetteur=?, objet=?, version=?, file_path=?, notes=?
                                WHERE id=?''',
                               (title, year, category, archives if archives else None, project, site if site else None, 
                                nomenclature if nomenclature else None, emetteur if emetteur else None, 
                                objet if objet else None, version if version else None, new_relative_path, notes, self.current_file_id))
            self.conn.commit()

            for i, (file_id, _, f_year, f_category, f_archives, f_project) in enumerate(self.all_files):
                if file_id == self.current_file_id:
                    self.all_files[i] = (file_id, title, year, category, archives, project)
                    break

            self.current_selected_folder = (year, category, archives, project, notes)
            self.current_folder = self.current_selected_folder
            self.refresh_folder_list()
            self.load_files()
            messagebox.showinfo("Succès", "Fichier modifié avec succès.")
        except (sqlite3.Error, OSError) as e:
            messagebox.showerror("Erreur", f"Échec de la modification du fichier : {str(e)}")

    def delete_file(self):
        try:
            selected = self.file_tree.selection()
            if not selected:
                messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce à supprimer.")
                return
            file_id = self.file_tree.item(selected[0])["values"][0]
            self.cursor.execute("SELECT title, file_path FROM library WHERE id=?", (file_id,))
            file_title, file_path = self.cursor.fetchone()
            file_title = str(file_title).strip()
            file_path = str(file_path).strip().replace('\\', '/')
            if not messagebox.askyesno("Confirmation", f"Supprimer la pièce '{file_title}' ?"):
                return
            full_path = os.path.normpath(os.path.join(self.files_dir, file_path))
            if os.path.exists(full_path):
                os.remove(full_path)
            self.cursor.execute("DELETE FROM library WHERE id=?", (file_id,))
            self.conn.commit()
            self.all_files = [f for f in self.all_files if f[0] != file_id]
            self.refresh_folder_list()
            self.clear_file_form()
            self.load_files()
            messagebox.showinfo("Succès", "Fichier supprimé avec succès.")
        except (sqlite3.Error, OSError) as e:
            messagebox.showerror("Erreur", f"Échec de la suppression du fichier : {str(e)}")

    def open_file(self):
        try:
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
            year = str(year).strip()
            category = str(category).strip()
            archives = str(archives).strip() if archives else ""
            project = str(project).strip()
            title = str(title).strip()
            stored_file_path = str(stored_file_path).strip().replace('\\', '/')
            path_components = [year, category] + ([archives] if archives else []) + [project, title]
            expected_relative_path = os.path.join(*path_components).replace('\\', '/')
            expected_file_path = os.path.normpath(os.path.join(self.files_dir, expected_relative_path))
            file_path = expected_file_path if os.path.exists(expected_file_path) else os.path.normpath(os.path.join(self.files_dir, stored_file_path))
            if not os.path.exists(file_path):
                messagebox.showerror("Erreur", f"Le fichier n'existe pas :\n{file_path}")
                return
            if not os.access(file_path, os.R_OK):
                messagebox.showerror("Erreur", f"Permissions insuffisantes pour '{file_path}'.")
                return
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", file_path], check=True)
            else:
                subprocess.run(["open", file_path], check=True)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier : {str(e)}")

    def open_file_explorer(self):
        try:
            selected = self.file_tree.selection()
            if not selected:
                messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce.")
                return
            file_id = self.file_tree.item(selected[0])["values"][0]
            self.cursor.execute("SELECT year, category, archives, project, title, file_path FROM library WHERE id=?", (file_id,))
            result = self.cursor.fetchone()
            if not result:
                messagebox.showerror("Erreur", f"Aucune entrée trouvée pour l'ID {file_id}.")
                return
            year, category, archives, project, title, stored_file_path = result
            year = str(year).strip()
            category = str(category).strip()
            archives = str(archives).strip() if archives else ""
            project = str(project).strip()
            title = str(title).strip()
            stored_file_path = str(stored_file_path).strip().replace('\\', '/')
            path_components = [year, category] + ([archives] if archives else []) + [project, title]
            expected_relative_path = os.path.join(*path_components).replace('\\', '/')
            expected_file_path = os.path.normpath(os.path.join(self.files_dir, expected_relative_path))
            file_path = expected_file_path if os.path.exists(expected_file_path) else os.path.normpath(os.path.join(self.files_dir, stored_file_path))
            if not os.path.exists(file_path):
                messagebox.showerror("Erreur", f"Le fichier n'existe pas :\n{file_path}")
                return
            folder_path = os.path.dirname(file_path)
            if platform.system() == "Windows":
                subprocess.run(["explorer", folder_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", folder_path])
            else:
                subprocess.run(["open", folder_path])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'explorateur : {str(e)}")

    def load_file_to_form(self, event):
        try:
            selected = self.file_tree.selection()
            if not selected:
                return
            file_id = self.file_tree.item(selected[0])["values"][0]
            self.current_file_id = file_id
            self.cursor.execute("SELECT title, site, nomenclature, emetteur, objet, version FROM library WHERE id=?", (file_id,))
            result = self.cursor.fetchone()
            if result:
                title, site, nomenclature, emetteur, objet, version = result
                self.site_var.set(str(site).strip() if site else "")
                self.nomenclature_var.set(str(nomenclature).strip() if nomenclature else "")
                self.emetteur_var.set(str(emetteur).strip() if emetteur else "")
                self.objet_var.set(str(objet).strip() if objet else "")
                self.version_var.set(str(version).strip() if version else "")
                self.keep_name_var.set(not all([site, nomenclature, emetteur, objet, version]))
                self.toggle_file_fields()
        except sqlite3.Error as e:
            messagebox.showerror("Erreur", f"Échec du chargement du fichier : {str(e)}")

    def clear_folder(self):
        try:
            self.current_selected_folder = None
            self.folder_year_var.set(str(datetime.now().year))
            self.folder_category_var.set("")
            self.folder_archives_var.set("")
            self.folder_project_var.set("")
            self.folder_notes_var.set("")
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec du vidage du formulaire : {str(e)}")

    def clear_file_form(self):
        try:
            self.current_file_id = None
            self.site_var.set("")
            self.nomenclature_var.set("")
            self.emetteur_var.set("")
            self.objet_var.set("")
            self.version_var.set("V1")
            self.keep_name_var.set(False)
            self.move_file_var.set(False)
            self.toggle_file_fields()
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec du vidage du formulaire : {str(e)}")

    def sort_column(self, col, reverse):
        try:
            if col not in self.sort_direction:
                raise ValueError(f"Colonne invalide pour le tri : {col}")
            self.sort_column_name = col
            self.sort_reverse = reverse
            self.sort_direction[col] = not reverse
            self.refresh_folder_list()
            self.folder_tree.heading(col, command=lambda: self.sort_column(col, not reverse))
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec du tri des colonnes : {str(e)}")

    def refresh_folder_list(self):
        try:
            selected = self.folder_tree.selection()
            selected_values = None
            if selected:
                selected_values = self.folder_tree.item(selected[0])["values"]
            year_filter = self.year_filter_var.get().strip().lower()
            category_filter = self.category_filter_var.get().strip().lower()
            archives_filter = self.archives_filter_var.get().strip().lower()
            project_filter = self.project_filter_var.get().strip().lower()
            filtered_folders = self.all_folders
            if year_filter:
                filtered_folders = [
                    row for row in filtered_folders
                    if (year_filter in row[0].lower() or
                        year_filter in row[1].lower() or
                        year_filter in row[2].lower() or
                        year_filter in row[3].lower() or
                        year_filter in row[4].lower())
                ]
            if category_filter:
                filtered_folders = [row for row in filtered_folders if category_filter in row[1].lower()]
            if archives_filter:
                filtered_folders = [row for row in filtered_folders if archives_filter in row[2].lower()]
            if project_filter:
                filtered_folders = [row for row in filtered_folders if project_filter in row[3].lower()]
            col_index = {"year": 0, "category": 1, "archives": 2, "project": 3, "notes": 4}
            sort_index = col_index[self.sort_column_name]
            for row in filtered_folders:
                if len(row) != 5:
                    raise ValueError(f"Donnée invalide dans filtered_folders : {row}")
                if not all(isinstance(item, str) for item in row):
                    raise ValueError(f"Donnée non-string dans filtered_folders : {row}")
            filtered_folders.sort(key=lambda x: x[sort_index].lower(), reverse=self.sort_reverse)
            for item in self.folder_tree.get_children():
                self.folder_tree.delete(item)
            items = []
            for index, row in enumerate(filtered_folders):
                tag = "OddRow" if index % 2 else "EvenRow"
                item = self.folder_tree.insert("", tk.END, values=row, tags=(tag,))
                items.append((item, row))
            if selected_values and self.current_selected_folder:
                normalized_selected = (
                    str(self.current_selected_folder[0]).strip(),
                    str(self.current_selected_folder[1]).strip(),
                    str(self.current_selected_folder[2]).strip(),
                    str(self.current_selected_folder[3]).strip(),
                    str(self.current_selected_folder[4]).strip()
                )
                for item, values in items:
                    if (values[0].lower() == normalized_selected[0].lower() and
                        values[1].lower() == normalized_selected[1].lower() and
                        values[2].lower() == normalized_selected[2].lower() and
                        values[3].lower() == normalized_selected[3].lower()):
                        self.folder_tree.selection_set(item)
                        self.folder_tree.see(item)
                        break
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'actualisation de la liste des dossiers : {str(e)}")

    def on_filter_change(self, *args):
        try:
            self.refresh_folder_list()
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec du filtrage : {str(e)}")

    def load_files(self):
        try:
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
            if not self.current_selected_folder:
                self.current_folder = None
                return
            self.current_folder = self.current_selected_folder
            year, category, archives, project, notes = self.current_folder
            year = str(year).strip()
            category = str(category).strip()
            archives = str(archives).strip()
            project = str(project).strip()
            matching_files = [
                (file_id, title) for file_id, title, f_year, f_category, f_archives, f_project in self.all_files
                if f_year.lower() == year.lower() and 
                   f_category.lower() == category.lower() and 
                   f_archives.lower() == archives.lower() and 
                   f_project.lower() == project.lower()
            ]
            for index, (file_id, title) in enumerate(matching_files):
                tag = "OddRow" if index % 2 else "EvenRow"
                self.file_tree.insert("", tk.END, values=(file_id, title), tags=(tag,))
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec du chargement des fichiers : {str(e)}")

    def filter_files(self, event=None):
        try:
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
            if not self.current_folder:
                return
            search_term = self.search_var.get().lower()
            year, category, archives, project, notes = self.current_folder
            year = str(year).strip()
            category = str(category).strip()
            archives = str(archives).strip()
            project = str(project).strip()
            matching_files = [
                (file_id, title) for file_id, title, f_year, f_category, f_archives, f_project in self.all_files
                if f_year.lower() == year.lower() and 
                   f_category.lower() == category.lower() and 
                   f_archives.lower() == archives.lower() and 
                   f_project.lower() == project.lower() and
                   search_term in title.lower()
            ]
            for index, (file_id, title) in enumerate(matching_files):
                tag = "OddRow" if index % 2 else "EvenRow"
                self.file_tree.insert("", tk.END, values=(file_id, title), tags=(tag,))
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec du filtrage des fichiers : {str(e)}")
