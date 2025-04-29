import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry, Calendar
import sqlite3
from datetime import datetime, timedelta
import os
import csv
import json
import subprocess
import platform

class TaskManager:
    def __init__(self, parent, conn, conn_library, library_manager):
        self.parent = parent
        self.conn = conn
        self.conn_library = conn_library  # Connexion à library.db
        self.cursor = conn.cursor()
        self.cursor_library = conn_library.cursor()  # Curseur pour library.db
        self.library_manager = library_manager  # Référence à LibraryManager
        self.init_db()

        # Charger la configuration
        self.config_file = os.path.join(os.path.dirname(__file__), "config_tasks.json")
        self.load_config()

        # Configurer les styles pour les boutons
        style = ttk.Style()
        style.configure("Create.TButton", background="#90EE90", foreground="black")  # Vert clair
        style.configure("Modify.TButton", background="#FFFFE0", foreground="black")  # Jaune clair
        style.configure("Delete.TButton", background="#FF0000", foreground="black")  # Rouge
        style.configure("Complete.TButton", background="#32CD32", foreground="black")  # Vert
        style.configure("Associate.TButton", background="#FFD700", foreground="black")  # Jaune
        style.configure("Open.TButton", background="#00CED1", foreground="black")  # Turquoise
        style.configure("Dissociate.TButton", background="#FF6347", foreground="black")  # Rouge tomate
        style.configure("MassDelete.TButton", background="#FF0000", foreground="black")  # Rouge pour la suppression en masse
        style.configure("AddSubtask.TButton", background="#90EE90", foreground="black")  # Vert clair
        style.configure("ToggleSubtask.TButton", background="#32CD32", foreground="black")  # Vert
        style.configure("DeleteSubtask.TButton", background="#FF6347", foreground="black")  # Rouge tomate
        style.configure("ModifySubtask.TButton", background="#FFFFE0", foreground="black")  # Jaune clair
        style.configure("Calendar.TButton", background="#ADD8E6", foreground="black")  # Bleu clair pour le bouton Vue Planning
        style.configure("Refresh.TButton", background="#ADD8E6", foreground="black")  # Bleu clair pour le bouton Actualiser
        # Styles pour lignes alternées
        style.configure("OddRow.Treeview", background="#F5F5F5")
        style.configure("EvenRow.Treeview", background="#FFFFFF")

        # Interface principale avec deux volets horizontaux
        self.main_frame = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Volet gauche : Liste des tâches
        self.tasks_frame = ttk.LabelFrame(self.main_frame, text="Liste des Tâches")
        self.main_frame.add(self.tasks_frame, weight=3)  # Augmenter la taille du Treeview

        # Filtres
        filter_frame = ttk.Frame(self.tasks_frame)
        filter_frame.pack(fill="x", pady=5)
        ttk.Label(filter_frame, text="Rechercher :").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filter_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_tasks)

        ttk.Label(filter_frame, text="Statut :").pack(side="left", padx=5)
        self.status_filter_var = tk.StringVar(value=self.status_filter)
        self.status_filter = ttk.Combobox(filter_frame, textvariable=self.status_filter_var, values=["Tous", "En cours", "Terminé"], state="readonly", width=15)
        self.status_filter.pack(side="left", padx=5)
        self.status_filter.bind("<<ComboboxSelected>>", self.save_status_filter)

        ttk.Label(filter_frame, text="Échéance :").pack(side="left", padx=5)
        self.due_filter_var = tk.StringVar(value="Toutes")
        self.due_filter = ttk.Combobox(filter_frame, textvariable=self.due_filter_var, values=["Toutes", "Aujourd'hui", "Cette semaine", "Ce mois"], state="readonly", width=15)
        self.due_filter.pack(side="left", padx=5)
        self.due_filter.bind("<<ComboboxSelected>>", self.filter_tasks)

        # Treeview pour les tâches avec sélection multiple
        self.task_tree = ttk.Treeview(self.tasks_frame, columns=("ID", "Title", "Due Date", "Priority", "Status", "Recurrence", "Progress"), show="headings", selectmode="extended")
        self.task_tree.heading("ID", text="ID", command=lambda: self.sort_column("ID", False))
        self.task_tree.heading("Title", text="Titre", command=lambda: self.sort_column("Title", False))
        self.task_tree.heading("Due Date", text="Échéance", command=lambda: self.sort_column("Due Date", False))
        self.task_tree.heading("Priority", text="Priorité", command=lambda: self.sort_column("Priority", False))
        self.task_tree.heading("Status", text="Statut", command=lambda: self.sort_column("Status", False))
        self.task_tree.heading("Recurrence", text="Récurrence", command=lambda: self.sort_column("Recurrence", False))
        self.task_tree.heading("Progress", text="% Terminé", command=lambda: self.sort_column("Progress", False))
        self.task_tree.column("ID", width=50, anchor="center")
        self.task_tree.column("Title", width=150)
        self.task_tree.column("Due Date", width=100, anchor="center")
        self.task_tree.column("Priority", width=80, anchor="center")
        self.task_tree.column("Status", width=100, anchor="center")
        self.task_tree.column("Recurrence", width=100, anchor="center")
        self.task_tree.column("Progress", width=80, anchor="center")
        self.task_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.task_tree.bind("<<TreeviewSelect>>", self.load_task_to_form)
        self.task_tree.tag_configure("urgent", background="#FF9999")  # Rouge clair
        self.task_tree.tag_configure("completed", background="#99FF99")  # Vert clair

        # Boutons d'exportation, de suppression en masse et de vue planning
        button_frame = ttk.Frame(self.tasks_frame)
        button_frame.pack(fill="x", pady=5)
        ttk.Button(button_frame, text="Exporter en CSV", command=self.export_to_csv).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Supprimer les tâches sélectionnées", style="MassDelete.TButton", command=self.delete_selected_tasks).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Vue Planning", style="Calendar.TButton", command=self.show_task_calendar).pack(side="left", padx=5)

        # Volet droit : Formulaire pour gérer les tâches
        self.form_frame = ttk.LabelFrame(self.main_frame, text="Gestion des Tâches")
        self.main_frame.add(self.form_frame, weight=1)  # Réduire la taille du formulaire

        # Grille pour le formulaire
        form_grid = ttk.Frame(self.form_frame)
        form_grid.pack(fill="x", padx=5, pady=5)

        ttk.Label(form_grid, text="Titre :").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(form_grid, textvariable=self.title_var)
        self.title_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        ttk.Label(form_grid, text="Description :").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.description_text = tk.Text(form_grid, height=4, width=30)
        self.description_text.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        ttk.Label(form_grid, text="Échéance :").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.due_date_var = tk.StringVar()
        self.due_date_entry = DateEntry(form_grid, textvariable=self.due_date_var, date_pattern="yyyy-mm-dd", width=12)
        self.due_date_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(form_grid, text="Priorité :").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.priority_var = tk.StringVar(value="Moyenne")
        self.priority_combobox = ttk.Combobox(form_grid, textvariable=self.priority_var, values=["Haute", "Moyenne", "Basse"], state="readonly")
        self.priority_combobox.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        ttk.Label(form_grid, text="Statut :").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.status_var = tk.StringVar(value="En cours")
        self.status_combobox = ttk.Combobox(form_grid, textvariable=self.status_var, values=["En cours", "Terminé"], state="readonly")
        self.status_combobox.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        ttk.Label(form_grid, text="Récurrence :").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.recurrence_var = tk.StringVar(value="Aucune")
        self.recurrence_combobox = ttk.Combobox(form_grid, textvariable=self.recurrence_var, values=["Aucune", "Quotidienne", "Hebdomadaire", "Mensuel", "Trimestrielle", "Semestrielle", "Annuelle"], state="readonly")
        self.recurrence_combobox.grid(row=5, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        # Cases à cocher pour week-end
        self.exclude_saturday_var = tk.BooleanVar(value=self.exclude_saturday)
        self.exclude_sunday_var = tk.BooleanVar(value=self.exclude_sunday)
        ttk.Checkbutton(form_grid, text="Exclure Samedi", variable=self.exclude_saturday_var, command=self.save_config).grid(row=6, column=1, padx=5, pady=5, sticky="w")
        ttk.Checkbutton(form_grid, text="Exclure Dimanche", variable=self.exclude_sunday_var, command=self.save_config).grid(row=6, column=2, padx=5, pady=5, sticky="w")

        buttons_frame = ttk.Frame(form_grid)
        buttons_frame.grid(row=7, column=0, columnspan=3, pady=10)
        self.create_btn = ttk.Button(buttons_frame, text="Créer", style="Create.TButton", command=self.create_task)
        self.create_btn.pack(side="left", padx=5)
        self.modify_btn = ttk.Button(buttons_frame, text="Modifier", style="Modify.TButton", command=self.modify_task, state="disabled")
        self.modify_btn.pack(side="left", padx=5)
        self.complete_btn = ttk.Button(buttons_frame, text="Terminé", style="Complete.TButton", command=self.mark_completed, state="disabled")
        self.complete_btn.pack(side="left", padx=5)
        self.associate_btn = ttk.Button(buttons_frame, text="Associer une pièce", style="Associate.TButton", command=self.associate_file, state="disabled")
        self.associate_btn.pack(side="left", padx=5)

        # Sous-tâches et barre de progression
        subtasks_frame = ttk.LabelFrame(self.form_frame, text="Sous-tâches")
        subtasks_frame.pack(fill="x", pady=5)

        self.subtask_tree = ttk.Treeview(subtasks_frame, columns=("ID", "Title", "Status"), show="headings")
        self.subtask_tree.heading("ID", text="ID")
        self.subtask_tree.heading("Title", text="Titre")
        self.subtask_tree.heading("Status", text="Statut")
        self.subtask_tree.column("ID", width=50)
        self.subtask_tree.column("Title", width=300)
        self.subtask_tree.column("Status", width=100)
        self.subtask_tree.pack(fill="both", expand=True, padx=5, pady=5)

        subtask_buttons_frame = ttk.Frame(subtasks_frame)
        subtask_buttons_frame.pack(fill="x", pady=5)
        self.add_subtask_btn = ttk.Button(subtask_buttons_frame, text="Ajouter une sous-tâche", style="AddSubtask.TButton", command=self.add_subtask, state="disabled")
        self.add_subtask_btn.pack(side="left", padx=5)
        self.toggle_subtask_btn = ttk.Button(subtask_buttons_frame, text="Marquer Terminé/En cours", style="ToggleSubtask.TButton", command=self.toggle_subtask_status, state="disabled")
        self.toggle_subtask_btn.pack(side="left", padx=5)
        self.modify_subtask_btn = ttk.Button(subtask_buttons_frame, text="Modifier", style="ModifySubtask.TButton", command=self.modify_subtask, state="disabled")
        self.modify_subtask_btn.pack(side="left", padx=5)
        self.delete_subtask_btn = ttk.Button(subtask_buttons_frame, text="Supprimer", style="DeleteSubtask.TButton", command=self.delete_subtask, state="disabled")
        self.delete_subtask_btn.pack(side="right", padx=(20, 5))

        # Barre de progression
        self.progress_label = ttk.Label(subtasks_frame, text="Progression: 0%")
        self.progress_label.pack(pady=2)
        self.progress_bar = ttk.Progressbar(subtasks_frame, length=200, mode="determinate")
        self.progress_bar.pack(pady=2)

        # Treeview pour afficher les pièces associées
        associated_frame = ttk.LabelFrame(self.form_frame, text="Pièces associées")
        associated_frame.pack(fill="x", pady=5)

        self.associated_tree = ttk.Treeview(associated_frame, columns=("ID", "Titre"), show="headings")
        self.associated_tree.heading("ID", text="ID")
        self.associated_tree.heading("Titre", text="Titre")
        self.associated_tree.column("ID", width=50)
        self.associated_tree.column("Titre", width=450)
        self.associated_tree.pack(fill="both", expand=True, padx=5, pady=5)

        associated_button_frame = ttk.Frame(associated_frame)
        associated_button_frame.pack(fill="x", pady=5)
        ttk.Button(associated_button_frame, text="Ouvrir pièce", style="Open.TButton", command=self.open_associated_file).pack(side="left", padx=5)
        ttk.Button(associated_button_frame, text="Dissocier pièce", style="Dissociate.TButton", command=self.dissociate_file).pack(side="left", padx=5)

        self.current_task_id = None
        self.sort_direction = {}
        self.calendar_window = None  # Pour suivre la fenêtre de la vue planning
        self.tasks_tree = None  # Pour le Treeview des tâches dans la vue planning
        self.subtasks_tree = None  # Pour le Treeview des sous-tâches dans la vue planning
        self.calendar = None  # Pour le calendrier dans la vue planning
        self.refresh_task_list()

    def init_db(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            priority TEXT DEFAULT 'Moyenne',
            status TEXT DEFAULT 'En cours',
            recurrence TEXT DEFAULT 'Aucune'
        )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'En cours',
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )""")
        self.cursor.execute("PRAGMA table_info(tasks)")
        columns = [info[1] for info in self.cursor.fetchall()]
        if 'priority' not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'Moyenne'")
        if 'recurrence' not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN recurrence TEXT DEFAULT 'Aucune'")
        self.cursor.execute("UPDATE tasks SET status='En cours' WHERE status='Reportée'")
        self.conn.commit()

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                self.exclude_saturday = config.get("tasks_exclude_saturday", False)
                self.exclude_sunday = config.get("tasks_exclude_sunday", False)
                self.status_filter = config.get("tasks_status_filter", "Tous")
                if self.status_filter not in ["Tous", "En cours", "Terminé"]:
                    self.status_filter = "Tous"
            else:
                self.exclude_saturday = False
                self.exclude_sunday = False
                self.status_filter = "Tous"
        except Exception:
            self.exclude_saturday = False
            self.exclude_sunday = False
            self.status_filter = "Tous"

    def save_config(self):
        try:
            config = {
                "tasks_exclude_saturday": self.exclude_saturday_var.get(),
                "tasks_exclude_sunday": self.exclude_sunday_var.get(),
                "tasks_status_filter": self.status_filter_var.get()
            }
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception:
            pass

    def save_status_filter(self, event=None):
        self.save_config()
        self.filter_tasks()

    def create_task(self):
        title = self.title_var.get()
        description = self.description_text.get("1.0", tk.END).strip()
        due_date = self.due_date_var.get()
        priority = self.priority_var.get()
        status = "En cours"
        recurrence = self.recurrence_var.get()

        if not title or not due_date:
            messagebox.showwarning("Erreur", "Le titre et la date d'échéance sont obligatoires !")
            return

        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Erreur", "La date d'échéance doit être au format YYYY-MM-DD !")
            return

        copy_subtasks = False
        copy_files = False
        if self.current_task_id:
            copy_window = tk.Toplevel(self.parent)
            copy_window.title("Copier les éléments")
            copy_window.geometry("300x150")
            copy_window.transient(self.parent)
            copy_window.grab_set()

            ttk.Label(copy_window, text="Copier les sous-tâches ?").pack(pady=5)
            copy_subtasks_var = tk.BooleanVar()
            ttk.Checkbutton(copy_window, variable=copy_subtasks_var).pack()

            ttk.Label(copy_window, text="Copier les pièces associées ?").pack(pady=5)
            copy_files_var = tk.BooleanVar()
            ttk.Checkbutton(copy_window, variable=copy_files_var).pack()

            def confirm():
                nonlocal copy_subtasks, copy_files
                copy_subtasks = copy_subtasks_var.get()
                copy_files = copy_files_var.get()
                copy_window.destroy()

            ttk.Button(copy_window, text="Confirmer", command=confirm).pack(pady=5)
            self.parent.wait_window(copy_window)

        self.cursor.execute("INSERT INTO tasks (title, description, due_date, priority, status, recurrence) VALUES (?, ?, ?, ?, ?, ?)",
                           (title, description, due_date, priority, status, recurrence))
        self.conn.commit()

        self.cursor.execute("SELECT last_insert_rowid()")
        new_task_id = self.cursor.fetchone()[0]

        if self.current_task_id and copy_subtasks:
            self.cursor.execute("SELECT title FROM subtasks WHERE task_id=?", (self.current_task_id,))
            subtasks = self.cursor.fetchall()
            for subtask in subtasks:
                subtask_title = subtask[0]
                self.cursor.execute("INSERT INTO subtasks (task_id, title, status) VALUES (?, ?, 'En cours')",
                                   (new_task_id, subtask_title))

        if self.current_task_id and copy_files:
            self.cursor_library.execute("SELECT file_id FROM task_file_link WHERE task_id=?", (self.current_task_id,))
            file_links = self.cursor_library.fetchall()
            for link in file_links:
                file_id = link[0]
                self.cursor_library.execute("INSERT INTO task_file_link (task_id, file_id) VALUES (?, ?)",
                                           (new_task_id, file_id))
            self.conn_library.commit()

        self.refresh_task_list()
        self.parent.after(100, self.refresh_calendar)

        for item in self.task_tree.get_children():
            if int(self.task_tree.item(item)["values"][0]) == new_task_id:
                self.task_tree.selection_set(item)
                self.task_tree.focus(item)
                self.task_tree.see(item)
                self.load_task_to_form(None)
                break

    def modify_task(self):
        if not self.current_task_id:
            messagebox.showwarning("Erreur", "Sélectionnez une tâche à modifier.")
            return

        if not messagebox.askyesno("Confirmation", "Voulez-vous vraiment modifier cette tâche ?"):
            return

        title = self.title_var.get()
        description = self.description_text.get("1.0", tk.END).strip()
        due_date = self.due_date_var.get()
        priority = self.priority_var.get()
        status = self.status_var.get()
        recurrence = self.recurrence_var.get()

        if not title or not due_date:
            messagebox.showwarning("Erreur", "Le titre et la date d'échéance sont obligatoires !")
            return

        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Erreur", "La date d'échéance doit être au format YYYY-MM-DD !")
            return

        self.cursor.execute("UPDATE tasks SET title=?, description=?, due_date=?, priority=?, status=?, recurrence=? WHERE id=?",
                           (title, description, due_date, priority, status, recurrence, self.current_task_id))
        self.conn.commit()
        self.refresh_task_list()
        self.parent.after(100, self.refresh_calendar)

    def delete_selected_tasks(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner au moins une tâche à supprimer.")
            return
        if not messagebox.askyesno("Confirmation", f"Supprimer les {len(selected)} tâches sélectionnées ?"):
            return
        for item in selected:
            task_id = self.task_tree.item(item)["values"][0]
            self.cursor.execute("DELETE FROM subtasks WHERE task_id=?", (task_id,))
            self.cursor_library.execute("DELETE FROM task_file_link WHERE task_id=?", (task_id,))
            self.conn_library.commit()
            self.cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()
        self.clear_task_form()
        self.refresh_task_list()
        self.parent.after(100, self.refresh_calendar)
        messagebox.showinfo("Succès", f"{len(selected)} tâches supprimées.")

    def mark_completed(self):
        if not self.current_task_id:
            messagebox.showwarning("Erreur", "Sélectionnez une tâche à marquer comme terminée.")
            return
        if not messagebox.askyesno("Confirmation", "Marquer cette tâche comme terminée ?"):
            return
        self.cursor.execute("SELECT title, description, due_date, priority, recurrence FROM tasks WHERE id=?", (self.current_task_id,))
        task = self.cursor.fetchone()
        if not task:
            return

        # Vérifier si toutes les sous-tâches sont terminées
        self.cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id=?", (self.current_task_id,))
        total_subtasks = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id=? AND status='Terminé'", (self.current_task_id,))
        completed_subtasks = self.cursor.fetchone()[0]

        if total_subtasks > 0 and completed_subtasks < total_subtasks:
            if not messagebox.askyesno("Confirmation", "Certaines sous-tâches ne sont pas terminées. Voulez-vous marquer la tâche comme terminée ?"):
                return
            # Marquer toutes les sous-tâches comme terminées
            self.cursor.execute("UPDATE subtasks SET status='Terminé' WHERE task_id=?", (self.current_task_id,))
            self.conn.commit()

        title, description, due_date, priority, recurrence = task
        self.cursor.execute("UPDATE tasks SET status='Terminé' WHERE id=?", (self.current_task_id,))
        self.conn.commit()

        if recurrence != "Aucune":
            new_due_date = self.calculate_next_due_date(due_date, recurrence)
            self.cursor.execute("INSERT INTO tasks (title, description, due_date, priority, status, recurrence) VALUES (?, ?, ?, ?, 'En cours', ?)",
                               (title, description, new_due_date, priority, recurrence))
            self.conn.commit()

            self.cursor.execute("SELECT last_insert_rowid()")
            new_task_id = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT title FROM subtasks WHERE task_id=?", (self.current_task_id,))
            subtasks = self.cursor.fetchall()
            for subtask in subtasks:
                subtask_title = subtask[0]
                self.cursor.execute("INSERT INTO subtasks (task_id, title, status) VALUES (?, ?, 'En cours')",
                                   (new_task_id, subtask_title))

            self.cursor_library.execute("SELECT file_id FROM task_file_link WHERE task_id=?", (self.current_task_id,))
            file_links = self.cursor_library.fetchall()
            for link in file_links:
                file_id = link[0]
                self.cursor_library.execute("INSERT INTO task_file_link (task_id, file_id) VALUES (?, ?)",
                                           (new_task_id, file_id))
            self.conn_library.commit()

        self.clear_task_form()
        self.refresh_subtasks()
        self.refresh_task_list()
        self.parent.after(100, self.refresh_calendar)

    def calculate_next_due_date(self, due_date, recurrence):
        due = datetime.strptime(due_date, "%Y-%m-%d").date()
        if recurrence == "Quotidienne":
            due += timedelta(days=1)
        elif recurrence == "Hebdomadaire":
            due += timedelta(weeks=1)
        elif recurrence == "Mensuel":
            due += timedelta(days=30)
        elif recurrence == "Trimestrielle":
            due += timedelta(days=90)
        elif recurrence == "Semestrielle":
            due += timedelta(days=180)
        elif recurrence == "Annuelle":
            due += timedelta(days=365)

        while (self.exclude_saturday_var.get() and due.weekday() == 5) or (self.exclude_sunday_var.get() and due.weekday() == 6):
            due += timedelta(days=1)

        return due.strftime("%Y-%m-%d")

    def add_subtask(self):
        if not self.current_task_id:
            messagebox.showwarning("Erreur", "Sélectionnez une tâche pour ajouter une sous-tâche.")
            return

        subtask_window = tk.Toplevel(self.parent)
        subtask_window.title("Ajouter une sous-tâche")
        subtask_window.geometry("300x150")
        subtask_window.transient(self.parent)
        subtask_window.grab_set()

        ttk.Label(subtask_window, text="Titre de la sous-tâche :").pack(pady=5)
        title_var = tk.StringVar()
        title_entry = ttk.Entry(subtask_window, textvariable=title_var)
        title_entry.pack(pady=5, padx=10, fill="x")

        def save_subtask():
            title = title_var.get().strip()
            if not title:
                messagebox.showwarning("Erreur", "Le titre de la sous-tâche est obligatoire.")
                return
            if not messagebox.askyesno("Confirmation", "Ajouter cette sous-tâche ?"):
                return
            self.cursor.execute("INSERT INTO subtasks (task_id, title, status) VALUES (?, ?, 'En cours')",
                               (self.current_task_id, title))
            self.conn.commit()
            self.refresh_subtasks()
            self.refresh_task_list()
            self.parent.after(100, self.refresh_calendar)
            subtask_window.destroy()

        ttk.Button(subtask_window, text="Ajouter", command=save_subtask).pack(pady=5)
        ttk.Button(subtask_window, text="Annuler", command=subtask_window.destroy).pack(pady=5)

    def toggle_subtask_status(self):
        selected = self.subtask_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une sous-tâche.")
            return
        subtask_id = self.subtask_tree.item(selected[0])["values"][0]
        self.cursor.execute("SELECT status FROM subtasks WHERE id=?", (subtask_id,))
        current_status = self.cursor.fetchone()[0]
        new_status = "Terminé" if current_status == "En cours" else "En cours"
        if not messagebox.askyesno("Confirmation", f"Marquer cette sous-tâche comme {new_status.lower()} ?"):
            return
        self.cursor.execute("UPDATE subtasks SET status=? WHERE id=?", (new_status, subtask_id))
        self.conn.commit()
        self.refresh_subtasks()
        self.refresh_task_list()
        self.parent.after(100, self.refresh_calendar)

    def delete_subtask(self):
        selected = self.subtask_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une sous-tâche à supprimer.")
            return
        subtask_id = self.subtask_tree.item(selected[0])["values"][0]
        if not messagebox.askyesno("Confirmation", "Supprimer cette sous-tâche ?"):
            return
        self.cursor.execute("DELETE FROM subtasks WHERE id=?", (subtask_id,))
        self.conn.commit()
        self.refresh_subtasks()
        self.refresh_task_list()
        self.parent.after(100, self.refresh_calendar)

    def modify_subtask(self):
        selected = self.subtask_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une sous-tâche à modifier.")
            return
        subtask_id = self.subtask_tree.item(selected[0])["values"][0]
        current_title = self.subtask_tree.item(selected[0])["values"][1]

        subtask_window = tk.Toplevel(self.parent)
        subtask_window.title("Modifier une sous-tâche")
        subtask_window.geometry("300x150")
        subtask_window.transient(self.parent)
        subtask_window.grab_set()

        ttk.Label(subtask_window, text="Titre de la sous-tâche :").pack(pady=5)
        title_var = tk.StringVar(value=current_title)
        title_entry = ttk.Entry(subtask_window, textvariable=title_var)
        title_entry.pack(pady=5, padx=10, fill="x")

        def save_subtask():
            new_title = title_var.get().strip()
            if not new_title:
                messagebox.showwarning("Erreur", "Le titre de la sous-tâche est obligatoire.")
                return
            if not messagebox.askyesno("Confirmation", "Modifier cette sous-tâche ?"):
                return
            self.cursor.execute("UPDATE subtasks SET title=? WHERE id=?", (new_title, subtask_id))
            self.conn.commit()
            self.refresh_subtasks()
            self.refresh_task_list()
            self.parent.after(100, self.refresh_calendar)
            subtask_window.destroy()

        ttk.Button(subtask_window, text="Modifier", command=save_subtask).pack(pady=5)
        ttk.Button(subtask_window, text="Annuler", command=subtask_window.destroy).pack(pady=5)

    def refresh_subtasks(self):
        for item in self.subtask_tree.get_children():
            self.subtask_tree.delete(item)
        if not self.current_task_id:
            self.progress_bar["value"] = 0
            self.progress_label.config(text="Progression: 0%")
            self.delete_subtask_btn.config(state="disabled")
            self.modify_subtask_btn.config(state="disabled")
            return
        self.cursor.execute("SELECT id, title, status FROM subtasks WHERE task_id=?", (self.current_task_id,))
        total_subtasks = 0
        completed_subtasks = 0
        in_progress_subtasks = 0
        for index, row in enumerate(self.cursor.fetchall()):
            tag = "OddRow" if index % 2 else "EvenRow"
            self.subtask_tree.insert("", tk.END, values=row, tags=(tag,))
            total_subtasks += 1
            if row[2] == "Terminé":
                completed_subtasks += 1
            elif row[2] == "En cours":
                in_progress_subtasks += 1
        if total_subtasks > 0:
            progress = (completed_subtasks / total_subtasks) * 100
            self.progress_bar["value"] = progress
            self.progress_label.config(text=f"Progression: {int(progress)}%")
            self.delete_subtask_btn.config(state="normal")
            self.modify_subtask_btn.config(state="normal")
            self.cursor.execute("SELECT status FROM tasks WHERE id=?", (self.current_task_id,))
            task_status = self.cursor.fetchone()[0]
            if completed_subtasks == total_subtasks and task_status != "Terminé":
                self.cursor.execute("UPDATE tasks SET status='Terminé' WHERE id=?", (self.current_task_id,))
                self.conn.commit()
                self.refresh_task_list()
            elif in_progress_subtasks > 0 and task_status == "Terminé":
                self.cursor.execute("UPDATE tasks SET status='En cours' WHERE id=?", (self.current_task_id,))
                self.conn.commit()
                self.status_var.set("En cours")
                self.refresh_task_list()
        else:
            self.progress_bar["value"] = 0
            self.progress_label.config(text="Progression: 0%")
            self.delete_subtask_btn.config(state="disabled")
            self.modify_subtask_btn.config(state="disabled")
            self.cursor.execute("SELECT status FROM tasks WHERE id=?", (self.current_task_id,))
            task_status = self.cursor.fetchone()[0]
            if task_status == "Terminé":
                self.progress_bar["value"] = 100
                self.progress_label.config(text="Progression: 100%")

    def show_task_calendar(self):
        self.calendar_window = tk.Toplevel(self.parent)
        self.calendar_window.title("Vue Planning des Tâches")
        self.calendar_window.geometry("1280x800")
        self.calendar_window.resizable(True, True)
        self.calendar_window.transient(self.parent)
        self.calendar_window.grab_set()

        paned_window = ttk.PanedWindow(self.calendar_window, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        calendar_frame = ttk.LabelFrame(paned_window, text="Calendrier")
        paned_window.add(calendar_frame, weight=1)

        self.calendar = Calendar(calendar_frame, selectmode="day", date_pattern="yyyy-mm-dd")
        self.calendar.pack(fill="both", expand=True, padx=5, pady=5)

        tasks_frame = ttk.LabelFrame(paned_window, text="Tâches pour la date sélectionnée")
        paned_window.add(tasks_frame, weight=1)

        self.calendar_window.update_idletasks()
        window_width = 1280
        sash_position = window_width // 2
        paned_window.sashpos(0, sash_position)

        tasks_subframe = ttk.PanedWindow(tasks_frame, orient=tk.VERTICAL)
        tasks_subframe.pack(fill="both", expand=True, padx=5, pady=5)

        tasks_tree_frame = ttk.Frame(tasks_subframe)
        tasks_subframe.add(tasks_tree_frame, weight=1)

        self.tasks_tree = ttk.Treeview(tasks_tree_frame, columns=("Title", "Priority", "Status", "Recurrence", "Progress"), show="headings")
        self.tasks_tree.heading("Title", text="Titre")
        self.tasks_tree.heading("Priority", text="Priorité")
        self.tasks_tree.heading("Status", text="Statut")
        self.tasks_tree.heading("Recurrence", text="Récurrence")
        self.tasks_tree.heading("Progress", text="% Terminé")
        self.tasks_tree.column("Title", width=200)
        self.tasks_tree.column("Priority", width=80, anchor="center")
        self.tasks_tree.column("Status", width=80, anchor="center")
        self.tasks_tree.column("Recurrence", width=100, anchor="center")
        self.tasks_tree.column("Progress", width=80, anchor="center")
        self.tasks_tree.pack(fill="both", expand=True)

        subtasks_tree_frame = ttk.LabelFrame(tasks_subframe, text="Sous-tâches")
        tasks_subframe.add(subtasks_tree_frame, weight=1)

        self.subtasks_tree = ttk.Treeview(subtasks_tree_frame, columns=("Title", "Status"), show="headings")
        self.subtasks_tree.heading("Title", text="Titre")
        self.subtasks_tree.heading("Status", text="Statut")
        self.subtasks_tree.column("Title", width=260)
        self.subtasks_tree.column("Status", width=80, anchor="center")
        self.subtasks_tree.pack(fill="both", expand=True, padx=5, pady=5)

        button_frame = ttk.Frame(tasks_frame)
        button_frame.pack(fill="x", pady=5)
        ttk.Button(button_frame, text="Marquer Tâche Terminé/En cours", style="ToggleSubtask.TButton", command=self.toggle_task_status_calendar).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Marquer Sous-tâche Terminé/En cours", style="ToggleSubtask.TButton", command=self.toggle_subtask_status_calendar).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Actualiser", style="Refresh.TButton", command=self.refresh_calendar).pack(side="right", padx=5)

        def update_tasks(event=None):
            selected_task = self.tasks_tree.selection()
            selected_task_title = None
            if selected_task:
                selected_task_title = self.tasks_tree.item(selected_task[0])["values"][0]

            for item in self.tasks_tree.get_children():
                self.tasks_tree.delete(item)
            for item in self.subtasks_tree.get_children():
                self.subtasks_tree.delete(item)
            selected_date = self.calendar.get_date()
            tasks_frame.config(text=f"Tâches pour le {selected_date}")
            self.cursor.execute("SELECT id, title, priority, status, recurrence FROM tasks WHERE due_date=?", (selected_date,))
            tasks = self.cursor.fetchall()
            for index, task in enumerate(tasks):
                task_id, title, priority, status, recurrence = task
                self.cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id=?", (task_id,))
                total_subtasks = self.cursor.fetchone()[0]
                self.cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id=? AND status='Terminé'", (task_id,))
                completed_subtasks = self.cursor.fetchone()[0]
                progress = f"{int((completed_subtasks / total_subtasks) * 100) if total_subtasks > 0 else 0}%"
                if status == "Terminé" and total_subtasks == 0:
                    progress = "100%"
                tag = "OddRow" if index % 2 else "EvenRow"
                item = self.tasks_tree.insert("", tk.END, values=(title, priority, status, recurrence, progress), tags=(task_id, tag))
                if title == selected_task_title:
                    self.tasks_tree.selection_set(item)

        def update_subtasks(event=None):
            selected_subtask = self.subtasks_tree.selection()
            selected_subtask_title = None
            if selected_subtask:
                selected_subtask_title = self.subtasks_tree.item(selected_subtask[0])["values"][0]

            for item in self.subtasks_tree.get_children():
                self.subtasks_tree.delete(item)
            selected = self.tasks_tree.selection()
            if not selected:
                return
            task_id = self.tasks_tree.item(selected[0])["tags"][0]
            self.cursor.execute("SELECT title, status FROM subtasks WHERE task_id=?", (task_id,))
            for index, row in enumerate(self.cursor.fetchall()):
                tag = "OddRow" if index % 2 else "EvenRow"
                item = self.subtasks_tree.insert("", tk.END, values=row, tags=(tag,))
                if row[0] == selected_subtask_title:
                    self.subtasks_tree.selection_set(item)

        self.calendar.bind("<<CalendarSelected>>", update_tasks)
        self.tasks_tree.bind("<<TreeviewSelect>>", update_subtasks)

        self.highlight_calendar_days()
        update_tasks()

        ttk.Button(self.calendar_window, text="Fermer", command=self.close_calendar).pack(pady=5)

    def highlight_calendar_days(self):
        self.calendar.tag_config("has_tasks", background="lightblue")
        self.calendar.tag_config("overdue", background="lightcoral")
        self.calendar.tag_config("all_completed", background="lightgreen")

        self.cursor.execute("SELECT id, due_date, status FROM tasks WHERE due_date IS NOT NULL")
        tasks = self.cursor.fetchall()
        today = datetime.now().date()

        tasks_by_day = {}
        for task in tasks:
            task_id, due_date, status = task
            if not due_date:
                continue
            due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
            if due_date not in tasks_by_day:
                tasks_by_day[due_date] = []
            tasks_by_day[due_date].append((task_id, status))

        for due_date, tasks in tasks_by_day.items():
            all_completed = True
            has_overdue = False
            has_tasks = False

            for _, status in tasks:
                if status != "Terminé":
                    has_tasks = True
                    all_completed = False
                    if due_date < today:
                        has_overdue = True

            if has_overdue:
                self.calendar.calevent_create(due_date, "overdue", "overdue")
            elif all_completed and tasks:
                self.calendar.calevent_create(due_date, "all_completed", "all_completed")
            elif has_tasks:
                self.calendar.calevent_create(due_date, "has_tasks", "has_tasks")

    def toggle_task_status_calendar(self):
        selected = self.tasks_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une tâche.")
            return
        task_id = self.tasks_tree.item(selected[0])["tags"][0]
        self.cursor.execute("SELECT title, description, due_date, priority, status, recurrence FROM tasks WHERE id=?", (task_id,))
        task = self.cursor.fetchone()
        if not task:
            messagebox.showerror("Erreur", "Tâche non trouvée.")
            return

        title, description, due_date, priority, current_status, recurrence = task

        # Vérifier si toutes les sous-tâches sont terminées
        self.cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id=?", (task_id,))
        total_subtasks = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id=? AND status='Terminé'", (task_id,))
        completed_subtasks = self.cursor.fetchone()[0]

        if total_subtasks > 0 and completed_subtasks < total_subtasks and current_status == "En cours":
            if not messagebox.askyesno("Confirmation", "Certaines sous-tâches ne sont pas terminées. Voulez-vous marquer la tâche comme terminée ?"):
                return
            # Marquer toutes les sous-tâches comme terminées
            self.cursor.execute("UPDATE subtasks SET status='Terminé' WHERE task_id=?", (task_id,))
            self.conn.commit()

        new_status = "Terminé" if current_status == "En cours" else "En cours"
        if not messagebox.askyesno("Confirmation", f"Marquer la tâche comme {new_status.lower()} ?"):
            return
        self.cursor.execute("UPDATE tasks SET status=? WHERE id=?", (new_status, task_id))
        self.conn.commit()

        if new_status == "Terminé" and recurrence and recurrence != "Aucune":
            new_due_date = self.calculate_next_due_date(due_date, recurrence)
            self.cursor.execute("INSERT INTO tasks (title, description, due_date, priority, status, recurrence) VALUES (?, ?, ?, ?, ?, ?)",
                               (title, description, new_due_date, priority, "En cours", recurrence))
            self.conn.commit()

            self.cursor.execute("SELECT last_insert_rowid()")
            new_task_id = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT title FROM subtasks WHERE task_id=?", (task_id,))
            subtasks = self.cursor.fetchall()
            for subtask in subtasks:
                subtask_title = subtask[0]
                self.cursor.execute("INSERT INTO subtasks (task_id, title, status) VALUES (?, ?, 'En cours')",
                                   (new_task_id, subtask_title))

            self.cursor_library.execute("SELECT file_id FROM task_file_link WHERE task_id=?", (task_id,))
            file_links = self.cursor_library.fetchall()
            for link in file_links:
                file_id = link[0]
                self.cursor_library.execute("INSERT INTO task_file_link (task_id, file_id) VALUES (?, ?)",
                                           (new_task_id, file_id))
            self.conn_library.commit()

        self.refresh_task_list()
        self.parent.after(100, self.refresh_calendar)

    def toggle_subtask_status_calendar(self):
        selected = self.subtasks_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une sous-tâche.")
            return
        subtask_title = self.subtasks_tree.item(selected[0])["values"][0]
        selected_task = self.tasks_tree.selection()
        if not selected_task:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une tâche.")
            return
        task_id = self.tasks_tree.item(selected_task[0])["tags"][0]
        self.cursor.execute("SELECT id, status FROM subtasks WHERE task_id=? AND title=?", (task_id, subtask_title))
        subtask = self.cursor.fetchone()
        if not subtask:
            return
        subtask_id, current_status = subtask
        new_status = "Terminé" if current_status == "En cours" else "En cours"
        if not messagebox.askyesno("Confirmation", f"Marquer cette sous-tâche comme {new_status.lower()} ?"):
            return
        self.cursor.execute("UPDATE subtasks SET status=? WHERE id=?", (new_status, subtask_id))
        self.conn.commit()

        self.cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id=?", (task_id,))
        total_subtasks = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id=? AND status='Terminé'", (task_id,))
        completed_subtasks = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT title, description, due_date, priority, status, recurrence FROM tasks WHERE id=?", (task_id,))
        task = self.cursor.fetchone()
        if not task:
            messagebox.showerror("Erreur", "Tâche non trouvée.")
            return
        title, description, due_date, priority, task_status, recurrence = task

        if total_subtasks > 0 and completed_subtasks == total_subtasks and task_status != "Terminé":
            self.cursor.execute("UPDATE tasks SET status='Terminé' WHERE id=?", (task_id,))
            self.conn.commit()

            if recurrence and recurrence != "Aucune":
                new_due_date = self.calculate_next_due_date(due_date, recurrence)
                self.cursor.execute("INSERT INTO tasks (title, description, due_date, priority, status, recurrence) VALUES (?, ?, ?, ?, ?, ?)",
                                   (title, description, new_due_date, priority, "En cours", recurrence))
                self.conn.commit()

                self.cursor.execute("SELECT last_insert_rowid()")
                new_task_id = self.cursor.fetchone()[0]

                self.cursor.execute("SELECT title FROM subtasks WHERE task_id=?", (task_id,))
                subtasks = self.cursor.fetchall()
                for subtask in subtasks:
                    subtask_title = subtask[0]
                    self.cursor.execute("INSERT INTO subtasks (task_id, title, status) VALUES (?, ?, 'En cours')",
                                       (new_task_id, subtask_title))

                self.cursor_library.execute("SELECT file_id FROM task_file_link WHERE task_id=?", (task_id,))
                file_links = self.cursor_library.fetchall()
                for link in file_links:
                    file_id = link[0]
                    self.cursor_library.execute("INSERT INTO task_file_link (task_id, file_id) VALUES (?, ?)",
                                               (new_task_id, file_id))
                self.conn_library.commit()

        elif total_subtasks > 0 and completed_subtasks < total_subtasks and task_status == "Terminé":
            self.cursor.execute("UPDATE tasks SET status='En cours' WHERE id=?", (task_id,))
            self.conn.commit()

        self.refresh_task_list()
        self.parent.after(100, self.refresh_calendar)

    def refresh_calendar(self):
        if self.calendar_window and self.calendar_window.winfo_exists():
            selected_date = self.calendar.get_date()
            selected_task = self.tasks_tree.selection()
            selected_task_title = None
            if selected_task:
                selected_task_title = self.tasks_tree.item(selected_task[0])["values"][0]
            selected_subtask = self.subtasks_tree.selection()
            selected_subtask_title = None
            if selected_subtask:
                selected_subtask_title = self.subtasks_tree.item(selected_subtask[0])["values"][0]

            for item in self.tasks_tree.get_children():
                self.tasks_tree.delete(item)
            for item in self.subtasks_tree.get_children():
                self.subtasks_tree.delete(item)
            self.cursor.execute("SELECT id, title, priority, status, recurrence FROM tasks WHERE due_date=?", (selected_date,))
            tasks = self.cursor.fetchall()
            for index, task in enumerate(tasks):
                task_id, title, priority, status, recurrence = task
                self.cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id=?", (task_id,))
                total_subtasks = self.cursor.fetchone()[0]
                self.cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id=? AND status='Terminé'", (task_id,))
                completed_subtasks = self.cursor.fetchone()[0]
                progress = f"{int((completed_subtasks / total_subtasks) * 100) if total_subtasks > 0 else 0}%"
                if status == "Terminé" and total_subtasks == 0:
                    progress = "100%"
                tag = "OddRow" if index % 2 else "EvenRow"
                item = self.tasks_tree.insert("", tk.END, values=(title, priority, status, recurrence, progress), tags=(task_id, tag))
                if title == selected_task_title:
                    self.tasks_tree.selection_set(item)

            if selected_task_title:
                selected = self.tasks_tree.selection()
                if selected:
                    task_id = self.tasks_tree.item(selected[0])["tags"][0]
                    self.cursor.execute("SELECT title, status FROM subtasks WHERE task_id=?", (task_id,))
                    for index, row in enumerate(self.cursor.fetchall()):
                        tag = "OddRow" if index % 2 else "EvenRow"
                        item = self.subtasks_tree.insert("", tk.END, values=row, tags=(tag,))
                        if row[0] == selected_subtask_title:
                            self.subtasks_tree.selection_set(item)

            self.highlight_calendar_days()

    def close_calendar(self):
        self.calendar_window.destroy()
        self.calendar_window = None
        self.tasks_tree = None
        self.subtasks_tree = None
        self.calendar = None

    def associate_file(self):
        if not self.current_task_id:
            messagebox.showwarning("Erreur", "Sélectionnez une tâche pour associer une pièce.")
            return

        select_window = tk.Toplevel(self.parent)
        select_window.title("Sélectionner une pièce")
        select_window.geometry("1600x600")  # Doubled width from 800 to 1600
        select_window.transient(self.parent)
        select_window.grab_set()

        paned_window = ttk.PanedWindow(select_window, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        folder_frame = ttk.LabelFrame(paned_window, text="Dossiers")
        paned_window.add(folder_frame, weight=1)

        search_frame = ttk.Frame(folder_frame)
        search_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(search_frame, text="Année :").pack(side="left")
        self.year_search_var = tk.StringVar()
        year_search_entry = ttk.Entry(search_frame, textvariable=self.year_search_var)
        year_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Label(search_frame, text="Catégorie :").pack(side="left")
        self.category_search_var = tk.StringVar()
        category_search_entry = ttk.Entry(search_frame, textvariable=self.category_search_var)
        category_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Label(search_frame, text="Archives :").pack(side="left")
        self.archives_search_var = tk.StringVar()
        archives_search_entry = ttk.Entry(search_frame, textvariable=self.archives_search_var)
        archives_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Label(search_frame, text="Projet :").pack(side="left")
        self.project_search_var = tk.StringVar()
        project_search_entry = ttk.Entry(search_frame, textvariable=self.project_search_var)
        project_search_entry.pack(side="left", fill="x", expand=True)

        folder_tree = ttk.Treeview(folder_frame, columns=("Year", "Category", "Archives", "Project"), show="headings")
        folder_tree.heading("Year", text="Année")
        folder_tree.heading("Category", text="Catégorie")
        folder_tree.heading("Archives", text="Archives")
        folder_tree.heading("Project", text="Projet")
        folder_tree.column("Year", width=100)
        folder_tree.column("Category", width=150)
        folder_tree.column("Archives", width=150)
        folder_tree.column("Project", width=200)
        folder_tree.pack(fill="both", expand=True, padx=5, pady=5)

        file_frame = ttk.LabelFrame(paned_window, text="Fichiers")
        paned_window.add(file_frame, weight=3)

        file_search_frame = ttk.Frame(file_frame)
        file_search_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(file_search_frame, text="Rechercher fichier :").pack(side="left")
        self.file_search_var = tk.StringVar()
        file_search_entry = ttk.Entry(file_search_frame, textvariable=self.file_search_var)
        file_search_entry.pack(side="left", fill="x", expand=True)

        file_tree = ttk.Treeview(file_frame, columns=("ID", "Title"), show="headings")
        file_tree.heading("ID", text="ID")
        file_tree.heading("Title", text="Titre")
        file_tree.column("ID", width=50)
        file_tree.column("Title", width=450)
        file_tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.cursor_library.execute("SELECT DISTINCT year, category, archives, project FROM library WHERE file_path != '' OR title = '[Dossier]'")
        folder_data = self.cursor_library.fetchall()
        for index, row in enumerate(folder_data):
            normalized_row = (row[0], row[1], row[2] or "", row[3])
            tag = "OddRow" if index % 2 else "EvenRow"
            folder_tree.insert("", tk.END, values=normalized_row, tags=(tag,))

        def filter_folders(event=None):
            for item in folder_tree.get_children():
                folder_tree.delete(item)
            
            year_search = self.year_search_var.get().lower()
            category_search = self.category_search_var.get().lower()
            archives_search = self.archives_search_var.get().lower()
            project_search = self.project_search_var.get().lower()
            
            filtered_data = [
                row for row in folder_data
                if (not year_search or year_search in str(row[0]).lower())
                and (not category_search or category_search in str(row[1]).lower())
                and (not archives_search or archives_search in str(row[2] or "").lower())
                and (not project_search or project_search in str(row[3]).lower())
            ]
            
            for index, row in enumerate(filtered_data):
                normalized_row = (row[0], row[1], row[2] or "", row[3])
                tag = "OddRow" if index % 2 else "EvenRow"
                folder_tree.insert("", tk.END, values=normalized_row, tags=(tag,))

        def load_and_filter_files(event=None):
            for item in file_tree.get_children():
                file_tree.delete(item)
            selected = folder_tree.selection()
            if not selected:
                return
            year, category, archives, project = folder_tree.item(selected[0])["values"]
            
            file_search = self.file_search_var.get().lower()
            
            self.cursor_library.execute("SELECT id, title FROM library WHERE year=? AND category=? AND (archives=? OR archives IS NULL) AND project=? AND file_path != ''",
                                       (year, category, archives or None, project))
            files = self.cursor_library.fetchall()
            
            for index, row in enumerate(files):
                tag = "OddRow" if index % 2 else "EvenRow"
                file_tree.insert("", tk.END, values=row, tags=(tag,))

        year_search_entry.bind("<KeyRelease>", filter_folders)
        category_search_entry.bind("<KeyRelease>", filter_folders)
        archives_search_entry.bind("<KeyRelease>", filter_folders)
        project_search_entry.bind("<KeyRelease>", filter_folders)
        file_search_entry.bind("<KeyRelease>", load_and_filter_files)
        folder_tree.bind("<<TreeviewSelect>>", load_and_filter_files)

        filter_folders()

        def apply_selection():
            file_selected = file_tree.selection()
            if not file_selected:
                messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce.")
                return
            file_id = file_tree.item(file_selected[0])["values"][0]
            self.cursor_library.execute("SELECT 1 FROM task_file_link WHERE task_id=? AND file_id=?", (self.current_task_id, file_id))
            if self.cursor_library.fetchone():
                messagebox.showinfo("Information", "Cette pièce est déjà associée à la tâche.")
                return
            self.cursor_library.execute("INSERT INTO task_file_link (task_id, file_id) VALUES (?, ?)", (self.current_task_id, file_id))
            self.conn_library.commit()
            self.refresh_associated_files()
            select_window.destroy()

        ttk.Button(select_window, text="Associer", command=apply_selection).pack(pady=5)
        ttk.Button(select_window, text="Annuler", command=select_window.destroy).pack(pady=5)

    def dissociate_file(self):
        selected = self.associated_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce à dissocier.")
            return
        file_id = self.associated_tree.item(selected[0])["values"][0]
        if not messagebox.askyesno("Confirmation", "Dissocier cette pièce de la tâche ?"):
            return
        self.cursor_library.execute("DELETE FROM task_file_link WHERE task_id=? AND file_id=?", (self.current_task_id, file_id))
        self.conn_library.commit()
        self.refresh_associated_files()

    def open_associated_file(self):
        selected = self.associated_tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce à ouvrir.")
            return
        file_id = self.associated_tree.item(selected[0])["values"][0]
        self.cursor_library.execute("SELECT file_path FROM library WHERE id=?", (file_id,))
        result = self.cursor_library.fetchone()
        if not result:
            messagebox.showerror("Erreur", "Pièce introuvable dans la bibliothèque.")
            return
        relative_path = result[0]
        file_path = os.path.normpath(os.path.join(self.library_manager.files_dir, relative_path))
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

    def sort_column(self, col, reverse):
        items = [(self.task_tree.set(item, col), item) for item in self.task_tree.get_children()]
        if col == "ID":
            items.sort(key=lambda x: int(x[0]), reverse=reverse)
        elif col == "Due Date":
            items.sort(key=lambda x: x[0] if x[0] else "9999-12-31", reverse=reverse)
        elif col == "Priority":
            priority_order = {"Haute": 1, "Moyenne": 2, "Basse": 3}
            items.sort(key=lambda x: priority_order.get(x[0], 4), reverse=reverse)
        elif col == "Recurrence":
            recurrence_order = {"Aucune": 0, "Quotidienne": 1, "Hebdomadaire": 2, "Mensuel": 3, "Trimestrielle": 4, "Semestrielle": 5, "Annuelle": 6}
            items.sort(key=lambda x: recurrence_order.get(x[0], 7), reverse=reverse)
        elif col == "Progress":
            items.sort(key=lambda x: float(x[0].replace('%', '')) if x[0] else 0, reverse=reverse)
        else:
            items.sort(key=lambda x: x[0].lower(), reverse=reverse)

        for index, (value, item) in enumerate(items):
            self.task_tree.move(item, "", index)

        self.sort_direction[col] = not reverse
        self.task_tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def refresh_task_list(self):
        selected = self.task_tree.selection()
        selected_id = None
        if selected:
            selected_id = self.task_tree.item(selected[0])["values"][0]

        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        search_term = self.search_var.get()
        status_filter = self.status_filter_var.get()
        due_filter = self.due_filter_var.get()

        query = "SELECT id, title, due_date, priority, status, recurrence FROM tasks WHERE 1=1"
        params = []

        if search_term:
            query += " AND (LOWER(title) LIKE ? OR LOWER(description) LIKE ?)"
            params.extend([f"%{search_term.lower()}%", f"%{search_term.lower()}%"])

        if status_filter != "Tous":
            query += " AND status = ?"
            params.append(status_filter)

        if due_filter != "Toutes":
            today = datetime.now().date()
            if due_filter == "Aujourd'hui":
                query += " AND due_date = ?"
                params.append(today.strftime("%Y-%m-%d"))
            elif due_filter == "Cette semaine":
                week_end = today + timedelta(days=7)
                query += " AND due_date BETWEEN ? AND ?"
                params.extend([today.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")])
            elif due_filter == "Ce mois":
                month_start = today.replace(day=1)
                month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
                query += " AND due_date BETWEEN ? AND ?"
                params.extend([month_start.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d")])

        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()

        items = []
        today = datetime.now().date()
        threshold_date = today + timedelta(days=3)

        for index, row in enumerate(rows):
            task_id = row[0]
            due_date = row[2] if row[2] else "9999-12-31"
            self.cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id=?", (task_id,))
            total_subtasks = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id=? AND status='Terminé'", (task_id,))
            completed_subtasks = self.cursor.fetchone()[0]
            progress = f"{int((completed_subtasks / total_subtasks) * 100) if total_subtasks > 0 else 0}%"
            if row[4] == "Terminé" and total_subtasks == 0:
                progress = "100%"
            values = (row[0], row[1], row[2], row[3], row[4], row[5], progress)
            tags = ["OddRow" if index % 2 else "EvenRow"]
            if row[2]:
                due_date_obj = datetime.strptime(row[2], "%Y-%m-%d").date()
                if (due_date_obj <= today or due_date_obj <= threshold_date) and row[4] == "En cours":
                    tags.append("urgent")
                elif row[4] == "Terminé":
                    tags.append("completed")
            item = self.task_tree.insert("", tk.END, values=values, tags=tags)
            items.append((item, task_id, due_date))

        items.sort(key=lambda x: x[2])
        for index, (item, task_id, due_date) in enumerate(items):
            self.task_tree.move(item, "", index)

        if selected_id:
            for item, task_id, _ in items:
                if task_id == selected_id:
                    self.task_tree.selection_set(item)
                    self.task_tree.focus(item)
                    self.task_tree.see(item)
                    break

    def filter_tasks(self, event=None):
        self.refresh_task_list()

    def load_task_to_form(self, event):
        selected = self.task_tree.selection()
        if not selected:
            self.current_task_id = None
            self.associate_btn.config(state="disabled")
            self.add_subtask_btn.config(state="disabled")
            self.toggle_subtask_btn.config(state="disabled")
            self.clear_task_form()
            self.refresh_associated_files()
            self.refresh_subtasks()
            return
        try:
            item = self.task_tree.item(selected[0])["values"]
            self.current_task_id = item[0]
            self.title_var.set(item[1])
            self.due_date_var.set(item[2] if item[2] else "")
            self.priority_var.set(item[3] if item[3] else "Moyenne")
            self.status_var.set(item[4] if item[4] else "En cours")
            self.recurrence_var.set(item[5] if item[5] else "Aucune")
            self.description_text.delete("1.0", tk.END)
            self.cursor.execute("SELECT description FROM tasks WHERE id=?", (self.current_task_id,))
            description = self.cursor.fetchone()[0] or ""
            self.description_text.insert("1.0", description)
            self.modify_btn.config(state="normal")
            self.complete_btn.config(state="normal")
            self.associate_btn.config(state="normal")
            self.add_subtask_btn.config(state="normal")
            self.toggle_subtask_btn.config(state="normal")
            self.refresh_associated_files()
            self.refresh_subtasks()
        except Exception:
            self.clear_task_form()

    def clear_task_form(self):
        self.current_task_id = None
        self.title_var.set("")
        self.description_text.delete("1.0", tk.END)
        self.due_date_var.set("")
        self.priority_var.set("Moyenne")
        self.status_var.set("En cours")
        self.recurrence_var.set("Aucune")
        self.modify_btn.config(state="disabled")
        self.complete_btn.config(state="disabled")
        self.associate_btn.config(state="disabled")
        self.add_subtask_btn.config(state="disabled")
        self.toggle_subtask_btn.config(state="disabled")
        for item in self.associated_tree.get_children():
            self.associated_tree.delete(item)
        for item in self.subtask_tree.get_children():
            self.subtask_tree.delete(item)
        self.progress_bar["value"] = 0
        self.progress_label.config(text="Progression: 0%")

    def refresh_associated_files(self):
        for item in self.associated_tree.get_children():
            self.associated_tree.delete(item)
        if not self.current_task_id:
            return
        self.cursor_library.execute('''SELECT l.id, l.title 
                                      FROM library l 
                                      JOIN task_file_link tfl ON l.id = tfl.file_id 
                                      WHERE tfl.task_id=?''', (self.current_task_id,))
        for index, row in enumerate(self.cursor_library.fetchall()):
            tag = "OddRow" if index % 2 else "EvenRow"
            self.associated_tree.insert("", tk.END, values=row, tags=(tag,))

    def export_to_csv(self):
        if not self.task_tree.get_children():
            messagebox.showwarning("Erreur", "Aucune tâche à exporter.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv")],
            initialfile=f"taches_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["ID", "Titre", "Échéance", "Priorité", "Statut", "Récurrence", "Description"])
                for item in self.task_tree.get_children():
                    values = list(self.task_tree.item(item)["values"])
                    task_id = values[0]
                    self.cursor.execute("SELECT description FROM tasks WHERE id=?", (task_id,))
                    description = self.cursor.fetchone()[0] or ""
                    values.append(description)
                    writer.writerow(values)
            messagebox.showinfo("Succès", f"Tâches exportées dans {file_path}.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exportation : {e}")