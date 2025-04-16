import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import csv
import os

class MeterReports:
    def __init__(self, parent, conn, graph_manager):
        self.parent = parent
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.graph_manager = graph_manager

        self.main_frame = ttk.LabelFrame(self.parent, text="Rapports")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Filtres
        filters_frame = ttk.Frame(self.main_frame)
        filters_frame.pack(fill="x", pady=5)

        ttk.Label(filters_frame, text="Période de début :").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.start_month_var = tk.StringVar(value="01")
        ttk.Combobox(filters_frame, textvariable=self.start_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly").grid(row=0, column=1, padx=5, pady=5)
        self.start_year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Combobox(filters_frame, textvariable=self.start_year_var, values=[str(i) for i in range(2000, 2051)], width=7, state="readonly").grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(filters_frame, text="Période de fin :").grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.end_month_var = tk.StringVar(value="12")
        ttk.Combobox(filters_frame, textvariable=self.end_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly").grid(row=0, column=4, padx=5, pady=5)
        self.end_year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Combobox(filters_frame, textvariable=self.end_year_var, values=[str(i) for i in range(2000, 2051)], width=7, state="readonly").grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(filters_frame, text="Compteur :").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.meter_var = tk.StringVar()
        self.meter_entry = ttk.Entry(filters_frame, textvariable=self.meter_var, width=20)
        self.meter_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        self.meter_entry.bind("<KeyRelease>", self.compare_periods)

        ttk.Label(filters_frame, text="Catégorie :").grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.category_var = tk.StringVar()
        self.category_entry = ttk.Entry(filters_frame, textvariable=self.category_var, width=20)
        self.category_entry.grid(row=1, column=4, columnspan=2, padx=5, pady=5)
        self.category_entry.bind("<KeyRelease>", self.compare_periods)

        ttk.Label(filters_frame, text="Paramètre :").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.parameter_var = tk.StringVar()
        self.parameter_entry = ttk.Entry(filters_frame, textvariable=self.parameter_var, width=20)
        self.parameter_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5)
        self.parameter_entry.bind("<KeyRelease>", self.compare_periods)

        ttk.Button(filters_frame, text="Générer", command=self.compare_periods).grid(row=2, column=4, padx=5, pady=5)
        ttk.Button(filters_frame, text="Exporter CSV", command=self.export_to_csv).grid(row=2, column=5, padx=5, pady=5)

        # Tableau
        self.tree = ttk.Treeview(self.main_frame, columns=("ID", "Date", "Category", "Meter", "Parameter", "Value", "Unit", "Target", "Max", "Difference", "Status", "Note"), show="headings")
        self.tree.heading("ID", text="ID", command=lambda: self.sort_column("ID", False))
        self.tree.heading("Date", text="Date", command=lambda: self.sort_column("Date", False))
        self.tree.heading("Category", text="Catégorie", command=lambda: self.sort_column("Category", False))
        self.tree.heading("Meter", text="Compteur", command=lambda: self.sort_column("Meter", False))
        self.tree.heading("Parameter", text="Paramètre", command=lambda: self.sort_column("Parameter", False))
        self.tree.heading("Value", text="Valeur", command=lambda: self.sort_column("Value", False))
        self.tree.heading("Unit", text="Unité", command=lambda: self.sort_column("Unit", False))
        self.tree.heading("Target", text="Cible", command=lambda: self.sort_column("Target", False))
        self.tree.heading("Max", text="Max", command=lambda: self.sort_column("Max", False))
        self.tree.heading("Difference", text="Écart", command=lambda: self.sort_column("Difference", False))
        self.tree.heading("Status", text="Statut", command=lambda: self.sort_column("Status", False))
        self.tree.heading("Note", text="Note", command=lambda: self.sort_column("Note", False))
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Date", width=100, anchor="center")
        self.tree.column("Category", width=100, anchor="center")
        self.tree.column("Meter", width=100, anchor="center")
        self.tree.column("Parameter", width=100, anchor="center")
        self.tree.column("Value", width=80, anchor="center")
        self.tree.column("Unit", width=60, anchor="center")
        self.tree.column("Target", width=80, anchor="center")
        self.tree.column("Max", width=80, anchor="center")
        self.tree.column("Difference", width=80, anchor="center")
        self.tree.column("Status", width=80, anchor="center")
        self.tree.column("Note", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree.tag_configure("exceed", background="#FF9999")  # Rouge clair
        self.tree.tag_configure("ok", background="#99FF99")     # Vert clair
        self.tree.tag_configure("below", background="#99CCFF")  # Bleu clair

        self.sort_direction = {}  # Pour suivre la direction du tri par colonne

        self.update_filters()

    def update_filters(self):
        # Compteurs
        self.cursor.execute("SELECT id, name FROM meters")
        self.meters = self.cursor.fetchall()
        self.meter_map = {m[1]: m[0] for m in self.meters}

        # Catégories
        self.cursor.execute("SELECT id, name, parent_id FROM categories")
        categories = self.cursor.fetchall()
        self.cat_hierarchy = {}
        for cat_id, name, parent_id in categories:
            hierarchy = []
            current_id = cat_id
            while current_id:
                self.cursor.execute("SELECT id, name, parent_id FROM categories WHERE id=?", (current_id,))
                cat = self.cursor.fetchone()
                if not cat:
                    break
                hierarchy.append(cat[1])
                current_id = cat[2]
            display_name = " > ".join(reversed(hierarchy))
            self.cat_hierarchy[display_name] = cat_id

        # Paramètres
        self.cursor.execute("SELECT DISTINCT name FROM parameters")
        self.parameters = self.cursor.fetchall()

    def compare_periods(self, event=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        start_date = f"{self.start_year_var.get()}-{self.start_month_var.get()}-01"
        end_date = f"{self.end_year_var.get()}-{self.end_month_var.get()}-01"
        meter_search = self.meter_var.get().lower()
        category_search = self.category_var.get().lower()
        parameter_search = self.parameter_var.get().lower()

        query = """
        SELECT r.id, r.date, m.id as meter_id, m.name as meter_name, m.category_id, p.name as param_name, 
               r.value, p.unit, p.target, p.max_value, r.note
        FROM readings r
        JOIN meters m ON r.meter_id = m.id
        JOIN parameters p ON r.parameter_id = p.id
        WHERE r.date BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if meter_search:
            query += " AND LOWER(m.name) LIKE ?"
            params.append(f"%{meter_search}%")

        if parameter_search:
            query += " AND LOWER(p.name) LIKE ?"
            params.append(f"%{parameter_search}%")

        self.cursor.execute(query, params)
        readings = self.cursor.fetchall()

        filtered_readings = []
        for reading in readings:
            reading_id, date, meter_id, meter_name, category_id, param_name, value, unit, target, max_val, note = reading
            category_name = self.get_category_name(category_id)

            # Filtrer par catégorie
            if category_search and category_search not in category_name.lower():
                continue

            note = note or ""
            unit = unit or "-"
            target = str(target) if target is not None else "-"
            max_val = str(max_val) if max_val is not None else "-"

            # Calcul de l'écart et statut
            difference = "-"
            status = "OK"
            tags = ("ok",)
            if max_val != "-" and value > float(max_val):
                difference = str(round(value - float(max_val), 2))
                status = "Dépassement"
                tags = ("exceed",)
            elif target != "-" and value > float(target):
                difference = str(round(value - float(target), 2))
                status = "Dépassement"
                tags = ("exceed",)
            elif target != "-" and value < float(target):
                difference = str(round(value - float(target), 2))
                status = "Inférieur"
                tags = ("below",)

            filtered_readings.append((
                reading_id, date, category_name, meter_name, param_name, value,
                unit, target, max_val, difference, status, note, tags
            ))

        for reading in filtered_readings:
            reading_id, date, category_name, meter_name, param_name, value, unit, target, max_val, difference, status, note, tags = reading
            self.tree.insert("", tk.END, values=(
                reading_id, date, category_name, meter_name, param_name, value,
                unit, target, max_val, difference, status, note
            ), tags=tags)

    def sort_column(self, col, reverse):
        # Récupérer toutes les lignes
        data = [(self.tree.set(item, col), item) for item in self.tree.get_children()]
        
        # Gérer les valeurs numériques
        try:
            if col in ("Value", "Target", "Max", "Difference"):
                data = [(float(val) if val != "-" else float("-inf"), item) for val, item in data]
            else:
                data = [(val.lower() if isinstance(val, str) else val, item) for val, item in data]
        except ValueError:
            data = [(val.lower() if isinstance(val, str) else val, item) for val, item in data]

        # Inverser la direction du tri si déjà trié sur cette colonne
        if col in self.sort_direction:
            reverse = not self.sort_direction[col]
        self.sort_direction = {col: reverse}

        # Trier les données
        data.sort(reverse=reverse)

        # Réorganiser les éléments dans le Treeview
        for index, (val, item) in enumerate(data):
            self.tree.move(item, "", index)

        # Mettre à jour la commande de tri pour la prochaine fois
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def get_category_name(self, category_id):
        if not category_id:
            return "Aucune"
        hierarchy = []
        current_id = category_id
        while current_id:
            self.cursor.execute("SELECT id, name, parent_id FROM categories WHERE id=?", (current_id,))
            cat = self.cursor.fetchone()
            if not cat:
                break
            hierarchy.append(cat[1])
            current_id = cat[2]
        return " > ".join(reversed(hierarchy))

    def export_to_csv(self):
        if not self.tree.get_children():
            messagebox.showwarning("Erreur", "Aucun relevé à exporter.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Fichiers CSV", "*.csv")])
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                # Écrire les en-têtes
                writer.writerow([self.tree.heading(col)["text"] for col in self.tree["columns"]])
                # Écrire les données
                for item in self.tree.get_children():
                    writer.writerow(self.tree.item(item)["values"])
            messagebox.showinfo("Succès", "Exportation réussie.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exportation : {e}")