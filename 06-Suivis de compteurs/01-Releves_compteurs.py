import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta

class MeterReadingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion des Relevés de Compteurs")

        # Appliquer le thème Clam
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#e1e1e1", foreground="#333333")
        style.configure("TButton", background="#4CAF50", foreground="white")
        style.configure("TEntry", fieldbackground="#ffffff")
        style.configure("TCombobox", fieldbackground="#ffffff")
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff")

        self.conn = sqlite3.connect("meters.db")
        self.cursor = self.conn.cursor()
        self.create_readings_table()

        # Liste des compteurs et catégories
        self.meters = self.load_meters()
        self.categories = self.load_categories()
        self.meter_to_category = {meter[0]: meter[3] for meter in self.meters}

        # Interface principale avec onglets
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Onglet "Relevés"
        self.readings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.readings_frame, text="Relevés")
        self.setup_readings_tab()

        # Onglet "Configuration"
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Configuration")
        self.setup_config_tab()

    def create_readings_table(self):
        """Crée les tables nécessaires et ajoute les colonnes nécessaires."""
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meter_id INTEGER,
            date TEXT NOT NULL,
            meter_index INTEGER NOT NULL,
            consumption INTEGER DEFAULT 0,
            note TEXT,
            FOREIGN KEY (meter_id) REFERENCES meters(id)
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS base_indices (
            meter_id INTEGER PRIMARY KEY,
            base_index INTEGER NOT NULL,
            FOREIGN KEY (meter_id) REFERENCES meters(id)
        )''')
        # Ajouter la colonne 'consumption' si elle n'existe pas déjà
        try:
            self.cursor.execute("ALTER TABLE readings ADD COLUMN consumption INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            # La colonne existe déjà, pas d'erreur
            pass
        self.conn.commit()

    def load_meters(self):
        """Charge les compteurs depuis la base de données."""
        self.cursor.execute("SELECT id, name, note, category_id FROM meters")
        return self.cursor.fetchall()

    def load_categories(self):
        """Charge les catégories depuis la base de données."""
        self.cursor.execute("SELECT id, name, parent_id FROM categories")
        return self.cursor.fetchall()

    def get_category_name(self, category_id):
        """Récupère le nom de la catégorie avec son chemin hiérarchique."""
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

    def setup_readings_tab(self):
        """Configure l'onglet Relevés."""
        self.readings_main_frame = ttk.PanedWindow(self.readings_frame, orient=tk.HORIZONTAL)
        self.readings_main_frame.pack(fill="both", expand=True)

        self.meters_frame = ttk.LabelFrame(self.readings_main_frame, text="Sélectionner un Compteur")
        self.readings_main_frame.add(self.meters_frame, weight=1)

        search_frame = ttk.Frame(self.meters_frame)
        search_frame.pack(fill="x", pady=5)

        ttk.Label(search_frame, text="Catégorie :").pack(side="left")
        self.meters_category_search_entry = ttk.Entry(search_frame, width=15)
        self.meters_category_search_entry.pack(side="left", padx=5)
        self.meters_category_search_entry.bind("<KeyRelease>", self.filter_meters)

        ttk.Label(search_frame, text="Compteur :").pack(side="left")
        self.meters_name_search_entry = ttk.Entry(search_frame)
        self.meters_name_search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.meters_name_search_entry.bind("<KeyRelease>", self.filter_meters)

        self.meters_tree = ttk.Treeview(self.meters_frame, columns=("Category", "Meter"), show="headings")
        self.meters_tree.heading("Category", text="Catégorie", command=lambda: self.sort_column(self.meters_tree, "Category", False))
        self.meters_tree.heading("Meter", text="Compteur", command=lambda: self.sort_column(self.meters_tree, "Meter", False))
        self.meters_tree.column("Category", width=200)
        self.meters_tree.column("Meter", width=150)
        self.meters_tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.meters_tree.bind("<<TreeviewSelect>>", self.load_selected_meter)

        self.readings_right_frame = ttk.Frame(self.readings_main_frame)
        self.readings_main_frame.add(self.readings_right_frame, weight=2)

        self.readings_form_frame = ttk.LabelFrame(self.readings_right_frame, text="Ajouter/Modifier un Relevé")
        self.readings_form_frame.pack(fill="x", pady=5)

        ttk.Label(self.readings_form_frame, text="Mois :").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.reading_month_var = tk.StringVar()
        self.reading_month_combobox = ttk.Combobox(self.readings_form_frame, textvariable=self.reading_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5)
        self.reading_month_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.reading_month_combobox.bind("<<ComboboxSelected>>", self.update_reading)

        ttk.Label(self.readings_form_frame, text="Année :").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.reading_year_var = tk.StringVar()
        self.reading_year_combobox = ttk.Combobox(self.readings_form_frame, textvariable=self.reading_year_var, values=[str(i) for i in range(2000, 2030)], width=7)
        self.reading_year_combobox.grid(row=0, column=3, padx=5, pady=5)
        self.reading_year_combobox.bind("<<ComboboxSelected>>", self.update_reading)

        ttk.Label(self.readings_form_frame, text="Index :").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.reading_index_var = tk.StringVar()
        self.reading_index_entry = ttk.Entry(self.readings_form_frame, textvariable=self.reading_index_var)
        self.reading_index_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        self.reading_index_var.trace("w", self.update_reading)

        ttk.Label(self.readings_form_frame, text="Note :").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.reading_note_var = tk.StringVar()
        self.reading_note_entry = ttk.Entry(self.readings_form_frame, textvariable=self.reading_note_var)
        self.reading_note_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        self.reading_note_var.trace("w", self.update_reading)

        ttk.Button(self.readings_form_frame, text="Nouveau", command=self.clear_reading_form).grid(row=3, column=0, padx=5, pady=5)
        ttk.Button(self.readings_form_frame, text="Supprimer", command=self.delete_reading).grid(row=3, column=1, padx=5, pady=5)

        self.readings_filter_frame = ttk.Frame(self.readings_right_frame)
        self.readings_filter_frame.pack(fill="x", pady=5)

        ttk.Label(self.readings_filter_frame, text="Rechercher :").pack(side="left")
        self.readings_search_entry = ttk.Entry(self.readings_filter_frame)
        self.readings_search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.readings_search_entry.bind("<KeyRelease>", self.filter_readings)

        ttk.Label(self.readings_filter_frame, text="Filtrer par date :").pack(side="left", padx=5)
        self.date_filter_var = tk.StringVar()
        self.date_filter_combobox = ttk.Combobox(self.readings_filter_frame, textvariable=self.date_filter_var, values=["Ce mois-ci", "Mois dernier", "Cette année", "Année dernière", "Aucun"], width=15)
        self.date_filter_combobox.pack(side="left", padx=5)
        self.date_filter_combobox.set("Aucun")
        self.date_filter_combobox.bind("<<ComboboxSelected>>", self.filter_readings)

        self.readings_tree_frame = ttk.Frame(self.readings_right_frame)
        self.readings_tree_frame.pack(fill="both", expand=True)

        self.readings_tree = ttk.Treeview(self.readings_tree_frame, columns=("ID", "Date", "Meter", "Index", "Consumption", "Note"), show="headings")
        self.readings_tree.heading("ID", text="ID")
        self.readings_tree.heading("Date", text="Date")
        self.readings_tree.heading("Meter", text="Compteur")
        self.readings_tree.heading("Index", text="Index")
        self.readings_tree.heading("Consumption", text="Consommation")
        self.readings_tree.heading("Note", text="Note")
        self.readings_tree.column("ID", width=50)
        self.readings_tree.column("Date", width=100)
        self.readings_tree.column("Meter", width=150)
        self.readings_tree.column("Index", width=100)
        self.readings_tree.column("Consumption", width=100)
        self.readings_tree.column("Note", width=150)
        self.readings_tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.readings_tree.bind("<<TreeviewSelect>>", self.load_reading_to_form)
        self.readings_tree.bind("<Double-1>", self.edit_reading)

        self.current_reading_id = None
        self.current_meter_id = None
        self.load_meters_to_tree()
        self.reading_month_var.set(f"{datetime.now().month:02d}")
        self.reading_year_var.set(str(datetime.now().year))

    def setup_config_tab(self):
        """Configure l'onglet Configuration."""
        self.config_tree_frame = ttk.Frame(self.config_frame)
        self.config_tree_frame.pack(fill="both", expand=True)

        search_frame = ttk.Frame(self.config_tree_frame)
        search_frame.pack(fill="x", pady=5)
        ttk.Label(search_frame, text="Rechercher :").pack(side="left")
        self.config_search_entry = ttk.Entry(search_frame)
        self.config_search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.config_search_entry.bind("<KeyRelease>", self.filter_config)

        self.config_tree = ttk.Treeview(self.config_tree_frame, columns=("Category", "Meter", "BaseIndex"), show="headings")
        self.config_tree.heading("Category", text="Catégorie")
        self.config_tree.heading("Meter", text="Compteur")
        self.config_tree.heading("BaseIndex", text="Index de Base")
        self.config_tree.column("Category", width=200)
        self.config_tree.column("Meter", width=150)
        self.config_tree.column("BaseIndex", width=100)
        self.config_tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.config_tree.bind("<Double-1>", self.edit_base_index)

        self.load_config()

    def sort_column(self, tree, col, reverse):
        """Trie les colonnes du Treeview."""
        items = [(tree.set(item, col), item) for item in tree.get_children()]
        items.sort(reverse=reverse)
        for index, (value, item) in enumerate(items):
            tree.move(item, "", index)
        tree.heading(col, command=lambda: self.sort_column(tree, col, not reverse))

    def load_meters_to_tree(self):
        """Charge les compteurs dans le Treeview de l'onglet Relevés."""
        for item in self.meters_tree.get_children():
            self.meters_tree.delete(item)

        for meter in self.meters:
            meter_id = meter[0]
            category_id = meter[3]
            category_name = self.get_category_name(category_id)
            self.meters_tree.insert("", tk.END, values=(category_name, meter[1]), tags=(meter_id,))

    def filter_meters(self, event):
        """Filtre les compteurs dans le Treeview en fonction des recherches."""
        category_search = self.meters_category_search_entry.get().lower()
        name_search = self.meters_name_search_entry.get().lower()

        for item in self.meters_tree.get_children():
            self.meters_tree.delete(item)

        for meter in self.meters:
            meter_id = meter[0]
            category_id = meter[3]
            category_name = self.get_category_name(category_id)
            if (not category_search or category_search in category_name.lower()) and (not name_search or name_search in meter[1].lower()):
                self.meters_tree.insert("", tk.END, values=(category_name, meter[1]), tags=(meter_id,))

    def get_last_reading_date(self, meter_id):
        """Récupère la date du dernier relevé pour un compteur donné."""
        self.cursor.execute("SELECT date FROM readings WHERE meter_id=? ORDER BY date DESC LIMIT 1", (meter_id,))
        result = self.cursor.fetchone()
        if result:
            year, month = result[0].split("-")
            return month, year
        return None, None

    def load_selected_meter(self, event):
        """Charge le compteur sélectionné dans le formulaire et met à jour les champs avec la dernière date."""
        selected = self.meters_tree.selection()
        if not selected:
            return

        item = self.meters_tree.item(selected[0])
        self.current_meter_id = item["tags"][0]
        self.update_all_consumptions(self.current_meter_id)  # Recalculer toutes les consommations
        self.load_readings()

        last_month, last_year = self.get_last_reading_date(self.current_meter_id)
        if last_month and last_year:
            self.reading_month_var.set(last_month)
            self.reading_year_var.set(last_year)
        else:
            self.reading_month_var.set(f"{datetime.now().month:02d}")
            self.reading_year_var.set(str(datetime.now().year))

    def update_all_consumptions(self, meter_id):
        """Met à jour dynamiquement toutes les consommations pour un compteur donné."""
        self.cursor.execute("SELECT base_index FROM base_indices WHERE meter_id=?", (meter_id,))
        base_index = self.cursor.fetchone()
        base_index = base_index[0] if base_index else 0

        self.cursor.execute("SELECT id, meter_index, date FROM readings WHERE meter_id=? ORDER BY date", (meter_id,))
        readings = self.cursor.fetchall()

        prev_index = base_index
        for reading in readings:
            reading_id, current_index, date = reading
            consumption = current_index - prev_index if current_index >= prev_index else 0
            self.cursor.execute("UPDATE readings SET consumption=? WHERE id=?", (consumption, reading_id))
            prev_index = current_index

        self.conn.commit()

    def load_readings(self):
        """Charge les relevés dans le Treeview avec les consommations enregistrées."""
        for item in self.readings_tree.get_children():
            self.readings_tree.delete(item)

        if not self.current_meter_id:
            return

        self.cursor.execute("SELECT id, meter_id, date, meter_index, consumption, note FROM readings WHERE meter_id=? ORDER BY date", (self.current_meter_id,))
        readings = self.cursor.fetchall()

        for reading in readings:
            reading_id, meter_id, date, index, consumption, note = reading
            meter_name = next((meter[1] for meter in self.meters if meter[0] == meter_id), "Inconnu")
            note = note if note is not None else ""
            self.readings_tree.insert("", tk.END, values=(reading_id, date, meter_name, index, consumption, note), tags=(index,))

    def filter_readings(self, event=None):
        """Filtre les relevés dans le Treeview en fonction de la recherche et du filtre de date."""
        search_term = self.readings_search_entry.get().lower()
        date_filter = self.date_filter_var.get()

        for item in self.readings_tree.get_children():
            self.readings_tree.delete(item)

        if not self.current_meter_id:
            return

        now = datetime.now()
        if date_filter == "Ce mois-ci":
            start_date = f"{now.year}-{now.month:02d}"
            end_date = start_date
        elif date_filter == "Mois dernier":
            last_month = now - relativedelta(months=1)
            start_date = f"{last_month.year}-{last_month.month:02d}"
            end_date = start_date
        elif date_filter == "Cette année":
            start_date = f"{now.year}-01"
            end_date = f"{now.year}-12"
        elif date_filter == "Année dernière":
            last_year = now.year - 1
            start_date = f"{last_year}-01"
            end_date = f"{last_year}-12"
        else:
            start_date = "0000-00"
            end_date = "9999-99"

        self.cursor.execute("SELECT id, meter_id, date, meter_index, consumption, note FROM readings WHERE meter_id=? AND date BETWEEN ? AND ? ORDER BY date", (self.current_meter_id, start_date, end_date))
        readings = self.cursor.fetchall()

        for reading in readings:
            reading_id, meter_id, date, index, consumption, note = reading
            meter_name = next((meter[1] for meter in self.meters if meter[0] == meter_id), "Inconnu")
            note = note if note is not None else ""
            if (search_term in date.lower() or search_term in meter_name.lower() or 
                search_term in str(index) or search_term in str(consumption) or search_term in note.lower()):
                self.readings_tree.insert("", tk.END, values=(reading_id, date, meter_name, index, consumption, note), tags=(index,))

    def load_reading_to_form(self, event):
        """Charge les données d'un relevé dans le formulaire."""
        selected = self.readings_tree.selection()
        if not selected:
            return

        item = self.readings_tree.item(selected[0])["values"]
        self.current_reading_id = item[0]

        date = item[1]
        year, month = date.split("-")
        self.reading_month_var.set(month)
        self.reading_year_var.set(year)

        index = str(item[3])
        self.reading_index_var.set(index)

        note = item[5] if len(item) > 5 else ""
        self.reading_note_var.set(note)

    def edit_reading(self, event):
        """Permet d'éditer un relevé directement dans le Treeview et met à jour les consommations."""
        selected = self.readings_tree.selection()
        if not selected:
            return

        item = self.readings_tree.item(selected[0])
        reading_id = item["values"][0]
        column = self.readings_tree.identify_column(event.x)
        if column not in ("#2", "#4", "#6"):  # Date, Index, Note
            return

        entry = ttk.Entry(self.readings_tree)
        entry.place(x=event.x, y=event.y, width=100)
        entry.insert(0, item["values"][int(column[1]) - 1])

        def save_edit(event):
            new_value = entry.get()
            if column == "#2":  # Date
                try:
                    year, month = new_value.split("-")
                    if not (month.isdigit() and year.isdigit() and 1 <= int(month) <= 12 and 2000 <= int(year) <= 2030):
                        raise ValueError
                    self.cursor.execute("UPDATE readings SET date=? WHERE id=?", (new_value, reading_id))
                    self.update_all_consumptions(self.current_meter_id)  # Recalculer toutes les consommations
                except ValueError:
                    messagebox.showwarning("Erreur", "Format de date invalide (YYYY-MM).")
                    entry.destroy()
                    return
            elif column == "#4":  # Index
                new_value = new_value.replace(" ", "")
                if not new_value.isdigit():
                    messagebox.showwarning("Erreur", "L'index doit être un nombre entier.")
                    entry.destroy()
                    return
                new_index = int(new_value)
                self.cursor.execute("UPDATE readings SET meter_index=? WHERE id=?", (new_index, reading_id))
                self.update_all_consumptions(self.current_meter_id)  # Recalculer toutes les consommations
            elif column == "#6":  # Note
                self.cursor.execute("UPDATE readings SET note=? WHERE id=?", (new_value, reading_id))

            self.conn.commit()
            self.load_readings()
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)
        entry.focus_set()

    def update_reading(self, *args):
        """Met à jour un relevé ou en ajoute un nouveau et recalcule toutes les consommations."""
        month = self.reading_month_var.get()
        year = self.reading_year_var.get()
        if not month or not year:
            return

        if not self.current_meter_id:
            return

        index = self.reading_index_var.get().replace(" ", "")
        if not index.isdigit():
            return
        index = int(index)

        date = f"{year}-{month}"
        note = self.reading_note_var.get()

        if self.current_reading_id:
            self.cursor.execute("UPDATE readings SET meter_id=?, date=?, meter_index=?, note=? WHERE id=?", 
                               (self.current_meter_id, date, index, note, self.current_reading_id))
        else:
            self.cursor.execute("INSERT INTO readings (meter_id, date, meter_index, note) VALUES (?, ?, ?, ?)", 
                               (self.current_meter_id, date, index, note))
            self.current_reading_id = self.cursor.lastrowid

        self.conn.commit()
        self.update_all_consumptions(self.current_meter_id)  # Recalculer toutes les consommations
        self.load_readings()

    def clear_reading_form(self):
        """Réinitialise le formulaire pour un nouveau relevé avec la dernière date du compteur sélectionné."""
        self.current_reading_id = None
        if self.current_meter_id:
            last_month, last_year = self.get_last_reading_date(self.current_meter_id)
            if last_month and last_year:
                self.reading_month_var.set(last_month)
                self.reading_year_var.set(last_year)
            else:
                self.reading_month_var.set(f"{datetime.now().month:02d}")
                self.reading_year_var.set(str(datetime.now().year))
        else:
            self.reading_month_var.set(f"{datetime.now().month:02d}")
            self.reading_year_var.set(str(datetime.now().year))
        self.reading_index_var.set("")
        self.reading_note_var.set("")

    def delete_reading(self):
        """Supprime un relevé sélectionné et recalcule les consommations."""
        if not self.current_reading_id:
            messagebox.showwarning("Erreur", "Veuillez sélectionner un relevé à supprimer.")
            return

        if messagebox.askyesno("Confirmation", "Supprimer ce relevé ?"):
            self.cursor.execute("DELETE FROM readings WHERE id=?", (self.current_reading_id,))
            self.conn.commit()
            self.update_all_consumptions(self.current_meter_id)  # Recalculer toutes les consommations
            self.clear_reading_form()
            self.load_readings()

    def load_config(self):
        """Charge les compteurs et leurs index de base dans le Treeview."""
        for item in self.config_tree.get_children():
            self.config_tree.delete(item)

        self.cursor.execute("SELECT meter_id, base_index FROM base_indices")
        base_indices = {row[0]: row[1] for row in self.cursor.fetchall()}

        for meter in self.meters:
            meter_id = meter[0]
            category_id = meter[3]
            category_name = self.get_category_name(category_id)
            base_index = base_indices.get(meter_id, 0)
            self.config_tree.insert("", tk.END, values=(category_name, meter[1], f"{base_index:,}".replace(",", " ")), tags=(meter_id,))

    def filter_config(self, event):
        """Filtre les compteurs dans le Treeview en fonction de la recherche."""
        search_term = self.config_search_entry.get().lower()
        for item in self.config_tree.get_children():
            self.config_tree.delete(item)

        self.cursor.execute("SELECT meter_id, base_index FROM base_indices")
        base_indices = {row[0]: row[1] for row in self.cursor.fetchall()}

        for meter in self.meters:
            meter_id = meter[0]
            category_id = meter[3]
            category_name = self.get_category_name(category_id)
            base_index = base_indices.get(meter_id, 0)
            if search_term in category_name.lower() or search_term in meter[1].lower():
                self.config_tree.insert("", tk.END, values=(category_name, meter[1], f"{base_index:,}".replace(",", " ")), tags=(meter_id,))

    def edit_base_index(self, event):
        """Permet d'éditer l'index de base directement dans le Treeview et recalcule les consommations."""
        selected = self.config_tree.selection()
        if not selected:
            return

        item = self.config_tree.item(selected[0])
        meter_id = item["tags"][0]
        column = self.config_tree.identify_column(event.x)
        if column != "#3":
            return

        entry = ttk.Entry(self.config_tree)
        entry.place(x=event.x, y=event.y, width=100)

        def save_edit(event):
            new_value = entry.get().replace(" ", "")
            if new_value.isdigit():
                new_value = int(new_value)
                self.cursor.execute("INSERT OR REPLACE INTO base_indices (meter_id, base_index) VALUES (?, ?)", (meter_id, new_value))
                self.conn.commit()
                self.update_all_consumptions(meter_id)  # Recalculer toutes les consommations
                self.load_config()
                if self.current_meter_id == meter_id:
                    self.load_readings()
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)
        entry.focus_set()

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = MeterReadingApp(root)
    root.mainloop()