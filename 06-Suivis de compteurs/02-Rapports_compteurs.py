import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import csv

class MeterConsumptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analyse des Consommations de Compteurs")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#e1e1e1", foreground="#333333")
        style.configure("TButton", background="#4CAF50", foreground="white")
        style.configure("TEntry", fieldbackground="#ffffff")
        style.configure("TCombobox", fieldbackground="#ffffff")
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        self.conn = sqlite3.connect("meters.db")
        self.cursor = self.conn.cursor()

        self.meters = self.load_meters()
        self.categories = self.load_categories()
        self.meter_to_category = {meter[0]: meter[3] for meter in self.meters}

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.compare_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.compare_frame, text="Comparer les Périodes")
        self.setup_compare_tab()

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

    def setup_compare_tab(self):
        self.compare_filter_frame = ttk.Frame(self.compare_frame)
        self.compare_filter_frame.pack(fill="x", pady=5)

        ttk.Label(self.compare_filter_frame, text="Période 1 :").pack(side="left", padx=5)
        ttk.Label(self.compare_filter_frame, text="De :").pack(side="left", padx=5)
        self.compare1_start_month_var = tk.StringVar()
        self.compare1_start_month_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare1_start_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly")
        self.compare1_start_month_combobox.pack(side="left", padx=5)
        self.compare1_start_month_combobox.set("01")

        self.compare1_start_year_var = tk.StringVar()
        self.compare1_start_year_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare1_start_year_var, values=[str(i) for i in range(2000, 2101)], width=7, state="readonly")
        self.compare1_start_year_combobox.pack(side="left", padx=5)
        self.compare1_start_year_combobox.set("2023")

        ttk.Label(self.compare_filter_frame, text="À :").pack(side="left", padx=5)
        self.compare1_end_month_var = tk.StringVar()
        self.compare1_end_month_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare1_end_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly")
        self.compare1_end_month_combobox.pack(side="left", padx=5)
        self.compare1_end_month_combobox.set("06")

        self.compare1_end_year_var = tk.StringVar()
        self.compare1_end_year_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare1_end_year_var, values=[str(i) for i in range(2000, 2101)], width=7, state="readonly")
        self.compare1_end_year_combobox.pack(side="left", padx=5)
        self.compare1_end_year_combobox.set("2023")

        ttk.Label(self.compare_filter_frame, text="Période 2 :").pack(side="left", padx=5)
        ttk.Label(self.compare_filter_frame, text="De :").pack(side="left", padx=5)
        self.compare2_start_month_var = tk.StringVar()
        self.compare2_start_month_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare2_start_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly")
        self.compare2_start_month_combobox.pack(side="left", padx=5)
        self.compare2_start_month_combobox.set("01")

        self.compare2_start_year_var = tk.StringVar()
        self.compare2_start_year_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare2_start_year_var, values=[str(i) for i in range(2000, 2101)], width=7, state="readonly")
        self.compare2_start_year_combobox.pack(side="left", padx=5)
        self.compare2_start_year_combobox.set("2024")

        ttk.Label(self.compare_filter_frame, text="À :").pack(side="left", padx=5)
        self.compare2_end_month_var = tk.StringVar()
        self.compare2_end_month_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare2_end_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly")
        self.compare2_end_month_combobox.pack(side="left", padx=5)
        self.compare2_end_month_combobox.set("06")

        self.compare2_end_year_var = tk.StringVar()
        self.compare2_end_year_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare2_end_year_var, values=[str(i) for i in range(2000, 2101)], width=7, state="readonly")
        self.compare2_end_year_combobox.pack(side="left", padx=5)
        self.compare2_end_year_combobox.set("2024")

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

        self.compare_tree = ttk.Treeview(self.compare_frame, columns=("Month", "Category", "Meter", "Period1", "Period2", "Note2", "Difference", "TargetDiff"), show="headings")
        self.compare_tree.heading("Month", text="Mois")
        self.compare_tree.heading("Category", text="Catégorie")
        self.compare_tree.heading("Meter", text="Compteur")
        self.compare_tree.heading("Period1", text="Période 1")
        self.compare_tree.heading("Period2", text="Période 2")
        self.compare_tree.heading("Note2", text="Note (Période 2)")
        self.compare_tree.heading("Difference", text="Différence")
        self.compare_tree.heading("TargetDiff", text="Écart Objectif (%)")
        self.compare_tree.column("Month", width=100)
        self.compare_tree.column("Category", width=200)
        self.compare_tree.column("Meter", width=150)
        self.compare_tree.column("Period1", width=100)
        self.compare_tree.column("Period2", width=100)
        self.compare_tree.column("Note2", width=150)
        self.compare_tree.column("Difference", width=100)
        self.compare_tree.column("TargetDiff", width=120)
        self.compare_tree.pack(fill="both", expand=True, padx=5, pady=5)

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

        # Récupérer les consommations au lieu des index
        self.cursor.execute("SELECT meter_id, date, consumption FROM readings WHERE date BETWEEN ? AND ? ORDER BY date", (period1_start_date, period1_end_date))
        period1_readings = self.cursor.fetchall()
        self.cursor.execute("SELECT meter_id, date, consumption, note FROM readings WHERE date BETWEEN ? AND ? ORDER BY date", (period2_start_date, period2_end_date))
        period2_readings = self.cursor.fetchall()

        is_monthly = self.monthly_comparison_var.get() == 1

        if is_monthly:
            self.compare_tree["columns"] = ("Month", "Category", "Meter", "Period1", "Period2", "Note2", "Difference", "TargetDiff")
            self.compare_tree.heading("Month", text="Mois")
            self.compare_tree.heading("Category", text="Catégorie")
            self.compare_tree.heading("Meter", text="Compteur")
            self.compare_tree.heading("Period1", text="Période 1")
            self.compare_tree.heading("Period2", text="Période 2")
            self.compare_tree.heading("Note2", text="Note (Période 2)")
            self.compare_tree.heading("Difference", text="Différence")
            self.compare_tree.heading("TargetDiff", text="Écart Objectif (%)")
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
                            self.compare_tree.insert("", tk.END, values=(
                                f"{month1} vs {month2}",
                                category_name,
                                meter_name,
                                f"{consumption1:,}".replace(",", " "),
                                f"{consumption2:,}".replace(",", " "),
                                note2,
                                f"{difference:+,}".replace(",", " "),
                                f"{target_diff:+.2f}%"
                            ))

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
                            self.compare_tree.insert("", tk.END, values=(
                                f"{month1} vs {month2}",
                                category_name,
                                "Sous-total",
                                f"{total1:,}".replace(",", " "),
                                f"{total2:,}".replace(",", " "),
                                note2,
                                f"{difference:+,}".replace(",", " "),
                                f"{target_diff:+.2f}%"
                            ))

                    total1 = top_level_totals_by_month1[month1][top_level_category]
                    total2 = top_level_totals_by_month2[month2][top_level_category]
                    difference = total2 - total1
                    target_diff = ((total2 - total1) / total1 * 100) if total1 > 0 else (float('inf') if total2 > 0 else 0)
                    self.compare_tree.insert("", tk.END, values=(
                        f"{month1} vs {month2}",
                        top_level_category,
                        "Total",
                        f"{total1:,}".replace(",", " "),
                        f"{total2:,}".replace(",", " "),
                        "",
                        f"{difference:+,}".replace(",", " "),
                        f"{target_diff:+.2f}%"
                    ))

            self.show_graphs_in_new_window(grouping_level, graph_data_by_month, period1_start_date, period1_end_date, period2_start_date, period2_end_date, is_monthly=True)

        else:
            self.compare_tree["columns"] = ("Category", "Meter", "Period1", "Period2", "Note2", "Difference", "TargetDiff")
            self.compare_tree.heading("Category", text="Catégorie")
            self.compare_tree.heading("Meter", text="Compteur")
            self.compare_tree.heading("Period1", text="Période 1")
            self.compare_tree.heading("Period2", text="Période 2")
            self.compare_tree.heading("Note2", text="Note (Période 2)")
            self.compare_tree.heading("Difference", text="Différence")
            self.compare_tree.heading("TargetDiff", text="Écart Objectif (%)")
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
                        self.compare_tree.insert("", tk.END, values=(
                            category_name,
                            meter_name,
                            f"{consumption1:,}".replace(",", " "),
                            f"{consumption2:,}".replace(",", " "),
                            note2,
                            f"{difference:+,}".replace(",", " "),
                            f"{target_diff:+.2f}%"
                        ))

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
                        self.compare_tree.insert("", tk.END, values=(
                            category_name,
                            "Sous-total",
                            f"{total1:,}".replace(",", " "),
                            f"{total2:,}".replace(",", " "),
                            note2,
                            f"{difference:+,}".replace(",", " "),
                            f"{target_diff:+.2f}%"
                        ))

                total1 = top_level_totals1[top_level_category]
                total2 = top_level_totals2[top_level_category]
                difference = total2 - total1
                target_diff = ((total2 - total1) / total1 * 100) if total1 > 0 else (float('inf') if total2 > 0 else 0)
                self.compare_tree.insert("", tk.END, values=(
                    top_level_category,
                    "Total",
                    f"{total1:,}".replace(",", " "),
                    f"{total2:,}".replace(",", " "),
                    "",
                    f"{difference:+,}".replace(",", " "),
                    f"{target_diff:+.2f}%"
                ))

            self.show_graphs_in_new_window(grouping_level, None, period1_start_date, period1_end_date, period2_start_date, period2_end_date, is_monthly=False, graph_data_cumulative={
                "12": {"period1": graph_data_12_1, "period2": graph_data_12_2},
                "34": {"period1": graph_data_34_1, "period2": graph_data_34_2},
                "5": {"period1": graph_data_5_1, "period2": graph_data_5_2}
            })

    def show_graphs_in_new_window(self, grouping_level, graph_data_by_month, period1_start_date, period1_end_date, period2_start_date, period2_end_date, is_monthly=True, graph_data_cumulative=None):
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Graphique de Comparaison")
        graph_window.resizable(True, True)
        graph_window.geometry("1000x900")

        main_pane = ttk.PanedWindow(graph_window, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True)

        graph_container = ttk.Frame(main_pane)
        main_pane.add(graph_container, weight=3)

        stats_frame = ttk.Frame(main_pane)
        main_pane.add(stats_frame, weight=1)

        level_frame = ttk.LabelFrame(stats_frame, text="Niveau d'Affichage")
        level_frame.pack(fill="x", padx=5, pady=5)

        display_level_var = tk.StringVar(value="Niveau 2")
        display_level_combobox = ttk.Combobox(level_frame, textvariable=display_level_var, values=["Niveau 1", "Niveau 2", "Niveau 3", "Niveau 4", "Niveau 5"], state="readonly")
        display_level_combobox.pack(fill="x", padx=5, pady=2)

        filter_frame = ttk.LabelFrame(stats_frame, text="Filtrer par Catégorie")
        filter_frame.pack(fill="x", padx=5, pady=5)

        filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=filter_var)
        filter_entry.pack(fill="x", padx=5, pady=2)

        label_frame = ttk.LabelFrame(stats_frame, text="Options d'Affichage")
        label_frame.pack(fill="x", padx=5, pady=5)

        show_labels_var = tk.BooleanVar(value=True)
        show_labels_checkbutton = ttk.Checkbutton(label_frame, text="Afficher les étiquettes", variable=show_labels_var)
        show_labels_checkbutton.pack(fill="x", padx=5, pady=2)

        stats_label_frame = ttk.LabelFrame(stats_frame, text="Résumé Statistique")
        stats_label_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.stats_text = tk.Text(stats_label_frame, height=10, width=30)
        self.stats_text.pack(fill="both", expand=True, padx=5, pady=5)

        fig, ax = plt.subplots(figsize=(8, 6))
        canvas = FigureCanvasTkAgg(fig, master=graph_container)
        toolbar = NavigationToolbar2Tk(canvas, graph_container)
        toolbar.update()
        toolbar.pack(fill="x")
        canvas.get_tk_widget().pack(fill="both", expand=True)

        self.color1 = "skyblue"
        self.color2 = "lightcoral"

        filter_trace_id = None
        display_level_trace_id = None
        show_labels_trace_id = None

        def update_graph():
            if not graph_window.winfo_exists():
                return

            ax.clear()

            display_level = display_level_var.get()
            level_num = int(display_level.split()[-1])
            title = f"Consommation Niveau {level_num} ({'Mois par Mois' if is_monthly else 'Cumul'})"

            if is_monthly:
                filter_text = filter_var.get().lower()
                filtered_data = {}
                for month_pair in graph_data_by_month:
                    month1, month2 = month_pair
                    filtered_data[month_pair] = {
                        "12": {"period1": {}, "period2": {}},
                        "34": {"period1": {}, "period2": {}},
                        "5": {"period1": {}, "period2": {}}
                    }
                    for level in ["12", "34", "5"]:
                        for period in ["period1", "period2"]:
                            for cat, val in graph_data_by_month[month_pair][level][period].items():
                                if filter_text in cat.lower():
                                    filtered_data[month_pair][level][period][cat] = val

                month_pairs = sorted(graph_data_by_month.keys(), key=lambda x: x[0])
                categories = set()
                if level_num <= 2:
                    data_source = "12"
                elif 3 <= level_num <= 4:
                    data_source = "34"
                else:
                    data_source = "5"

                for month_pair in month_pairs:
                    for cat in filtered_data[month_pair][data_source]["period1"].keys():
                        if level_num == 5:
                            categories.add(cat)
                        else:
                            cat_level = cat.count(" > ") + 1
                            if cat_level == level_num:
                                categories.add(cat)
                    for cat in filtered_data[month_pair][data_source]["period2"].keys():
                        if level_num == 5:
                            categories.add(cat)
                        else:
                            cat_level = cat.count(" > ") + 1
                            if cat_level == level_num:
                                categories.add(cat)
                categories = sorted(categories)

                if not categories:
                    ax.text(0.5, 0.5, "Aucune donnée pour ce niveau", ha='center', va='center', fontsize=12, color='red')
                    ax.set_xticks([])
                    ax.set_yticks([])
                    ax.set_title(title)
                    ax.set_ylabel("Consommation")
                    fig.tight_layout()
                    canvas.draw()
                    if self.stats_text.winfo_exists():
                        self.stats_text.delete(1.0, tk.END)
                        self.stats_text.insert(tk.END, f"{display_level}:\n")
                        self.stats_text.insert(tk.END, "Aucune donnée pour ce niveau.\n")
                    return

                x = np.arange(len(month_pairs))
                bar_width = 0.35 / len(categories)
                colors = plt.cm.tab20(np.linspace(0, 1, len(categories)))

                max_height = 0
                for cat in categories:
                    values_1 = [filtered_data[month_pair][data_source]["period1"].get(cat, 0) for month_pair in month_pairs]
                    values_2 = [filtered_data[month_pair][data_source]["period2"].get(cat, 0) for month_pair in month_pairs]
                    max_height = max(max_height, max(values_1 + values_2, default=0))

                for i, cat in enumerate(categories):
                    values_1 = [filtered_data[month_pair][data_source]["period1"].get(cat, 0) for month_pair in month_pairs]
                    values_2 = [filtered_data[month_pair][data_source]["period2"].get(cat, 0) for month_pair in month_pairs]
                    bars1 = ax.bar(x - bar_width * len(categories)/2 + i*bar_width, values_1, bar_width, label=f"{cat} - Période 1", color=colors[i], alpha=0.8)
                    bars2 = ax.bar(x - bar_width * len(categories)/2 + i*bar_width + bar_width/2, values_2, bar_width, label=f"{cat} - Période 2", color=colors[i], alpha=0.4)

                    if show_labels_var.get():
                        for j, (bar, value) in enumerate(zip(bars1, values_1)):
                            if value > 0:
                                offset = (i % 2) * 0.1 * max_height
                                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + offset, f"{cat}: {int(value):,}", 
                                        ha='center', va='bottom', fontsize=6, rotation=90)

                        for j, (bar, value) in enumerate(zip(bars2, values_2)):
                            if value > 0:
                                offset = ((i + 1) % 2) * 0.1 * max_height
                                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + offset, f"{cat}: {int(value):,}", 
                                        ha='center', va='bottom', fontsize=6, rotation=90)

                ax.set_ylim(0, max_height * 1.3)
                ax.set_xticks(x)
                ax.set_xticklabels([f"{month1} vs {month2}" for month1, month2 in month_pairs], rotation=45, ha="right")
                ax.set_title(title)
                ax.set_ylabel("Consommation")
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
                fig.tight_layout()
                canvas.draw()

                if self.stats_text.winfo_exists():
                    self.stats_text.delete(1.0, tk.END)
                    for month_pair in month_pairs:
                        month1, month2 = month_pair
                        if level_num <= 2:
                            data_source = "12"
                        elif 3 <= level_num <= 4:
                            data_source = "34"
                        else:
                            data_source = "5"
                        if level_num == 5:
                            stats_values_1 = list(graph_data_by_month[month_pair][data_source]["period1"].values())
                            stats_values_2 = list(graph_data_by_month[month_pair][data_source]["period2"].values())
                        else:
                            stats_values_1 = [val for cat, val in graph_data_by_month[month_pair][data_source]["period1"].items() if (cat.count(" > ") + 1) == level_num]
                            stats_values_2 = [val for cat, val in graph_data_by_month[month_pair][data_source]["period2"].items() if (cat.count(" > ") + 1) == level_num]
                        mean_1 = np.mean(stats_values_1) if stats_values_1 else 0
                        mean_2 = np.mean(stats_values_2) if stats_values_2 else 0
                        self.stats_text.insert(tk.END, f"{month1} vs {month2} ({display_level}):\n")
                        self.stats_text.insert(tk.END, f"Période 1 - Moyenne: {mean_1:,.2f}\n")
                        self.stats_text.insert(tk.END, f"Période 2 - Moyenne: {mean_2:,.2f}\n\n")

            else:
                filter_text = filter_var.get().lower()
                filtered_data = {
                    "12": {"period1": {}, "period2": {}},
                    "34": {"period1": {}, "period2": {}},
                    "5": {"period1": {}, "period2": {}}
                }
                for level in ["12", "34", "5"]:
                    for period in ["period1", "period2"]:
                        for cat, val in graph_data_cumulative[level][period].items():
                            if filter_text in cat.lower():
                                filtered_data[level][period][cat] = val

                categories = set()
                if level_num <= 2:
                    data_source = "12"
                elif 3 <= level_num <= 4:
                    data_source = "34"
                else:
                    data_source = "5"

                for cat in filtered_data[data_source]["period1"].keys():
                    if level_num == 5:
                        categories.add(cat)
                    else:
                        cat_level = cat.count(" > ") + 1
                        if cat_level == level_num:
                            categories.add(cat)
                for cat in filtered_data[data_source]["period2"].keys():
                    if level_num == 5:
                        categories.add(cat)
                    else:
                        cat_level = cat.count(" > ") + 1
                        if cat_level == level_num:
                            categories.add(cat)
                categories = sorted(categories)

                if not categories:
                    ax.text(0.5, 0.5, "Aucune donnée pour ce niveau", ha='center', va='center', fontsize=12, color='red')
                    ax.set_xticks([])
                    ax.set_yticks([])
                    ax.set_title(title)
                    ax.set_ylabel("Consommation")
                    fig.tight_layout()
                    canvas.draw()
                    if self.stats_text.winfo_exists():
                        self.stats_text.delete(1.0, tk.END)
                        self.stats_text.insert(tk.END, f"{display_level}:\n")
                        self.stats_text.insert(tk.END, "Aucune donnée pour ce niveau.\n")
                    return

                x = np.arange(len(categories))
                bar_width = 0.35
                values_1 = [filtered_data[data_source]["period1"].get(cat, 0) for cat in categories]
                values_2 = [filtered_data[data_source]["period2"].get(cat, 0) for cat in categories]
                bars1 = ax.bar(x - bar_width/2, values_1, bar_width, label="Période 1", color=self.color1)
                bars2 = ax.bar(x + bar_width/2, values_2, bar_width, label="Période 2", color=self.color2)

                max_height = max(max(values_1, default=0), max(values_2, default=0))

                if show_labels_var.get():
                    for i, (bar, cat, value) in enumerate(zip(bars1, categories, values_1)):
                        if value > 0:
                            offset = (i % 2) * 0.1 * max_height
                            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + offset, f"{cat}: {int(value):,}", 
                                    ha='center', va='bottom', fontsize=6, rotation=90)

                    for i, (bar, cat, value) in enumerate(zip(bars2, categories, values_2)):
                        if value > 0:
                            offset = ((i + 1) % 2) * 0.1 * max_height
                            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + offset, f"{cat}: {int(value):,}", 
                                    ha='center', va='bottom', fontsize=6, rotation=90)

                ax.set_ylim(0, max_height * 1.3)
                ax.set_xticks(x)
                ax.set_xticklabels(categories, rotation=45, ha="right")
                ax.set_title(title)
                ax.set_ylabel("Consommation")
                ax.legend()
                fig.tight_layout()
                canvas.draw()

                if self.stats_text.winfo_exists():
                    self.stats_text.delete(1.0, tk.END)
                    if level_num == 5:
                        stats_values_1 = list(graph_data_cumulative[data_source]["period1"].values())
                        stats_values_2 = list(graph_data_cumulative[data_source]["period2"].values())
                    else:
                        stats_values_1 = [val for cat, val in graph_data_cumulative[data_source]["period1"].items() if (cat.count(" > ") + 1) == level_num]
                        stats_values_2 = [val for cat, val in graph_data_cumulative[data_source]["period2"].items() if (cat.count(" > ") + 1) == level_num]
                    mean_1 = np.mean(stats_values_1) if stats_values_1 else 0
                    mean_2 = np.mean(stats_values_2) if stats_values_2 else 0
                    self.stats_text.insert(tk.END, f"{display_level}:\n")
                    self.stats_text.insert(tk.END, f"Période 1 - Moyenne: {mean_1:,.2f}\n")
                    self.stats_text.insert(tk.END, f"Période 2 - Moyenne: {mean_2:,.2f}\n")

        filter_trace_id = filter_var.trace("w", lambda *args: update_graph())
        display_level_trace_id = display_level_var.trace("w", lambda *args: update_graph())
        show_labels_trace_id = show_labels_var.trace("w", lambda *args: update_graph())

        def on_closing():
            if filter_trace_id:
                filter_var.trace_vdelete("w", filter_trace_id)
            if display_level_trace_id:
                display_level_var.trace_vdelete("w", display_level_trace_id)
            if show_labels_trace_id:
                show_labels_var.trace_vdelete("w", show_labels_trace_id)
            graph_window.destroy()

        graph_window.protocol("WM_DELETE_WINDOW", on_closing)

        update_graph()

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = MeterConsumptionApp(root)
    root.mainloop()