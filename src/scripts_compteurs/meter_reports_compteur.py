import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from dateutil.relativedelta import relativedelta
import csv

class MeterReports:
    def __init__(self, parent, conn, graph_manager):
        self.parent = parent
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.graph_manager = graph_manager  # Référence à l'instance de MeterGraphs

        self.meters = self.load_meters()
        self.categories = self.load_categories()
        self.meter_to_category = {meter[0]: meter[3] for meter in self.meters}

        # Récupère la date actuelle pour définir les valeurs par défaut
        current_date = datetime.now()  # Date actuelle : 2025-04-09
        current_year = current_date.year  # 2025
        current_month = current_date.month  # 04
        previous_year = current_year - 1  # 2024

        self.compare_filter_frame = ttk.Frame(self.parent)
        self.compare_filter_frame.pack(fill="x", pady=5)

        ttk.Label(self.compare_filter_frame, text="Période 1 :").pack(side="left", padx=5)
        ttk.Label(self.compare_filter_frame, text="De :").pack(side="left", padx=5)
        self.compare1_start_month_var = tk.StringVar()
        self.compare1_start_month_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare1_start_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly")
        self.compare1_start_month_combobox.pack(side="left", padx=5)
        self.compare1_start_month_combobox.set("01")  # Mois de début : janvier

        self.compare1_start_year_var = tk.StringVar()
        self.compare1_start_year_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare1_start_year_var, values=[str(i) for i in range(2000, 2101)], width=7, state="readonly")
        self.compare1_start_year_combobox.pack(side="left", padx=5)
        self.compare1_start_year_combobox.set(str(previous_year))  # Année précédente : 2024

        ttk.Label(self.compare_filter_frame, text="À :").pack(side="left", padx=5)
        self.compare1_end_month_var = tk.StringVar()
        self.compare1_end_month_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare1_end_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly")
        self.compare1_end_month_combobox.pack(side="left", padx=5)
        self.compare1_end_month_combobox.set(f"{current_month:02d}")  # Mois en cours : 04

        self.compare1_end_year_var = tk.StringVar()
        self.compare1_end_year_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare1_end_year_var, values=[str(i) for i in range(2000, 2101)], width=7, state="readonly")
        self.compare1_end_year_combobox.pack(side="left", padx=5)
        self.compare1_end_year_combobox.set(str(previous_year))  # Année précédente : 2024

        ttk.Label(self.compare_filter_frame, text="Période 2 :").pack(side="left", padx=5)
        ttk.Label(self.compare_filter_frame, text="De :").pack(side="left", padx=5)
        self.compare2_start_month_var = tk.StringVar()
        self.compare2_start_month_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare2_start_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly")
        self.compare2_start_month_combobox.pack(side="left", padx=5)
        self.compare2_start_month_combobox.set("01")  # Mois de début : janvier

        self.compare2_start_year_var = tk.StringVar()
        self.compare2_start_year_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare2_start_year_var, values=[str(i) for i in range(2000, 2101)], width=7, state="readonly")
        self.compare2_start_year_combobox.pack(side="left", padx=5)
        self.compare2_start_year_combobox.set(str(current_year))  # Année en cours : 2025

        ttk.Label(self.compare_filter_frame, text="À :").pack(side="left", padx=5)
        self.compare2_end_month_var = tk.StringVar()
        self.compare2_end_month_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare2_end_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly")
        self.compare2_end_month_combobox.pack(side="left", padx=5)
        self.compare2_end_month_combobox.set(f"{current_month:02d}")  # Mois en cours : 04

        self.compare2_end_year_var = tk.StringVar()
        self.compare2_end_year_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare2_end_year_var, values=[str(i) for i in range(2000, 2101)], width=7, state="readonly")
        self.compare2_end_year_combobox.pack(side="left", padx=5)
        self.compare2_end_year_combobox.set(str(current_year))  # Année en cours : 2025

        ttk.Label(self.compare_filter_frame, text="Niveau de regroupement :").pack(side="left", padx=5)
        self.compare_grouping_var = tk.StringVar()
        self.compare_grouping_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare_grouping_var, values=["Niveau 1", "Niveau 2", "Niveau 3", "Niveau 4", "Niveau 5"], width=10, state="readonly")
        self.compare_grouping_combobox.pack(side="left", padx=5)
        self.compare_grouping_combobox.set("Niveau 5")

        ttk.Label(self.compare_filter_frame, text="Objectif (%):").pack(side="left", padx=5)
        self.target_var = tk.StringVar(value="5")
        self.target_entry = ttk.Entry(self.compare_filter_frame, textvariable=self.target_var, width=5)
        self.target_entry.pack(side="left", padx=5)

        self.monthly_comparison_var = tk.IntVar(value=1)
        self.monthly_comparison_checkbutton = ttk.Checkbutton(self.compare_filter_frame, text="Comparaison mois par mois", variable=self.monthly_comparison_var)
        self.monthly_comparison_checkbutton.pack(side="left", padx=10)

        ttk.Button(self.compare_filter_frame, text="Comparer", command=self.compare_periods).pack(side="left", padx=10)
        ttk.Button(self.compare_filter_frame, text="Exporter en CSV", command=self.export_to_csv).pack(side="left", padx=10)

        self.search_frame = ttk.Frame(self.parent)
        self.search_frame.pack(fill="x", pady=5)

        ttk.Label(self.search_frame, text="Rechercher Catégorie :").pack(side="left", padx=5)
        self.category_search_var = tk.StringVar()
        self.category_search_entry = ttk.Entry(self.search_frame, textvariable=self.category_search_var)
        self.category_search_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.category_search_entry.bind("<KeyRelease>", self.filter_treeview)

        ttk.Label(self.search_frame, text="Rechercher Compteur :").pack(side="left", padx=5)
        self.meter_search_var = tk.StringVar()
        self.meter_search_entry = ttk.Entry(self.search_frame, textvariable=self.meter_search_var)
        self.meter_search_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.meter_search_entry.bind("<KeyRelease>", self.filter_treeview)

        ttk.Button(self.search_frame, text="Réinitialiser le tri", command=self.reset_sorting).pack(side="left", padx=10)

        self.compare_tree = ttk.Treeview(self.parent, columns=("Month", "Category", "Meter", "Period1", "Period2", "Note2", "Difference", "TargetDiff"), show="headings")
        self.compare_tree.heading("Month", text="Mois", command=lambda: self.sort_column("Month", False))
        self.compare_tree.heading("Category", text="Catégorie", command=lambda: self.sort_column("Category", False))
        self.compare_tree.heading("Meter", text="Compteur", command=lambda: self.sort_column("Meter", False))
        self.compare_tree.heading("Period1", text="Période 1", command=lambda: self.sort_column("Period1", False))
        self.compare_tree.heading("Period2", text="Période 2", command=lambda: self.sort_column("Period2", False))
        self.compare_tree.heading("Note2", text="Note (Période 2)", command=lambda: self.sort_column("Note2", False))
        self.compare_tree.heading("Difference", text="Différence", command=lambda: self.sort_column("Difference", False))
        self.compare_tree.heading("TargetDiff", text="Écart Objectif (%)", command=lambda: self.sort_column("TargetDiff", False))
        self.compare_tree.column("Month", width=100)
        self.compare_tree.column("Category", width=200)
        self.compare_tree.column("Meter", width=150)
        self.compare_tree.column("Period1", width=100)
        self.compare_tree.column("Period2", width=100)
        self.compare_tree.column("Note2", width=150)
        self.compare_tree.column("Difference", width=100)
        self.compare_tree.column("TargetDiff", width=120)
        self.compare_tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.compare_tree.tag_configure("positive", background="#ffcccc")
        self.compare_tree.tag_configure("negative", background="#ccffcc")

        self.original_data = []

    def load_meters(self):
        self.cursor.execute("SELECT id, name, note, category_id FROM meters")
        return self.cursor.fetchall()

    def load_categories(self):
        self.cursor.execute("SELECT id, name, parent_id FROM categories")
        return self.cursor.fetchall()

    def get_category_hierarchy(self, category_id):
        if not category_id:
            return ["Aucune"]
        hierarchy = []
        current_id = category_id
        while current_id:
            self.cursor.execute("SELECT id, name, parent_id FROM categories WHERE id=?", (current_id,))
            cat = self.cursor.fetchone()
            if not cat:
                break
            hierarchy.append((cat[0], cat[1]))
            current_id = cat[2]
        return list(reversed(hierarchy))

    def get_category_name(self, category_id, max_level=None):
        hierarchy = self.get_category_hierarchy(category_id)
        if max_level is not None:
            hierarchy = hierarchy[:max_level]
        return " > ".join(name for _, name in hierarchy)

    def get_top_level_category(self, category_id):
        hierarchy = self.get_category_hierarchy(category_id)
        return hierarchy[0][1] if hierarchy else "Aucune"

    def sort_column(self, col, reverse):
        items = [(self.compare_tree.set(item, col), item) for item in self.compare_tree.get_children()]
        if col in ("Period1", "Period2", "Difference"):
            items.sort(key=lambda x: float(x[0].replace(" ", "").replace("+", "") if x[0] else "0"), reverse=reverse)
        elif col == "TargetDiff":
            items.sort(key=lambda x: float(x[0].replace("%", "").replace("+", "") if x[0] else "0"), reverse=reverse)
        else:
            items.sort(reverse=reverse)
        for index, (value, item) in enumerate(items):
            self.compare_tree.move(item, "", index)
        self.compare_tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def reset_sorting(self):
        for item in self.compare_tree.get_children():
            self.compare_tree.delete(item)
        for row in self.original_data:
            tags = []
            difference = row[6].replace(" ", "").replace("+", "")
            if difference and float(difference) > 0:
                tags.append("positive")
            elif difference and float(difference) < 0:
                tags.append("negative")
            self.compare_tree.insert("", tk.END, values=row, tags=tags)

    def filter_treeview(self, event):
        category_search = self.category_search_var.get().lower()
        meter_search = self.meter_search_var.get().lower()
        for item in self.compare_tree.get_children():
            self.compare_tree.delete(item)
        for row in self.original_data:
            if (not category_search or category_search in row[1].lower()) and (not meter_search or meter_search in row[2].lower()):
                tags = []
                difference = row[6].replace(" ", "").replace("+", "")
                if difference and float(difference) > 0:
                    tags.append("positive")
                elif difference and float(difference) < 0:
                    tags.append("negative")
                self.compare_tree.insert("", tk.END, values=row, tags=tags)

    def export_to_csv(self):
        if not self.compare_tree.get_children():
            messagebox.showwarning("Aucune donnée", "Aucune donnée à exporter. Veuillez d'abord comparer les périodes.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            title="Enregistrer sous",
            initialfile="comparaison_periodes.csv"
        )
        if not file_path:
            return
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file, delimiter=';')
                headers = [self.compare_tree.heading(col)["text"] for col in self.compare_tree["columns"]]
                writer.writerow(headers)
                for item in self.compare_tree.get_children():
                    row = self.compare_tree.item(item)["values"]
                    writer.writerow(row)
            messagebox.showinfo("Succès", f"Données exportées avec succès dans {file_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exportation : {str(e)}")

    def compare_periods(self):
        for item in self.compare_tree.get_children():
            self.compare_tree.delete(item)
        self.original_data.clear()

        period1_start_year = self.compare1_start_year_var.get()
        period1_start_month = self.compare1_start_month_var.get()
        period1_end_year = self.compare1_end_year_var.get()
        period1_end_month = self.compare1_end_month_var.get()
        period2_start_year = self.compare2_start_year_var.get()
        period2_start_month = self.compare2_start_month_var.get()
        period2_end_year = self.compare2_end_year_var.get()
        period2_end_month = self.compare2_end_month_var.get()

        try:
            period1_start_year = int(period1_start_year)
            period1_end_year = int(period1_end_year)
            period2_start_year = int(period2_start_year)
            period2_end_year = int(period2_end_year)
            if not (2000 <= period1_start_year <= 2100 and 2000 <= period1_end_year <= 2100 and
                    2000 <= period2_start_year <= 2100 and 2000 <= period2_end_year <= 2100):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Erreur", "Les années doivent être des nombres entiers entre 2000 et 2100.")
            return

        try:
            period1_start_month = int(period1_start_month)
            period1_end_month = int(period1_end_month)
            period2_start_month = int(period2_start_month)
            period2_end_month = int(period2_end_month)
            if not (1 <= period1_start_month <= 12 and 1 <= period1_end_month <= 12 and
                    1 <= period2_start_month <= 12 and 1 <= period2_end_month <= 12):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Erreur", "Les mois doivent être des nombres entiers entre 01 et 12.")
            return

        period1_start_date = f"{period1_start_year}-{period1_start_month:02d}"
        period1_end_date = f"{period1_end_year}-{period1_end_month:02d}"
        period2_start_date = f"{period2_start_year}-{period2_start_month:02d}"
        period2_end_date = f"{period2_end_year}-{period2_end_month:02d}"

        grouping_level = int(self.compare_grouping_var.get().split()[-1])

        try:
            target = float(self.target_var.get())
        except ValueError:
            messagebox.showwarning("Erreur", "L'objectif doit être un nombre.")
            return

        self.cursor.execute("SELECT meter_id, date, consumption FROM readings WHERE date BETWEEN ? AND ? ORDER BY date", (period1_start_date, period1_end_date))
        period1_readings = self.cursor.fetchall()
        self.cursor.execute("SELECT meter_id, date, consumption, note FROM readings WHERE date BETWEEN ? AND ? ORDER BY date", (period2_start_date, period2_end_date))
        period2_readings = self.cursor.fetchall()

        is_monthly = self.monthly_comparison_var.get() == 1

        if is_monthly:
            self.compare_tree["columns"] = ("Month", "Category", "Meter", "Period1", "Period2", "Note2", "Difference", "TargetDiff")
            self.compare_tree.heading("Month", text="Mois", command=lambda: self.sort_column("Month", False))
            self.compare_tree.heading("Category", text="Catégorie", command=lambda: self.sort_column("Category", False))
            self.compare_tree.heading("Meter", text="Compteur", command=lambda: self.sort_column("Meter", False))
            self.compare_tree.heading("Period1", text="Période 1", command=lambda: self.sort_column("Period1", False))
            self.compare_tree.heading("Period2", text="Période 2", command=lambda: self.sort_column("Period2", False))
            self.compare_tree.heading("Note2", text="Note (Période 2)", command=lambda: self.sort_column("Note2", False))
            self.compare_tree.heading("Difference", text="Différence", command=lambda: self.sort_column("Difference", False))
            self.compare_tree.heading("TargetDiff", text="Écart Objectif (%)", command=lambda: self.sort_column("TargetDiff", False))
            self.compare_tree.column("Month", width=100)
            self.compare_tree.column("Category", width=200)
            self.compare_tree.column("Meter", width=150)
            self.compare_tree.column("Period1", width=100)
            self.compare_tree.column("Period2", width=100)
            self.compare_tree.column("Note2", width=150)
            self.compare_tree.column("Difference", width=100)
            self.compare_tree.column("TargetDiff", width=120)

            meter_readings1 = {}
            for meter_id, date, consumption in period1_readings:
                if meter_id not in meter_readings1:
                    meter_readings1[meter_id] = {}
                month = date[:7]
                meter_readings1[meter_id][month] = consumption

            meter_readings2 = {}
            for meter_id, date, consumption, note in period2_readings:
                if meter_id not in meter_readings2:
                    meter_readings2[meter_id] = {}
                month = date[:7]
                meter_readings2[meter_id][month] = (consumption, note if note is not None else "")

            start_date1 = datetime.strptime(period1_start_date, "%Y-%m")
            end_date1 = datetime.strptime(period1_end_date, "%Y-%m")
            start_date2 = datetime.strptime(period2_start_date, "%Y-%m")
            end_date2 = datetime.strptime(period2_end_date, "%Y-%m")

            months_period1 = [(current_date.strftime("%Y-%m"), current_date.month) 
                              for current_date in [start_date1 + relativedelta(months=i) for i in range((end_date1.year - start_date1.year) * 12 + end_date1.month - start_date1.month + 1)]]
            months_period2 = [(current_date.strftime("%Y-%m"), current_date.month) 
                              for current_date in [start_date2 + relativedelta(months=i) for i in range((end_date2.year - start_date2.year) * 12 + end_date2.month - start_date2.month + 1)]]

            months_to_compare = [(month1, month2) for (month1, m1) in months_period1 for (month2, m2) in months_period2 if m1 == m2]
            if not months_to_compare:
                messagebox.showwarning("Erreur", "Les périodes sélectionnées ne contiennent pas de mois communs.")
                return

            meter_consumptions_by_month = {}
            for meter in self.meters:
                meter_id = meter[0]
                meter_consumptions_by_month[meter_id] = {}
                for month1, month2 in months_to_compare:
                    consumption1 = meter_readings1.get(meter_id, {}).get(month1, 0)
                    consumption2_data = meter_readings2.get(meter_id, {}).get(month2, (0, ""))
                    consumption2, note2 = consumption2_data if isinstance(consumption2_data, tuple) else (0, "")
                    meter_consumptions_by_month[meter_id][month1] = {"period1": consumption1}
                    meter_consumptions_by_month[meter_id][month2] = {"period2": (consumption2, note2)}

            category_totals_by_month1 = {}
            category_totals_by_month2 = {}
            top_level_totals_by_month1 = {}
            top_level_totals_by_month2 = {}
            graph_data_by_month = {}

            for month1, month2 in months_to_compare:
                category_totals_by_month1[month1] = {}
                category_totals_by_month2[month2] = {}
                top_level_totals_by_month1[month1] = {}
                top_level_totals_by_month2[month2] = {}
                graph_data_by_month[(month1, month2)] = {
                    "12": {"period1": {}, "period2": {}},
                    "34": {"period1": {}, "period2": {}},
                    "5": {"period1": {}, "period2": {}}
                }

            for meter in self.meters:
                meter_id = meter[0]
                category_id = meter[3]
                category_hierarchy = self.get_category_hierarchy(category_id)
                top_level_category = self.get_top_level_category(category_id)

                for month1, month2 in months_to_compare:
                    consumption1 = meter_consumptions_by_month.get(meter_id, {}).get(month1, {}).get("period1", 0)
                    consumption_data2 = meter_consumptions_by_month.get(meter_id, {}).get(month2, {}).get("period2", (0, ""))
                    consumption2, note2 = consumption_data2 if isinstance(consumption_data2, tuple) else (0, "")

                    if top_level_category not in top_level_totals_by_month1[month1]:
                        top_level_totals_by_month1[month1][top_level_category] = 0
                        top_level_totals_by_month2[month2][top_level_category] = 0
                    top_level_totals_by_month1[month1][top_level_category] += consumption1
                    top_level_totals_by_month2[month2][top_level_category] += consumption2

                    for level in range(1, len(category_hierarchy) + 1):
                        if level > grouping_level:
                            break
                        category_name = " > ".join(name for _, name in category_hierarchy[:level])
                        if category_name not in category_totals_by_month1[month1]:
                            category_totals_by_month1[month1][category_name] = {}
                            category_totals_by_month2[month2][category_name] = {}
                        if level not in category_totals_by_month1[month1][category_name]:
                            category_totals_by_month1[month1][category_name][level] = 0
                            category_totals_by_month2[month2][category_name][level] = 0
                        category_totals_by_month1[month1][category_name][level] += consumption1
                        category_totals_by_month2[month2][category_name][level] += consumption2

                        if level <= 2:
                            if category_name not in graph_data_by_month[(month1, month2)]["12"]["period1"]:
                                graph_data_by_month[(month1, month2)]["12"]["period1"][category_name] = 0
                                graph_data_by_month[(month1, month2)]["12"]["period2"][category_name] = 0
                            graph_data_by_month[(month1, month2)]["12"]["period1"][category_name] += consumption1
                            graph_data_by_month[(month1, month2)]["12"]["period2"][category_name] += consumption2
                        elif 3 <= level <= 4:
                            if category_name not in graph_data_by_month[(month1, month2)]["34"]["period1"]:
                                graph_data_by_month[(month1, month2)]["34"]["period1"][category_name] = 0
                                graph_data_by_month[(month1, month2)]["34"]["period2"][category_name] = 0
                            graph_data_by_month[(month1, month2)]["34"]["period1"][category_name] += consumption1
                            graph_data_by_month[(month1, month2)]["34"]["period2"][category_name] += consumption2

                    meter_name = meter[1]
                    if meter_name not in graph_data_by_month[(month1, month2)]["5"]["period1"]:
                        graph_data_by_month[(month1, month2)]["5"]["period1"][meter_name] = 0
                        graph_data_by_month[(month1, month2)]["5"]["period2"][meter_name] = 0
                    graph_data_by_month[(month1, month2)]["5"]["period1"][meter_name] += consumption1
                    graph_data_by_month[(month1, month2)]["5"]["period2"][meter_name] += consumption2

            grouped_by_top_level_by_month1 = {}
            grouped_by_top_level_by_month2 = {}
            for month1, month2 in months_to_compare:
                grouped_by_top_level_by_month1[month1] = {}
                grouped_by_top_level_by_month2[month2] = {}
                for category_name, levels in category_totals_by_month1[month1].items():
                    top_level = category_name.split(" > ")[0]
                    if top_level not in grouped_by_top_level_by_month1[month1]:
                        grouped_by_top_level_by_month1[month1][top_level] = {}
                        grouped_by_top_level_by_month2[month2][top_level] = {}
                    for level in levels:
                        if level not in grouped_by_top_level_by_month1[month1][top_level]:
                            grouped_by_top_level_by_month1[month1][top_level][level] = {}
                            grouped_by_top_level_by_month2[month2][top_level][level] = {}
                        grouped_by_top_level_by_month1[month1][top_level][level][category_name] = category_totals_by_month1[month1][category_name][level]
                        grouped_by_top_level_by_month2[month2][top_level][level][category_name] = category_totals_by_month2[month2][category_name][level]

            for month1, month2 in months_to_compare:
                for top_level_category in sorted(grouped_by_top_level_by_month1[month1].keys()):
                    categories_by_level1 = grouped_by_top_level_by_month1[month1][top_level_category]
                    categories_by_level2 = grouped_by_top_level_by_month2[month2][top_level_category]

                    if grouping_level == 5:
                        meter_list = []
                        for meter in self.meters:
                            meter_id = meter[0]
                            consumption1 = meter_consumptions_by_month.get(meter_id, {}).get(month1, {}).get("period1", 0)
                            consumption_data2 = meter_consumptions_by_month.get(meter_id, {}).get(month2, {}).get("period2", (0, ""))
                            consumption2, note2 = consumption_data2 if isinstance(consumption_data2, tuple) else (0, "")
                            category_id = meter[3]
                            meter_top_level = self.get_top_level_category(category_id)
                            if meter_top_level != top_level_category:
                                continue
                            difference = consumption2 - consumption1
                            target_diff = ((consumption2 - consumption1) / consumption1 * 100) if consumption1 > 0 else (float('inf') if consumption2 > 0 else 0)
                            category_name = self.get_category_name(category_id, max_level=grouping_level)
                            meter_list.append((category_name, meter[1], consumption1, consumption2, note2, difference, target_diff))

                        meter_list.sort(key=lambda x: (-x[0].count(">"), x[0], x[1]))
                        for category_name, meter_name, consumption1, consumption2, note2, difference, target_diff in meter_list:
                            row = (
                                f"{month1} vs {month2}",
                                category_name,
                                meter_name,
                                f"{consumption1:,}".replace(",", " "),
                                f"{consumption2:,}".replace(",", " "),
                                note2,
                                f"{difference:+,}".replace(",", " "),
                                f"{target_diff:+.2f}%"
                            )
                            tags = []
                            if difference > 0:
                                tags.append("positive")
                            elif difference < 0:
                                tags.append("negative")
                            self.compare_tree.insert("", tk.END, values=row, tags=tags)
                            self.original_data.append(row)

                    if grouping_level > 1:
                        category_list = []
                        for level in sorted(categories_by_level1.keys()):
                            if level > grouping_level:
                                continue
                            for category_name in categories_by_level1[level]:
                                if category_name == top_level_category and level == 1:
                                    continue
                                total1 = categories_by_level1[level][category_name]
                                total2 = categories_by_level2[level][category_name]
                                difference = total2 - total1
                                target_diff = ((total2 - total1) / total1 * 100) if total1 > 0 else (float('inf') if total2 > 0 else 0)
                                category_list.append((category_name, total1, total2, "", difference, target_diff))

                        category_list.sort(key=lambda x: (-x[0].count(">"), x[0]))
                        for category_name, total1, total2, note2, difference, target_diff in category_list:
                            row = (
                                f"{month1} vs {month2}",
                                category_name,
                                "Sous-total",
                                f"{total1:,}".replace(",", " "),
                                f"{total2:,}".replace(",", " "),
                                note2,
                                f"{difference:+,}".replace(",", " "),
                                f"{target_diff:+.2f}%"
                            )
                            tags = []
                            if difference > 0:
                                tags.append("positive")
                            elif difference < 0:
                                tags.append("negative")
                            self.compare_tree.insert("", tk.END, values=row, tags=tags)
                            self.original_data.append(row)

                    total1 = top_level_totals_by_month1[month1][top_level_category]
                    total2 = top_level_totals_by_month2[month2][top_level_category]
                    difference = total2 - total1
                    target_diff = ((total2 - total1) / total1 * 100) if total1 > 0 else (float('inf') if total2 > 0 else 0)
                    row = (
                        f"{month1} vs {month2}",
                        top_level_category,
                        "Total",
                        f"{total1:,}".replace(",", " "),
                        f"{total2:,}".replace(",", " "),
                        "",
                        f"{difference:+,}".replace(",", " "),
                        f"{target_diff:+.2f}%"
                    )
                    tags = []
                    if difference > 0:
                        tags.append("positive")
                    elif difference < 0:
                        tags.append("negative")
                    self.compare_tree.insert("", tk.END, values=row, tags=tags)
                    self.original_data.append(row)

            # Passe les données à l'onglet Graphiques
            self.graph_manager.update_data(
                grouping_level, graph_data_by_month, period1_start_date, period1_end_date,
                period2_start_date, period2_end_date, is_monthly=True
            )

        else:
            self.compare_tree["columns"] = ("Category", "Meter", "Period1", "Period2", "Note2", "Difference", "TargetDiff")
            self.compare_tree.heading("Category", text="Catégorie", command=lambda: self.sort_column("Category", False))
            self.compare_tree.heading("Meter", text="Compteur", command=lambda: self.sort_column("Meter", False))
            self.compare_tree.heading("Period1", text="Période 1", command=lambda: self.sort_column("Period1", False))
            self.compare_tree.heading("Period2", text="Période 2", command=lambda: self.sort_column("Period2", False))
            self.compare_tree.heading("Note2", text="Note (Période 2)", command=lambda: self.sort_column("Note2", False))
            self.compare_tree.heading("Difference", text="Différence", command=lambda: self.sort_column("Difference", False))
            self.compare_tree.heading("TargetDiff", text="Écart Objectif (%)", command=lambda: self.sort_column("TargetDiff", False))
            self.compare_tree.column("Category", width=200)
            self.compare_tree.column("Meter", width=150)
            self.compare_tree.column("Period1", width=100)
            self.compare_tree.column("Period2", width=100)
            self.compare_tree.column("Note2", width=150)
            self.compare_tree.column("Difference", width=100)
            self.compare_tree.column("TargetDiff", width=120)

            meter_consumptions1 = {}
            for meter_id, date, consumption in period1_readings:
                meter_consumptions1[meter_id] = meter_consumptions1.get(meter_id, 0) + consumption

            meter_consumptions2 = {}
            last_notes = {}
            for meter_id, date, consumption, note in period2_readings:
                meter_consumptions2[meter_id] = meter_consumptions2.get(meter_id, 0) + consumption
                last_notes[meter_id] = note if note is not None else ""

            category_totals_by_level1 = {}
            category_totals_by_level2 = {}
            top_level_totals1 = {}
            top_level_totals2 = {}
            graph_data_12_1 = {}
            graph_data_12_2 = {}
            graph_data_34_1 = {}
            graph_data_34_2 = {}
            graph_data_5_1 = {}
            graph_data_5_2 = {}

            for meter in self.meters:
                meter_id = meter[0]
                consumption1 = meter_consumptions1.get(meter_id, 0)
                consumption2 = meter_consumptions2.get(meter_id, 0)
                note2 = last_notes.get(meter_id, "")
                if consumption1 == 0 and consumption2 == 0:
                    continue

                category_id = meter[3]
                category_hierarchy = self.get_category_hierarchy(category_id)
                top_level_category = self.get_top_level_category(category_id)

                if top_level_category not in top_level_totals1:
                    top_level_totals1[top_level_category] = 0
                    top_level_totals2[top_level_category] = 0
                top_level_totals1[top_level_category] += consumption1
                top_level_totals2[top_level_category] += consumption2

                for level in range(1, len(category_hierarchy) + 1):
                    if level > grouping_level:
                        break
                    category_name = " > ".join(name for _, name in category_hierarchy[:level])
                    if category_name not in category_totals_by_level1:
                        category_totals_by_level1[category_name] = {}
                        category_totals_by_level2[category_name] = {}
                    if level not in category_totals_by_level1[category_name]:
                        category_totals_by_level1[category_name][level] = 0
                        category_totals_by_level2[category_name][level] = 0
                    category_totals_by_level1[category_name][level] += consumption1
                    category_totals_by_level2[category_name][level] += consumption2

                    if level <= 2:
                        if category_name not in graph_data_12_1:
                            graph_data_12_1[category_name] = 0
                            graph_data_12_2[category_name] = 0
                        graph_data_12_1[category_name] += consumption1
                        graph_data_12_2[category_name] += consumption2
                    elif 3 <= level <= 4:
                        if category_name not in graph_data_34_1:
                            graph_data_34_1[category_name] = 0
                            graph_data_34_2[category_name] = 0
                        graph_data_34_1[category_name] += consumption1
                        graph_data_34_2[category_name] += consumption2

                meter_name = meter[1]
                if meter_name not in graph_data_5_1:
                    graph_data_5_1[meter_name] = 0
                    graph_data_5_2[meter_name] = 0
                graph_data_5_1[meter_name] += consumption1
                graph_data_5_2[meter_name] += consumption2

            grouped_by_top_level1 = {}
            grouped_by_top_level2 = {}
            for category_name, levels in category_totals_by_level1.items():
                top_level = category_name.split(" > ")[0]
                if top_level not in grouped_by_top_level1:
                    grouped_by_top_level1[top_level] = {}
                    grouped_by_top_level2[top_level] = {}
                for level in levels:
                    if level not in grouped_by_top_level1[top_level]:
                        grouped_by_top_level1[top_level][level] = {}
                        grouped_by_top_level2[top_level][level] = {}
                    grouped_by_top_level1[top_level][level][category_name] = category_totals_by_level1[category_name][level]
                    grouped_by_top_level2[top_level][level][category_name] = category_totals_by_level2[category_name][level]

            for top_level_category in sorted(grouped_by_top_level1.keys()):
                categories_by_level1 = grouped_by_top_level1[top_level_category]
                categories_by_level2 = grouped_by_top_level2[top_level_category]

                if grouping_level == 5:
                    meter_list = []
                    for meter in self.meters:
                        meter_id = meter[0]
                        consumption1 = meter_consumptions1.get(meter_id, 0)
                        consumption2 = meter_consumptions2.get(meter_id, 0)
                        note2 = last_notes.get(meter_id, "")
                        if consumption1 == 0 and consumption2 == 0:
                            continue
                        category_id = meter[3]
                        meter_top_level = self.get_top_level_category(category_id)
                        if meter_top_level != top_level_category:
                            continue
                        difference = consumption2 - consumption1
                        target_diff = ((consumption2 - consumption1) / consumption1 * 100) if consumption1 > 0 else (float('inf') if consumption2 > 0 else 0)
                        category_name = self.get_category_name(category_id, max_level=grouping_level)
                        meter_list.append((category_name, meter[1], consumption1, consumption2, note2, difference, target_diff))

                    meter_list.sort(key=lambda x: (-x[0].count(">"), x[0], x[1]))
                    for category_name, meter_name, consumption1, consumption2, note2, difference, target_diff in meter_list:
                        row = (
                            category_name,
                            meter_name,
                            f"{consumption1:,}".replace(",", " "),
                            f"{consumption2:,}".replace(",", " "),
                            note2,
                            f"{difference:+,}".replace(",", " "),
                            f"{target_diff:+.2f}%"
                        )
                        tags = []
                        if difference > 0:
                            tags.append("positive")
                        elif difference < 0:
                            tags.append("negative")
                        self.compare_tree.insert("", tk.END, values=row, tags=tags)
                        self.original_data.append(row)

                if grouping_level > 1:
                    category_list = []
                    for level in sorted(categories_by_level1.keys()):
                        if level > grouping_level:
                            continue
                        for category_name in categories_by_level1[level]:
                            if category_name == top_level_category and level == 1:
                                continue
                            total1 = categories_by_level1[level][category_name]
                            total2 = categories_by_level2[level][category_name]
                            difference = total2 - total1
                            target_diff = ((total2 - total1) / total1 * 100) if total1 > 0 else (float('inf') if total2 > 0 else 0)
                            category_list.append((category_name, total1, total2, "", difference, target_diff))

                    category_list.sort(key=lambda x: (-x[0].count(">"), x[0]))
                    for category_name, total1, total2, note2, difference, target_diff in category_list:
                        row = (
                            category_name,
                            "Sous-total",
                            f"{total1:,}".replace(",", " "),
                            f"{total2:,}".replace(",", " "),
                            note2,
                            f"{difference:+,}".replace(",", " "),
                            f"{target_diff:+.2f}%"
                        )
                        tags = []
                        if difference > 0:
                            tags.append("positive")
                        elif difference < 0:
                            tags.append("negative")
                        self.compare_tree.insert("", tk.END, values=row, tags=tags)
                        self.original_data.append(row)

                total1 = top_level_totals1[top_level_category]
                total2 = top_level_totals2[top_level_category]
                difference = total2 - total1
                target_diff = ((total2 - total1) / total1 * 100) if total1 > 0 else (float('inf') if total2 > 0 else 0)
                row = (
                    top_level_category,
                    "Total",
                    f"{total1:,}".replace(",", " "),
                    f"{total2:,}".replace(",", " "),
                    "",
                    f"{difference:+,}".replace(",", " "),
                    f"{target_diff:+.2f}%"
                )
                tags = []
                if difference > 0:
                    tags.append("positive")
                elif difference < 0:
                    tags.append("negative")
                self.compare_tree.insert("", tk.END, values=row, tags=tags)
                self.original_data.append(row)

            # Passe les données à l'onglet Graphiques
            self.graph_manager.update_data(
                grouping_level, None, period1_start_date, period1_end_date,
                period2_start_date, period2_end_date, is_monthly=False,
                graph_data_cumulative={
                    "12": {"period1": graph_data_12_1, "period2": graph_data_12_2},
                    "34": {"period1": graph_data_34_1, "period2": graph_data_34_2},
                    "5": {"period1": graph_data_5_1, "period2": graph_data_5_2}
                }
            )