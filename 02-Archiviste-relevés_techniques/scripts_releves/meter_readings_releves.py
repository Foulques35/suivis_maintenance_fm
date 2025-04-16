import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import shutil
import subprocess
import calendar

class MeterReadings:
    def __init__(self, parent, conn):
        self.parent = parent
        self.conn = conn
        self.cursor = None if conn is None else conn.cursor()
        self.current_meter_id = None
        self.current_reading_id = None
        self.last_parameter = {}  # Stocke le dernier paramètre par compteur

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
        self.meters_tree.heading("Category", text="Catégorie")
        self.meters_tree.heading("Meter", text="Compteur")
        self.meters_tree.column("Category", width=150)
        self.meters_tree.column("Meter", width=100)
        self.meters_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.meters_tree.bind("<<TreeviewSelect>>", self.load_selected_meter)

        # Formulaire et relevés
        self.right_frame = ttk.PanedWindow(self.main_frame, orient=tk.VERTICAL)
        self.main_frame.add(self.right_frame, weight=2)

        self.form_frame = ttk.LabelFrame(self.right_frame, text="Ajouter un Relevé")
        self.right_frame.add(self.form_frame, weight=1)

        # Formulaire aligné avec une grille
        form_grid = ttk.Frame(self.form_frame)
        form_grid.pack(fill="x", padx=5, pady=5)

        ttk.Label(form_grid, text="Relevé :").grid(row=0, column=0, padx=5, pady=5, sticky="w")
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
        ttk.Combobox(form_grid, textvariable=self.day_var, values=[f"{i:02d}" for i in range(1, 32)], width=5, state="readonly").grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.month_var = tk.StringVar(value=f"{datetime.now().month:02d}")
        ttk.Combobox(form_grid, textvariable=self.month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Combobox(form_grid, textvariable=self.year_var, values=[str(i) for i in range(2000, 2051)], width=7, state="readonly").grid(row=2, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(form_grid, text="Valeur :").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.value_var = tk.StringVar()
        ttk.Entry(form_grid, textvariable=self.value_var, width=30).grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        ttk.Label(form_grid, text="Note :").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.note_var = tk.StringVar()
        ttk.Entry(form_grid, textvariable=self.note_var, width=30).grid(row=4, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        self.target_label = ttk.Label(form_grid, text="Cible : - | Max : - | Unité : -")
        self.target_label.grid(row=5, column=0, columnspan=4, padx=5, pady=5)

        buttons_frame = ttk.Frame(form_grid)
        buttons_frame.grid(row=6, column=0, columnspan=4, pady=10)
        ttk.Button(buttons_frame, text="Enregistrer", command=self.save_reading).pack(side="left", padx=5)
        self.edit_btn = ttk.Button(buttons_frame, text="Modifier", command=self.enable_edit_reading, state="disabled")
        self.edit_btn.pack(side="left", padx=5)
        self.delete_btn = ttk.Button(buttons_frame, text="Supprimer", command=self.delete_reading, state="disabled")
        self.delete_btn.pack(side="left", padx=5)
        self.attachment_var = tk.StringVar()
        ttk.Button(buttons_frame, text="Ajouter fichier", command=self.choose_attachment).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Supprimer Fichier", command=self.delete_attachment).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Ouvrir Fichier", command=self.open_attachment).pack(side="left", padx=5)

        # Liste des relevés
        self.readings_frame = ttk.LabelFrame(self.right_frame, text="Relevés")
        self.right_frame.add(self.readings_frame, weight=3)

        self.readings_tree = ttk.Treeview(self.readings_frame, columns=("ID", "Date", "Meter", "Parameter", "Value", "Target", "Max", "Unit", "Note"), show="headings")
        self.readings_tree.heading("ID", text="ID")
        self.readings_tree.heading("Date", text="Date")
        self.readings_tree.heading("Meter", text="Compteur")
        self.readings_tree.heading("Parameter", text="Paramètre")
        self.readings_tree.heading("Value", text="Valeur")
        self.readings_tree.heading("Target", text="Cible")
        self.readings_tree.heading("Max", text="Max")
        self.readings_tree.heading("Unit", text="Unité")
        self.readings_tree.heading("Note", text="Note")
        self.readings_tree.column("ID", width=50)
        self.readings_tree.column("Date", width=100)
        self.readings_tree.column("Meter", width=100)
        self.readings_tree.column("Parameter", width=100)
        self.readings_tree.column("Value", width=80)
        self.readings_tree.column("Target", width=80)
        self.readings_tree.column("Max", width=80)
        self.readings_tree.column("Unit", width=60)
        self.readings_tree.column("Note", width=100)
        self.readings_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.readings_tree.bind("<<TreeviewSelect>>", self.load_reading_to_form)
        self.readings_tree.tag_configure("exceed", foreground="red")

        # Liste des fichiers joints
        self.files_frame = ttk.LabelFrame(self.right_frame, text="Fichiers Joints")
        self.right_frame.add(self.files_frame, weight=1)

        self.files_tree = ttk.Treeview(self.files_frame, columns=("File"), show="headings")
        self.files_tree.heading("File", text="Fichier")
        self.files_tree.column("File", width=200)
        self.files_tree.pack(fill="both", expand=True, padx=5, pady=5)

        if self.conn:
            self.load_meters_to_tree()

    def set_connection(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor
        self.load_meters_to_tree()

    def load_meters_to_tree(self):
        for item in self.meters_tree.get_children():
            self.meters_tree.delete(item)
        if not self.conn or not self.cursor:
            return
        self.cursor.execute("SELECT id, name, category_id FROM meters")
        meters = self.cursor.fetchall()
        for meter_id, name, category_id in meters:
            category_name = self.get_category_name(category_id)
            self.meters_tree.insert("", tk.END, values=(category_name, name), tags=(meter_id,))

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

    def filter_meters(self, event):
        search_term = self.search_entry.get().lower()
        for item in self.meters_tree.get_children():
            self.meters_tree.delete(item)
        if not self.conn or not self.cursor:
            return
        self.cursor.execute("SELECT id, name, category_id FROM meters")
        meters = self.cursor.fetchall()
        for meter_id, name, category_id in meters:
            category_name = self.get_category_name(category_id)
            if search_term in name.lower() or search_term in category_name.lower():
                self.meters_tree.insert("", tk.END, values=(category_name, name), tags=(meter_id,))

    def load_selected_meter(self, event):
        selected = self.meters_tree.selection()
        if not selected:
            return
        item = self.meters_tree.item(selected[0])
        self.current_meter_id = item["tags"][0]
        self.meter_var.set(item["values"][1])
        self.update_parameters(None)
        self.load_readings()
        self.clear_form()

    def update_parameters(self, event):
        self.parameter_combobox.set("")
        self.parameter_combobox["values"] = []
        self.parameter_map = {}
        self.target_label.config(text="Cible : - | Max : - | Unité : -")
        if not self.current_meter_id or not self.conn or not self.cursor:
            return
        self.cursor.execute("SELECT id, name FROM parameters WHERE meter_id=?", (self.current_meter_id,))
        params = self.cursor.fetchall()
        param_names = [p[1] for p in params]
        self.parameter_combobox["values"] = param_names
        self.parameter_map = {p[1]: p[0] for p in params}
        # Sélectionner le premier paramètre par défaut si disponible
        if param_names:
            self.parameter_var.set(param_names[0])
            self.show_targets(None)
        # Si un dernier paramètre est mémorisé, l’utiliser à la place
        if self.current_meter_id in self.last_parameter:
            last_param = self.last_parameter[self.current_meter_id]
            if last_param in param_names:
                self.parameter_var.set(last_param)
                self.show_targets(None)

    def show_targets(self, event):
        param_name = self.parameter_var.get()
        if not param_name:
            self.target_label.config(text="Cible : - | Max : - | Unité : -")
            return
        param_id = self.parameter_map.get(param_name)
        if not self.conn or not self.cursor:
            return
        self.cursor.execute("SELECT target, max_value, unit FROM parameters WHERE id=?", (param_id,))
        result = self.cursor.fetchone()
        if result:
            target, max_val, unit = result
            target = str(target) if target is not None else "-"
            max_val = str(max_val) if max_val is not None else "-"
            unit = unit or "-"
            self.target_label.config(text=f"Cible : {target} | Max : {max_val} | Unité : {unit}")
        else:
            self.target_label.config(text="Cible : - | Max : - | Unité : -")

    def choose_attachment(self):
        file_path = filedialog.askopenfilename(filetypes=[("Tous fichiers", "*.*")])
        if file_path:
            self.attachment_var.set(file_path)

    def validate_date(self, year, month, day):
        """Valide si la date (jour/mois/année) est correcte."""
        try:
            year = int(year)
            month = int(month)
            day = int(day)
            # Vérifier si le jour est valide pour le mois et l’année donnés
            max_days = calendar.monthrange(year, month)[1]
            if day < 1 or day > max_days:
                return False, f"Le mois {month}/{year} a {max_days} jours maximum, mais {day} a été sélectionné."
            return True, ""
        except ValueError:
            return False, "La date doit contenir des valeurs numériques valides."

    def save_reading(self):
        meter_name = self.meter_var.get()
        param_name = self.parameter_var.get()
        day = self.day_var.get()
        month = self.month_var.get()
        year = self.year_var.get()
        value = self.value_var.get()
        note = self.note_var.get()
        attachment = self.attachment_var.get()

        if not (meter_name and param_name and day and month and year and value):
            messagebox.showwarning("Erreur", "Remplissez tous les champs requis.")
            return

        # Valider la date
        is_valid, error_message = self.validate_date(year, month, day)
        if not is_valid:
            messagebox.showwarning("Erreur", f"Date invalide : {error_message}")
            return

        date = f"{year}-{month}-{day}"

        try:
            value = float(value)
            param_id = self.parameter_map.get(param_name)
            self.cursor.execute("SELECT max_value, target FROM parameters WHERE id=?", (param_id,))
            result = self.cursor.fetchone()
            if not result:
                messagebox.showerror("Erreur", f"Paramètre {param_name} introuvable.")
                return
            max_val, target = result
            if max_val is not None and value > max_val:
                messagebox.showwarning("Attention", f"Valeur dépasse le maximum ({max_val}) !")
            elif target is not None and value > target:
                messagebox.showwarning("Attention", f"Valeur dépasse la cible ({target}) !")

            # Mémoriser le paramètre
            self.last_parameter[self.current_meter_id] = param_name

            # Gérer le fichier joint
            attachment_path = None
            if attachment:
                self.cursor.execute("SELECT name FROM meters WHERE id=?", (self.current_meter_id,))
                meter_name = self.cursor.fetchone()[0]
                dest_dir = os.path.join(os.path.dirname(__file__), "..", "fichiers", year, month, meter_name)
                os.makedirs(dest_dir, exist_ok=True)
                dest_file = os.path.join(dest_dir, os.path.basename(attachment))

                # Vérifier si on doit copier le fichier
                copy_file = True
                if self.current_reading_id:
                    self.cursor.execute("SELECT attachment_path FROM readings WHERE id=?", (self.current_reading_id,))
                    existing_attachment = self.cursor.fetchone()[0]
                    if existing_attachment and os.path.basename(existing_attachment) == os.path.basename(attachment):
                        copy_file = False  # Ne pas copier si le fichier est le même

                if copy_file:
                    shutil.copy2(attachment, dest_file)
                attachment_path = os.path.join("fichiers", year, month, meter_name, os.path.basename(attachment))

            if self.current_reading_id:
                self.cursor.execute("UPDATE readings SET meter_id=?, parameter_id=?, date=?, value=?, note=?, attachment_path=? WHERE id=?",
                                   (self.current_meter_id, param_id, date, value, note, attachment_path, self.current_reading_id))
            else:
                self.cursor.execute("INSERT INTO readings (meter_id, parameter_id, date, value, note, attachment_path) VALUES (?, ?, ?, ?, ?, ?)",
                                   (self.current_meter_id, param_id, date, value, note, attachment_path))
            self.conn.commit()
            self.clear_form()
            self.load_readings()
            self.load_files()
            messagebox.showinfo("Succès", "Relevé enregistré.")
        except ValueError:
            messagebox.showwarning("Erreur", "La valeur doit être un nombre.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def load_readings(self):
        for item in self.readings_tree.get_children():
            self.readings_tree.delete(item)
        if not self.current_meter_id or not self.conn or not self.cursor:
            return
        self.cursor.execute("SELECT id, meter_id, parameter_id, date, value, note, attachment_path FROM readings WHERE meter_id=? ORDER BY date", (self.current_meter_id,))
        readings = self.cursor.fetchall()
        for reading_id, meter_id, param_id, date, value, note, attachment in readings:
            self.cursor.execute("SELECT name, unit, target, max_value FROM parameters WHERE id=?", (param_id,))
            param_result = self.cursor.fetchone()
            if not param_result:
                continue  # Ignore les relevés avec un paramètre invalide
            param_name, unit, target, max_val = param_result
            self.cursor.execute("SELECT name FROM meters WHERE id=?", (meter_id,))
            meter_result = self.cursor.fetchone()
            if not meter_result:
                continue  # Ignore les relevés avec un compteur invalide
            meter_name = meter_result[0]
            note = note or ""
            target = str(target) if target is not None else "-"
            max_val = str(max_val) if max_val is not None else "-"
            tags = ("exceed",) if (target != "-" and float(value) > float(target)) or \
                                  (max_val != "-" and float(value) > float(max_val)) else ()
            self.readings_tree.insert("", tk.END, values=(reading_id, date, meter_name, param_name, value, target, max_val, unit or "-", note), tags=tags)

    def load_files(self):
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        if not self.current_meter_id or not self.conn or not self.cursor:
            return
        self.cursor.execute("SELECT attachment_path FROM readings WHERE meter_id=? AND attachment_path IS NOT NULL", (self.current_meter_id,))
        attachments = self.cursor.fetchall()
        for attachment in attachments:
            self.files_tree.insert("", tk.END, values=(os.path.basename(attachment[0]),))

    def load_reading_to_form(self, event):
        selected = self.readings_tree.selection()
        if not selected:
            return
        item = self.readings_tree.item(selected[0])["values"]
        self.current_reading_id = item[0]
        date = item[1]
        year, month, day = date.split("-")
        self.day_var.set(day)
        self.month_var.set(month)
        self.year_var.set(year)
        self.meter_var.set(item[2])
        self.parameter_var.set(item[3])
        self.value_var.set(str(item[4]))
        self.note_var.set(item[8])
        self.cursor.execute("SELECT attachment_path FROM readings WHERE id=?", (self.current_reading_id,))
        attachment = self.cursor.fetchone()
        if attachment:
            self.attachment_var.set(attachment[0] if attachment[0] else "")
        self.show_targets(None)
        self.edit_btn.config(state="normal")
        self.delete_btn.config(state="normal")

    def enable_edit_reading(self):
        if not self.current_reading_id:
            messagebox.showwarning("Erreur", "Sélectionnez un relevé à modifier.")
            return
        self.meter_combobox.config(state="normal")
        self.parameter_combobox.config(state="normal")

    def delete_reading(self):
        if not self.current_reading_id:
            messagebox.showwarning("Erreur", "Sélectionnez un relevé à supprimer.")
            return
        if messagebox.askyesno("Confirmation", "Supprimer ce relevé ?"):
            self.cursor.execute("DELETE FROM readings WHERE id=?", (self.current_reading_id,))
            self.conn.commit()
            self.clear_form()
            self.load_readings()

    def delete_attachment(self):
        if not self.current_reading_id:
            messagebox.showwarning("Erreur", "Sélectionnez un relevé.")
            return
        self.cursor.execute("SELECT attachment_path FROM readings WHERE id=? AND attachment_path IS NOT NULL", (self.current_reading_id,))
        attachment = self.cursor.fetchone()
        if not attachment:
            messagebox.showinfo("Info", "Aucun fichier joint à supprimer.")
            return
        if messagebox.askyesno("Confirmation", "Supprimer le fichier joint ?"):
            file_path = os.path.join(os.path.dirname(__file__), "..", attachment[0])
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer {file_path} : {e}")
            self.cursor.execute("UPDATE readings SET attachment_path=NULL WHERE id=?", (self.current_reading_id,))
            self.conn.commit()
            self.load_files()
            self.attachment_var.set("")
            messagebox.showinfo("Succès", "Fichier joint supprimé.")

    def clear_form(self):
        self.current_reading_id = None
        self.day_var.set(f"{datetime.now().day:02d}")
        self.month_var.set(f"{datetime.now().month:02d}")
        self.year_var.set(str(datetime.now().year))
        self.value_var.set("")
        self.note_var.set("")
        self.attachment_var.set("")
        self.meter_combobox.config(state="readonly")
        self.parameter_combobox.config(state="readonly")
        self.edit_btn.config(state="disabled")
        self.delete_btn.config(state="disabled")
        self.load_readings()
        self.load_files()

    def open_attachment(self):
        if not self.current_reading_id:
            messagebox.showwarning("Erreur", "Sélectionnez un relevé.")
            return
        self.cursor.execute("SELECT attachment_path FROM readings WHERE id=? AND attachment_path IS NOT NULL", (self.current_reading_id,))
        attachment = self.cursor.fetchone()
        if not attachment:
            messagebox.showinfo("Info", "Aucun fichier joint trouvé.")
            return
        file_path = os.path.join(os.path.dirname(__file__), "..", attachment[0])
        try:
            if os.name == "nt":  # Windows
                os.startfile(file_path)
            else:  # Linux
                subprocess.run(["xdg-open", file_path])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir {file_path} : {e}")