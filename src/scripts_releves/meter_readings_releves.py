import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import shutil
import subprocess
import calendar
import csv
from datetime import datetime, timedelta

class MeterReadings:
    def __init__(self, parent, conn):
        self.parent = parent
        self.conn = conn
        self.cursor = None if conn is None else conn.cursor()
        self.current_meter_id = None
        self.current_reading_id = None
        self.last_parameter = {}
        self.parameter_map = {}
        self.form_locked = True
        self.sort_column = None
        self.sort_reverse = False

        self.main_frame = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill="both", expand=True)

        # Liste des compteurs
        self.meters_frame = ttk.LabelFrame(self.main_frame, text="Compteurs")
        self.main_frame.add(self.meters_frame, weight=1)

        search_frame = ttk.Frame(self.meters_frame)
        search_frame.pack(fill="x", pady=5)
        ttk.Label(search_frame, text="Rechercher :").pack(side="left")
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_meters)

        self.meters_tree = ttk.Treeview(self.meters_frame, columns=("Category", "Meter"), show="headings")
        self.meters_tree.heading("Category", text="Catégorie", command=lambda: self.sort_treeview(self.meters_tree, "Category", False))
        self.meters_tree.heading("Meter", text="Compteur", command=lambda: self.sort_treeview(self.meters_tree, "Meter", False))
        self.meters_tree.column("Category", width=300)
        self.meters_tree.column("Meter", width=100)
        self.meters_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.meters_tree.bind("<<TreeviewSelect>>", self.load_selected_meter)

        # Formulaire et relevés
        self.right_frame = ttk.PanedWindow(self.main_frame, orient=tk.VERTICAL)
        self.main_frame.add(self.right_frame, weight=2)

        self.form_frame = ttk.LabelFrame(self.right_frame, text="Ajouter un Relevé")
        self.right_frame.add(self.form_frame, weight=1)

        form_grid = ttk.Frame(self.form_frame)
        form_grid.pack(fill="x", padx=5, pady=5)

        ttk.Label(form_grid, text="Compteur :").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.meter_var = tk.StringVar()
        self.meter_combobox = ttk.Combobox(form_grid, textvariable=self.meter_var, state="readonly", width=30)
        self.meter_combobox.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        self.meter_combobox.bind("<<ComboboxSelected>>", self.update_parameters)

        ttk.Label(form_grid, text="Paramètre :").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.parameter_var = tk.StringVar()
        self.parameter_combobox = ttk.Combobox(form_grid, textvariable=self.parameter_var, state="readonly", width=30)
        self.parameter_combobox.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        self.parameter_combobox.bind("<<ComboboxSelected>>", self.show_targets)

        ttk.Label(form_grid, text="Date :").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.day_var = tk.StringVar(value=f"{datetime.now().day:02d}")
        self.day_combobox = ttk.Combobox(form_grid, textvariable=self.day_var, values=[f"{i:02d}" for i in range(1, 32)], width=5, state="readonly")
        self.day_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.month_var = tk.StringVar(value=f"{datetime.now().month:02d}")
        self.month_combobox = ttk.Combobox(form_grid, textvariable=self.month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly")
        self.month_combobox.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        self.year_combobox = ttk.Combobox(form_grid, textvariable=self.year_var, values=[str(i) for i in range(2000, 2051)], width=7, state="readonly")
        self.year_combobox.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(form_grid, text="Valeur :").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.value_var = tk.StringVar()
        self.value_entry = ttk.Entry(form_grid, textvariable=self.value_var, width=30)
        self.value_entry.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        ttk.Label(form_grid, text="Note :").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.note_var = tk.StringVar()
        self.note_entry = ttk.Entry(form_grid, textvariable=self.note_var, width=30)
        self.note_entry.grid(row=4, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        self.target_frame = ttk.Frame(self.form_frame)
        self.target_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(self.target_frame, text="Min:").pack(side="left")
        self.min_label = ttk.Label(self.target_frame, text="-")
        self.min_label.pack(side="left", padx=5)
        ttk.Label(self.target_frame, text="Max:").pack(side="left")
        self.max_label = ttk.Label(self.target_frame, text="-")
        self.max_label.pack(side="left", padx=5)
        ttk.Label(self.target_frame, text="Unité:").pack(side="left")
        self.unit_label = ttk.Label(self.target_frame, text="-")
        self.unit_label.pack(side="left", padx=5)

        buttons_frame = ttk.Frame(self.form_frame)
        buttons_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(buttons_frame, text="Ajouter Relevé", command=self.add_reading, style="Blue.TButton").pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Enregistrer", command=self.save_reading, style="Green.TButton").pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Modifier", command=self.edit_reading, style="Yellow.TButton").pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Supprimer", command=self.delete_reading, style="Red.TButton").pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Ajouter Fichier", command=self.add_file, style="Blue.TButton").pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Supprimer Fichier", command=self.delete_file, style="Red.TButton").pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Ouvrir Fichier", command=self.open_file, style="Yellow.TButton").pack(side="left", padx=5)

        style = ttk.Style()
        style.configure("Green.TButton", background="#90EE90")
        style.configure("Yellow.TButton", background="#FFFFE0")
        style.configure("Red.TButton", background="#FFB6C1")
        style.configure("Blue.TButton", background="#ADD8E6")

        self.readings_frame = ttk.LabelFrame(self.right_frame, text="Relevés")
        self.right_frame.add(self.readings_frame, weight=2)

        readings_control_frame = ttk.Frame(self.readings_frame)
        readings_control_frame.pack(fill="x", pady=5)

        search_subframe = ttk.Frame(readings_control_frame)
        search_subframe.pack(side="left", padx=5)
        ttk.Label(search_subframe, text="Rechercher :").pack(side="left")
        self.readings_search_entry = ttk.Entry(search_subframe, width=20)
        self.readings_search_entry.pack(side="left", padx=5)
        self.readings_search_entry.bind("<KeyRelease>", self.filter_readings)

        filter_subframe = ttk.Frame(readings_control_frame)
        filter_subframe.pack(side="left", padx=5)
        ttk.Label(filter_subframe, text="Filtrer par période :").pack(side="left")
        self.date_filter_var = tk.StringVar(value="Tous")
        date_filter_options = ["Tous", "Ce mois-ci", "Mois dernier", "Cette année", "Année dernière"]
        self.date_filter_combobox = ttk.Combobox(filter_subframe, textvariable=self.date_filter_var, values=date_filter_options, state="readonly", width=15)
        self.date_filter_combobox.pack(side="left", padx=5)
        self.date_filter_combobox.bind("<<ComboboxSelected>>", self.filter_readings)

        export_subframe = ttk.Frame(readings_control_frame)
        export_subframe.pack(side="right", padx=5)
        ttk.Button(export_subframe, text="Exporter CSV", command=self.export_to_csv).pack(side="right")

        self.readings_tree = ttk.Treeview(self.readings_frame, columns=("ID", "Date", "Meter", "Parameter", "Value", "Min", "Max", "Unit", "Note"), show="headings")
        self.readings_tree.heading("ID", text="ID", command=lambda: self.sort_treeview(self.readings_tree, "ID", False))
        self.readings_tree.heading("Date", text="Date", command=lambda: self.sort_treeview(self.readings_tree, "Date", False))
        self.readings_tree.heading("Meter", text="Compteur", command=lambda: self.sort_treeview(self.readings_tree, "Meter", False))
        self.readings_tree.heading("Parameter", text="Paramètre", command=lambda: self.sort_treeview(self.readings_tree, "Parameter", False))
        self.readings_tree.heading("Value", text="Valeur", command=lambda: self.sort_treeview(self.readings_tree, "Value", False))
        self.readings_tree.heading("Min", text="Min", command=lambda: self.sort_treeview(self.readings_tree, "Min", False))
        self.readings_tree.heading("Max", text="Max", command=lambda: self.sort_treeview(self.readings_tree, "Max", False))
        self.readings_tree.heading("Unit", text="Unité", command=lambda: self.sort_treeview(self.readings_tree, "Unit", False))
        self.readings_tree.heading("Note", text="Note", command=lambda: self.sort_treeview(self.readings_tree, "Note", False))
        self.readings_tree.column("ID", width=50)
        self.readings_tree.column("Date", width=100)
        self.readings_tree.column("Meter", width=100)
        self.readings_tree.column("Parameter", width=100)
        self.readings_tree.column("Value", width=80)
        self.readings_tree.column("Min", width=50)
        self.readings_tree.column("Max", width=50)
        self.readings_tree.column("Unit", width=50)
        self.readings_tree.column("Note", width=150)
        self.readings_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.readings_tree.tag_configure("below", background="#ADD8E6")  # Bleu clair
        self.readings_tree.tag_configure("exceed", background="#FFB6C1")  # Rouge clair
        self.readings_tree.tag_configure("within", background="#90EE90")  # Vert clair
        self.readings_tree.tag_configure("ok", background="white")
        self.readings_tree.bind("<<TreeviewSelect>>", self.load_selected_reading)

        self.files_frame = ttk.LabelFrame(self.right_frame, text="Fichiers")
        self.right_frame.add(self.files_frame, weight=1)

        self.files_listbox = tk.Listbox(self.files_frame)
        self.files_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        self.lock_form()
        self.load_meters_to_tree()

    def lock_form(self):
        self.form_locked = True
        self.meter_combobox.config(state="readonly")
        self.parameter_combobox.config(state="readonly")
        self.day_combobox.config(state="disabled")
        self.month_combobox.config(state="disabled")
        self.year_combobox.config(state="disabled")
        self.value_entry.config(state="disabled")
        self.note_entry.config(state="disabled")

    def unlock_form(self):
        self.form_locked = False
        self.meter_combobox.config(state="readonly")
        self.parameter_combobox.config(state="readonly")
        self.day_combobox.config(state="readonly")
        self.month_combobox.config(state="readonly")
        self.year_combobox.config(state="readonly")
        self.value_entry.config(state="normal")
        self.note_entry.config(state="normal")

    def add_reading(self):
        self.update_parameters()  # Assurer que les paramètres sont chargés
        self.clear_form()
        self.unlock_form()

    def sort_treeview(self, tree, col, reverse):
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = reverse
        items = [(tree.set(item, col), item) for item in tree.get_children()]
        items.sort(key=lambda x: x[0].lower() if isinstance(x[0], str) else x[0], reverse=self.sort_reverse)
        for index, (value, item) in enumerate(items):
            tree.move(item, "", index)
        tree.heading(col, command=lambda: self.sort_treeview(tree, col, not self.sort_reverse))

    def filter_readings(self, event=None):
        search_term = self.readings_search_entry.get().lower()
        period = self.date_filter_var.get()
        self.cursor.execute("SELECT id, meter_id, parameter_id, date, value, note, attachment_path FROM readings WHERE meter_id=? ORDER BY date", (self.current_meter_id,))
        readings = self.cursor.fetchall()
        for item in self.readings_tree.get_children():
            self.readings_tree.delete(item)
        today = datetime.now()
        if period == "Ce mois-ci":
            start_date = today.replace(day=1)
            end_date = today
        elif period == "Mois dernier":
            last_month = today.replace(day=1) - timedelta(days=1)
            start_date = last_month.replace(day=1)
            end_date = last_month
        elif period == "Cette année":
            start_date = today.replace(month=1, day=1)
            end_date = today
        elif period == "Année dernière":
            last_year = today.year - 1
            start_date = datetime(last_year, 1, 1)
            end_date = datetime(last_year, 12, 31)
        else:
            start_date = None
            end_date = None
        for reading_id, meter_id, param_id, date, value, note, attachment in readings:
            reading_date = datetime.strptime(date, "%Y-%m-%d")
            if start_date and end_date:
                if not (start_date <= reading_date <= end_date):
                    continue
            param_name = "-"
            unit = "-"
            min_val = "-"
            max_val = "-"
            tags = ("ok",)
            if param_id:
                self.cursor.execute("SELECT name, unit, target, max_value FROM parameters WHERE id=?", (param_id,))
                param_result = self.cursor.fetchone()
                if param_result:
                    param_name, unit, target_val, max_value = param_result
                    min_val = str(target_val) if target_val is not None else "-"
                    max_val = str(max_value) if max_value is not None else "-"
                    unit = unit or "-"
                    value_float = float(value)
                    has_min = target_val is not None
                    has_max = max_value is not None
                    if has_min and has_max:
                        min_float = float(target_val)
                        max_float = float(max_value)
                        if value_float < min_float:
                            tags = ("below",)
                        elif value_float > max_float:
                            tags = ("exceed",)
                        else:
                            tags = ("within",)
                    elif has_min:
                        min_float = float(target_val)
                        if value_float < min_float:
                            tags = ("below",)
                        else:
                            tags = ("within",)
                    elif has_max:
                        max_float = float(max_value)
                        if value_float > max_float:
                            tags = ("exceed",)
                        else:
                            tags = ("within",)
            self.cursor.execute("SELECT name FROM meters WHERE id=?", (meter_id,))
            meter_result = self.cursor.fetchone()
            if not meter_result:
                continue
            meter_name = meter_result[0]
            note = note or ""
            row_values = [str(reading_id), date, meter_name, param_name, str(value), min_val, max_val, unit, note]
            if search_term and not any(search_term in str(val).lower() for val in row_values):
                continue
            self.readings_tree.insert("", tk.END, values=(reading_id, date, meter_name, param_name, value, min_val, max_val, unit, note), tags=tags)

    def export_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not file_path:
            return
        try:
            with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                headers = ["ID", "Date", "Compteur", "Paramètre", "Valeur", "Min", "Max", "Unité", "Note"]
                writer.writerow(headers)
                for item in self.readings_tree.get_children():
                    values = self.readings_tree.item(item, "values")
                    writer.writerow(values)
            messagebox.showinfo("Succès", f"Les relevés ont été exportés avec succès vers {file_path}.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exportation : {str(e)}")

    def load_meters_to_tree(self):
        for item in self.meters_tree.get_children():
            self.meters_tree.delete(item)
        if not self.conn or not self.cursor:
            return
        query = """
        SELECT m.id, m.name,
               COALESCE(c3.name || ' > ' || c2.name || ' > ' || c1.name,
                        c2.name || ' > ' || c1.name,
                        c1.name) AS category_path
        FROM meters m
        JOIN categories c1 ON m.category_id = c1.id
        LEFT JOIN categories c2 ON c1.parent_id = c2.id
        LEFT JOIN categories c3 ON c2.parent_id = c3.id
        ORDER BY category_path, m.name
        """
        self.cursor.execute(query)
        meters = self.cursor.fetchall()
        meter_names = []
        for meter_id, meter_name, category_path in meters:
            self.meters_tree.insert("", tk.END, values=(category_path, meter_name), tags=(str(meter_id),))
            meter_names.append(f"{meter_name} ({category_path})")
        self.meter_combobox["values"] = meter_names
        if meter_names:
            self.meter_var.set(meter_names[0])
            self.current_meter_id = meters[0][0]
            self.update_parameters()

    def filter_meters(self, event):
        search_term = self.search_entry.get().lower()
        for item in self.meters_tree.get_children():
            self.meters_tree.delete(item)
        query = """
        SELECT m.id, m.name,
               COALESCE(c3.name || ' > ' || c2.name || ' > ' || c1.name,
                        c2.name || ' > ' || c1.name,
                        c1.name) AS category_path
        FROM meters m
        JOIN categories c1 ON m.category_id = c1.id
        LEFT JOIN categories c2 ON c1.parent_id = c2.id
        LEFT JOIN categories c3 ON c2.parent_id = c3.id
        ORDER BY category_path, m.name
        """
        self.cursor.execute(query)
        meters = self.cursor.fetchall()
        for meter_id, meter_name, category_path in meters:
            if search_term in category_path.lower() or search_term in meter_name.lower():
                self.meters_tree.insert("", tk.END, values=(category_path, meter_name), tags=(str(meter_id),))

    def load_selected_meter(self, event):
        selected_item = self.meters_tree.selection()
        if not selected_item:
            return
        meter_id = self.meters_tree.item(selected_item)["tags"][0]
        self.current_meter_id = int(meter_id)
        self.cursor.execute("SELECT m.name, c.name FROM meters m JOIN categories c ON m.category_id = c.id WHERE m.id=?", (self.current_meter_id,))
        meter_name, category_name = self.cursor.fetchone()
        self.meter_var.set(f"{meter_name} ({category_name})")
        self.clear_form()
        self.update_parameters()
        self.load_readings()

    def update_parameters(self, event=None):
        self.parameter_combobox["values"] = []
        self.parameter_map.clear()
        if not self.current_meter_id:
            return
        self.cursor.execute("SELECT id, name FROM parameters WHERE meter_id=?", (self.current_meter_id,))
        parameters = self.cursor.fetchall()
        param_names = []
        for param_id, param_name in parameters:
            param_names.append(param_name)
            self.parameter_map[param_name] = param_id
        self.parameter_combobox["values"] = param_names
        if param_names:
            # Toujours définir last_parameter pour garantir qu'un paramètre est sélectionné
            last_param = self.last_parameter.get(self.current_meter_id, param_names[0])
            if last_param in param_names:
                self.parameter_var.set(last_param)
            else:
                self.parameter_var.set(param_names[0])
                self.last_parameter[self.current_meter_id] = param_names[0]
        else:
            self.parameter_var.set("")
        self.show_targets()

    def show_targets(self, event=None):
        param_name = self.parameter_var.get()
        if not param_name or not self.current_meter_id:
            self.min_label.config(text="-")
            self.max_label.config(text="-")
            self.unit_label.config(text="-")
            return
        param_id = self.parameter_map.get(param_name)
        if param_id:
            self.cursor.execute("SELECT target, max_value, unit FROM parameters WHERE id=?", (param_id,))
            result = self.cursor.fetchone()
            if result:
                target, max_value, unit = result
                self.min_label.config(text=str(target) if target is not None else "-")
                self.max_label.config(text=str(max_value) if max_value is not None else "-")
                self.unit_label.config(text=unit if unit else "-")
            else:
                self.min_label.config(text="-")
                self.max_label.config(text="-")
                self.unit_label.config(text="-")

    def validate_date(self, year, month, day):
        try:
            year, month, day = int(year), int(month), int(day)
            if not (1 <= month <= 12):
                return False, "Mois doit être entre 1 et 12"
            days_in_month = calendar.monthrange(year, month)[1]
            if not (1 <= day <= days_in_month):
                return False, f"Jour doit être entre 1 et {days_in_month}"
            datetime(year, month, day)
            return True, ""
        except ValueError as e:
            return False, f"Date invalide : {str(e)}"

    def save_reading(self):
        if self.form_locked:
            messagebox.showwarning("Erreur", "Veuillez d'abord déverrouiller les champs en cliquant sur Modifier ou Ajouter Relevé.")
            return
        meter_name = self.meter_var.get()
        param_name = self.parameter_var.get()
        day = self.day_var.get()
        month = self.month_var.get()
        year = self.year_var.get()
        value = self.value_var.get()
        note = self.note_var.get()
        if not (meter_name and day and month and year and value):
            messagebox.showwarning("Erreur", "Remplissez tous les champs requis (compteur, date, valeur).")
            return
        if not param_name:
            messagebox.showwarning("Erreur", "Veuillez sélectionner un paramètre.")
            return
        is_valid, error_message = self.validate_date(year, month, day)
        if not is_valid:
            messagebox.showwarning("Erreur", f"Date invalide : {error_message}")
            return
        date = f"{year}-{month}-{day}"
        try:
            value = float(value)
            param_id = self.parameter_map.get(param_name)
            if not param_id:
                messagebox.showerror("Erreur", f"Paramètre {param_name} introuvable. Veuillez vérifier les paramètres du compteur.")
                return
            self.cursor.execute("SELECT target, max_value FROM parameters WHERE id=?", (param_id,))
            result = self.cursor.fetchone()
            if not result:
                messagebox.showerror("Erreur", f"Paramètre {param_name} introuvable dans la base de données.")
                return
            min_val, max_val = result
            if min_val is not None and value < min_val:
                messagebox.showwarning("Attention", f"Valeur inférieure au minimum ({min_val}) !")
            elif max_val is not None and value > max_val:
                messagebox.showwarning("Attention", f"Valeur dépasse le maximum ({max_val}) !")
            self.last_parameter[self.current_meter_id] = param_name
            if self.current_reading_id:
                self.cursor.execute("UPDATE readings SET meter_id=?, parameter_id=?, date=?, value=?, note=?, attachment_path=? WHERE id=?",
                                   (self.current_meter_id, param_id, date, value, note, None, self.current_reading_id))
            else:
                self.cursor.execute("INSERT INTO readings (meter_id, parameter_id, date, value, note, attachment_path) VALUES (?, ?, ?, ?, ?, ?)",
                                   (self.current_meter_id, param_id, date, value, note, None))
            self.conn.commit()
            self.clear_form()
            self.update_parameters()
            self.load_readings()
            self.load_files()
            messagebox.showinfo("Succès", "Relevé enregistré.")
        except ValueError:
            messagebox.showwarning("Erreur", "La valeur doit être un nombre.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def load_readings(self):
        self.filter_readings()

    def load_selected_reading(self, event):
        selected_item = self.readings_tree.selection()
        if not selected_item:
            self.files_listbox.delete(0, tk.END)
            return
        reading_id = self.readings_tree.item(selected_item)["values"][0]
        self.current_reading_id = reading_id
        self.cursor.execute("SELECT meter_id, parameter_id, date, value, note, attachment_path FROM readings WHERE id=?", (reading_id,))
        meter_id, param_id, date, value, note, attachment_path = self.cursor.fetchone()
        self.cursor.execute("SELECT m.name, c.name FROM meters m JOIN categories c ON m.category_id = c.id WHERE m.id=?", (meter_id,))
        meter_name, category_name = self.cursor.fetchone()
        self.meter_var.set(f"{meter_name} ({category_name})")
        self.current_meter_id = meter_id
        self.update_parameters()
        if param_id:
            self.cursor.execute("SELECT name FROM parameters WHERE id=?", (param_id,))
            param_result = self.cursor.fetchone()
            if param_result:
                self.parameter_var.set(param_result[0])
        else:
            self.parameter_var.set("")
        year, month, day = date.split("-")
        self.day_var.set(day)
        self.month_var.set(month)
        self.year_var.set(year)
        self.value_var.set(str(value))
        self.note_var.set(note if note else "")
        self.show_targets()
        self.lock_form()
        self.load_files()

    def clear_form(self):
        self.current_reading_id = None
        self.day_var.set(f"{datetime.now().day:02d}")
        self.month_var.set(f"{datetime.now().month:02d}")
        self.year_var.set(str(datetime.now().year))
        self.value_var.set("")
        self.note_var.set("")
        # Ne pas réinitialiser self.parameter_var ici pour préserver le paramètre sélectionné
        self.load_readings()
        self.files_listbox.delete(0, tk.END)
        self.lock_form()

    def edit_reading(self):
        if not self.current_reading_id:
            messagebox.showwarning("Erreur", "Sélectionnez un relevé à modifier.")
            return
        self.unlock_form()

    def delete_reading(self):
        if not self.current_reading_id:
            messagebox.showwarning("Erreur", "Sélectionnez un relevé à supprimer.")
            return
        if messagebox.askyesno("Confirmer", "Voulez-vous supprimer ce relevé ?"):
            self.cursor.execute("SELECT attachment_path FROM readings WHERE id=?", (self.current_reading_id,))
            attachment_path = self.cursor.fetchone()[0]
            if attachment_path and os.path.exists(attachment_path):
                os.remove(attachment_path)
            self.cursor.execute("DELETE FROM readings WHERE id=?", (self.current_reading_id,))
            self.conn.commit()
            self.clear_form()
            self.load_readings()
            self.load_files()

    def load_files(self):
        self.files_listbox.delete(0, tk.END)
        if not self.current_reading_id:
            return
        self.cursor.execute("SELECT attachment_path FROM readings WHERE id=? AND attachment_path IS NOT NULL", (self.current_reading_id,))
        file_path = self.cursor.fetchone()
        if file_path:
            file_path = file_path[0]
            if file_path and os.path.exists(file_path):
                self.files_listbox.insert(tk.END, os.path.basename(file_path))

    def add_file(self):
        if not self.current_reading_id:
            messagebox.showwarning("Erreur", "Sélectionnez un relevé pour ajouter un fichier.")
            return
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        self.cursor.execute("SELECT name FROM meters WHERE id=?", (self.current_meter_id,))
        meter_name = self.cursor.fetchone()[0]
        year = self.year_var.get()
        month = self.month_var.get()
        dest_dir = os.path.join(os.path.dirname(__file__), "..", "fichiers", year, month, meter_name)
        os.makedirs(dest_dir, exist_ok=True)
        dest_file = os.path.join(dest_dir, os.path.basename(file_path))
        shutil.copy2(file_path, dest_file)
        attachment_path = os.path.join("fichiers", year, month, meter_name, os.path.basename(file_path))
        self.cursor.execute("UPDATE readings SET attachment_path=? WHERE id=?", (attachment_path, self.current_reading_id))
        self.conn.commit()
        self.load_files()

    def delete_file(self):
        selected_file = self.files_listbox.curselection()
        if not selected_file:
            messagebox.showwarning("Erreur", "Sélectionnez un fichier à supprimer.")
            return
        file_name = self.files_listbox.get(selected_file)
        self.cursor.execute("SELECT attachment_path FROM readings WHERE attachment_path LIKE ?", (f"%{file_name}",))
        file_path = self.cursor.fetchone()[0]
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        self.cursor.execute("UPDATE readings SET attachment_path=NULL WHERE attachment_path LIKE ?", (f"%{file_name}",))
        self.conn.commit()
        self.load_files()

    def open_file(self):
        selected_file = self.files_listbox.curselection()
        if not selected_file:
            messagebox.showwarning("Erreur", "Sélectionnez un fichier à ouvrir.")
            return
        file_name = self.files_listbox.get(selected_file)
        self.cursor.execute("SELECT attachment_path FROM readings WHERE attachment_path LIKE ?", (f"%{file_name}",))
        file_path = self.cursor.fetchone()[0]
        if file_path and os.path.exists(file_path):
            subprocess.run(['xdg-open', file_path], check=True)
        else:
            messagebox.showerror("Erreur", "Fichier introuvable.")