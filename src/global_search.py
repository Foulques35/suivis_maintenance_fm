import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import platform

class GlobalSearch:
    """
    Crée un onglet de recherche global qui interroge la base de données des tâches
    et la base de données de la bibliothèque.
    """
    def __init__(self, parent, conn_tasks, conn_library, library_manager):
        """
        Initialise l'onglet de recherche globale.

        Args:
            parent (tk.Widget): Le widget parent (généralement un onglet d'un Notebook).
            conn_tasks (sqlite3.Connection): La connexion à la base de données des tâches (tasks.db).
            conn_library (sqlite3.Connection): La connexion à la base de données de la bibliothèque (library.db).
            library_manager (LibraryManager): Une instance du LibraryManager pour ouvrir les fichiers.
        """
        self.parent = parent
        self.conn_tasks = conn_tasks
        self.conn_library = conn_library
        self.cursor_tasks = self.conn_tasks.cursor()
        self.cursor_library = self.conn_library.cursor()
        self.library_manager = library_manager

        # --- Interface Utilisateur ---
        
        # Panneau principal divisé en deux (recherche et détails)
        self.main_pane = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Cadre de gauche : Recherche et Résultats ---
        results_frame = ttk.Frame(self.main_pane, padding=5)
        self.main_pane.add(results_frame, weight=2)

        # Cadre pour la barre de recherche
        search_frame = ttk.Frame(results_frame)
        search_frame.pack(fill="x", pady=5)

        ttk.Label(search_frame, text="Rechercher (plusieurs mots possibles) :").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.perform_search) # Lance la recherche à chaque frappe

        # Arborescence pour afficher les résultats
        self.results_tree = ttk.Treeview(results_frame, columns=("Type", "Nom", "Détail"), show="headings")
        self.results_tree.heading("Type", text="Type")
        self.results_tree.heading("Nom", text="Nom/Titre")
        self.results_tree.heading("Détail", text="Échéance / Projet")
        
        self.results_tree.column("Type", width=100, anchor="w")
        self.results_tree.column("Nom", width=250, anchor="w")
        self.results_tree.column("Détail", width=200, anchor="w")
        
        self.results_tree.pack(fill="both", expand=True, pady=5)
        self.results_tree.bind("<<TreeviewSelect>>", self.show_details)

        # --- Cadre de droite : Panneau de détails ---
        self.details_frame = ttk.LabelFrame(self.main_pane, text="Détails", padding=10)
        self.main_pane.add(self.details_frame, weight=1)
        
        self.details_text = tk.Text(self.details_frame, wrap="word", height=10, state="disabled", font=("Arial", 10))
        self.details_text.pack(fill="both", expand=True, pady=(0, 5))
        
        button_container = ttk.Frame(self.details_frame)
        button_container.pack(pady=5)

        self.open_file_button = ttk.Button(button_container, text="Ouvrir le fichier", command=self.open_selected_file, state="disabled")
        self.open_file_button.pack(side="left", padx=5)

        self.open_location_button = ttk.Button(button_container, text="Ouvrir l'emplacement", command=self.open_selected_file_location, state="disabled")
        self.open_location_button.pack(side="left", padx=5)

        self.current_selected_item = None

    def perform_search(self, event=None):
        """
        Exécute la recherche dans les deux bases de données et met à jour l'arborescence.
        Prend en charge plusieurs mots-clés.
        """
        search_terms = self.search_var.get().strip().lower().split()

        for i in self.results_tree.get_children():
            self.results_tree.delete(i)

        if not search_terms:
            return

        tasks_parent = self.results_tree.insert("", "end", text="Tâches", values=("--- TÂCHES ---", "", ""), open=True)
        library_parent = self.results_tree.insert("", "end", text="Bibliothèque", values=("--- BIBLIOTHÈQUE ---", "", ""), open=True)

        # --- Recherche dans les tâches ---
        try:
            task_conditions = " AND ".join(["(LOWER(title) LIKE ? OR LOWER(description) LIKE ?)" for _ in search_terms])
            query_tasks = f"SELECT id, title, due_date, description FROM tasks WHERE {task_conditions}"
            
            task_params = []
            for term in search_terms:
                task_params.extend([f'%{term}%', f'%{term}%'])
            
            self.cursor_tasks.execute(query_tasks, tuple(task_params))
            tasks = self.cursor_tasks.fetchall()

            for task in tasks:
                task_id, title, due_date, description = task
                self.results_tree.insert(tasks_parent, "end", values=("Tâche", title, f"Échéance: {due_date}"), tags=("task", task_id))

        except Exception as e:
            self.results_tree.insert(tasks_parent, "end", values=("Erreur", str(e), ""))

        # --- Recherche dans la bibliothèque ---
        try:
            lib_conditions = " AND ".join(["(LOWER(title) LIKE ? OR LOWER(project) LIKE ? OR LOWER(notes) LIKE ?)" for _ in search_terms])
            query_library = f"SELECT id, title, project, category, year FROM library WHERE file_path != '' AND ({lib_conditions})"
            
            lib_params = []
            for term in search_terms:
                lib_params.extend([f'%{term}%', f'%{term}%', f'%{term}%'])
                
            self.cursor_library.execute(query_library, tuple(lib_params))
            files = self.cursor_library.fetchall()

            for file in files:
                file_id, title, project, category, year = file
                detail_text = f"Projet: {project} ({category} - {year})"
                self.results_tree.insert(library_parent, "end", values=("Fichier", title, detail_text), tags=("file", file_id))

        except Exception as e:
            self.results_tree.insert(library_parent, "end", values=("Erreur", str(e), ""))

    def show_details(self, event=None):
        """
        Affiche les détails de l'élément sélectionné dans le panneau de droite.
        """
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.open_file_button.config(state="disabled")
        self.open_location_button.config(state="disabled")
        self.current_selected_item = None

        selected_items = self.results_tree.selection()
        if not selected_items:
            self.details_text.config(state="disabled")
            return

        selected_item = selected_items[0]
        tags = self.results_tree.item(selected_item, "tags")

        if not tags or len(tags) < 2:
            self.details_text.config(state="disabled")
            return

        item_type = tags[0]
        item_id = int(tags[1])
        self.current_selected_item = (item_type, item_id)

        details = ""
        if item_type == "task":
            try:
                self.cursor_tasks.execute("SELECT * FROM tasks WHERE id=?", (item_id,))
                task = self.cursor_tasks.fetchone()
                if task:
                    task_id, title, desc, due_date, priority, status, recurrence = task
                    details += f"Titre: {title}\n"
                    details += f"Échéance: {due_date}\n"
                    details += f"Priorité: {priority}\n"
                    details += f"Statut: {status}\n"
                    details += f"Récurrence: {recurrence}\n\n"
                    details += f"Description:\n{'-'*20}\n{desc}"
            except Exception as e:
                details = f"Erreur lors de la récupération des détails de la tâche : {e}"

        elif item_type == "file":
            try:
                self.cursor_library.execute("SELECT * FROM library WHERE id=?", (item_id,))
                file_data = self.cursor_library.fetchone()
                if file_data:
                    (file_id, title, year, category, archives, project, site, 
                     nomenclature, emetteur, objet, version, file_path, notes) = file_data
                    details += f"Titre: {title}\n"
                    details += f"Projet: {project}\n"
                    details += f"Catégorie: {category} ({year})\n"
                    if archives:
                        details += f"Archive: {archives}\n"
                    details += f"Chemin: {file_path}\n\n"
                    details += f"Notes:\n{'-'*20}\n{notes}"
                    self.open_file_button.config(state="normal")
                    self.open_location_button.config(state="normal")
            except Exception as e:
                details = f"Erreur lors de la récupération des détails du fichier : {e}"

        self.details_text.insert("1.0", details)
        self.details_text.config(state="disabled")

    def open_selected_file(self):
        """
        Ouvre le fichier sélectionné en utilisant la méthode du LibraryManager.
        """
        if not self.current_selected_item or self.current_selected_item[0] != 'file':
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un fichier à ouvrir.")
            return

        file_id = self.current_selected_item[1]
        
        # Astuce pour réutiliser le code de library_manager sans dupliquer la logique
        class MockFileTree:
            def selection(self):
                return ("item",)
            def item(self, item_id):
                return {"values": [file_id]}
        
        original_tree = self.library_manager.file_tree
        self.library_manager.file_tree = MockFileTree()
        try:
            self.library_manager.open_file()
        finally:
            self.library_manager.file_tree = original_tree

    def open_selected_file_location(self):
        """
        Ouvre l'emplacement du fichier sélectionné dans l'explorateur de fichiers.
        """
        if not self.current_selected_item or self.current_selected_item[0] != 'file':
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un fichier.")
            return

        file_id = self.current_selected_item[1]

        try:
            self.cursor_library.execute("SELECT file_path FROM library WHERE id=?", (file_id,))
            result = self.cursor_library.fetchone()
            if not result or not result[0]:
                messagebox.showerror("Erreur", "Chemin du fichier non trouvé dans la bibliothèque.")
                return

            relative_path = result[0]
            file_path = os.path.normpath(os.path.join(self.library_manager.files_dir, relative_path))

            if not os.path.exists(file_path):
                messagebox.showerror("Erreur", f"Le fichier n'existe plus à l'emplacement : {file_path}")
                return

            folder_path = os.path.dirname(file_path)

            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", folder_path])
            else:
                subprocess.run(["xdg-open", folder_path])

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'emplacement du fichier : {e}")