import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import csv

class MeterConsumptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analyse des Consommations de Compteurs")

        # Appliquer le thème Clam
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#e1e1e1", foreground="#333333")
        style.configure("TButton", background="#4CAF50", foreground="white")
        style.configure("TEntry", fieldbackground="#ffffff")
        style.configure("TCombobox", fieldbackground="#ffffff")
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        # Définir des styles pour les lignes alternées et les totaux
        style.configure("OddRow.Treeview", background="#f0f0f0")  # Gris clair pour les lignes impaires
        style.configure("EvenRow.Treeview", background="#ffffff")  # Blanc pour les lignes paires
        style.configure("TotalRow.Treeview", font=("Arial", 10, "bold"), background="#d3d3d3")  # Gris moyen pour les totaux
        style.configure("SubTotalRow.Treeview", font=("Arial", 10, "bold"), background="#e0e0e0")  # Gris légèrement plus clair pour les sous-totaux
        # Styles pour l'écart objectif
        style.configure("Green.Treeview", background="#90ee90")  # Vert clair
        style.configure("Yellow.Treeview", background="#ffff99")  # Jaune clair
        style.configure("Red.Treeview", background="#ff9999")  # Rouge clair

        self.conn = sqlite3.connect("meters.db")
        self.cursor = self.conn.cursor()

        # Liste des compteurs et catégories
        self.meters = self.load_meters()
        self.categories = self.load_categories()
        self.meter_to_category = {meter[0]: meter[3] for meter in self.meters}

        # Interface principale avec onglets
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Onglet "Comparer les Périodes"
        self.compare_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.compare_frame, text="Comparer les Périodes")
        self.setup_compare_tab()

    def load_meters(self):
        """Charge les compteurs depuis la base de données."""
        self.cursor.execute("SELECT id, name, note, category_id FROM meters")
        return self.cursor.fetchall()

    def load_categories(self):
        """Charge les catégories depuis la base de données."""
        self.cursor.execute("SELECT id, name, parent_id FROM categories")
        return self.cursor.fetchall()

    def get_category_hierarchy(self, category_id):
        """Récupère la hiérarchie complète d'une catégorie sous forme de liste."""
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
        """Récupère le nom de la catégorie jusqu'à un certain niveau."""
        hierarchy = self.get_category_hierarchy(category_id)
        if max_level is not None:
            hierarchy = hierarchy[:max_level]
        return " > ".join(name for _, name in hierarchy)

    def get_top_level_category(self, category_id):
        """Récupère la catégorie principale (niveau 1)."""
        hierarchy = self.get_category_hierarchy(category_id)
        return hierarchy[0][1] if hierarchy else "Aucune"

    def setup_compare_tab(self):
        """Configure l'onglet Comparer les Périodes."""
        # Frame pour les filtres
        self.compare_filter_frame = ttk.Frame(self.compare_frame)
        self.compare_filter_frame.pack(fill="x", pady=5)

        # Période 1
        ttk.Label(self.compare_filter_frame, text="Période 1 :").pack(side="left", padx=5)
        ttk.Label(self.compare_filter_frame, text="De :").pack(side="left", padx=5)
        self.compare1_start_month_var = tk.StringVar()
        self.compare1_start_month_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare1_start_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5)
        self.compare1_start_month_combobox.pack(side="left", padx=5)
        self.compare1_start_month_combobox.set("01")

        self.compare1_start_year_var = tk.StringVar()
        self.compare1_start_year_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare1_start_year_var, values=[str(i) for i in range(2000, 2030)], width=7)
        self.compare1_start_year_combobox.pack(side="left", padx=5)
        self.compare1_start_year_combobox.set("2023")

        ttk.Label(self.compare_filter_frame, text="À :").pack(side="left", padx=5)
        self.compare1_end_month_var = tk.StringVar()
        self.compare1_end_month_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare1_end_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5)
        self.compare1_end_month_combobox.pack(side="left", padx=5)
        self.compare1_end_month_combobox.set("06")

        self.compare1_end_year_var = tk.StringVar()
        self.compare1_end_year_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare1_end_year_var, values=[str(i) for i in range(2000, 2030)], width=7)
        self.compare1_end_year_combobox.pack(side="left", padx=5)
        self.compare1_end_year_combobox.set("2023")

        # Période 2
        ttk.Label(self.compare_filter_frame, text="Période 2 :").pack(side="left", padx=5)
        ttk.Label(self.compare_filter_frame, text="De :").pack(side="left", padx=5)
        self.compare2_start_month_var = tk.StringVar()
        self.compare2_start_month_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare2_start_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5)
        self.compare2_start_month_combobox.pack(side="left", padx=5)
        self.compare2_start_month_combobox.set("01")

        self.compare2_start_year_var = tk.StringVar()
        self.compare2_start_year_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare2_start_year_var, values=[str(i) for i in range(2000, 2030)], width=7)
        self.compare2_start_year_combobox.pack(side="left", padx=5)
        self.compare2_start_year_combobox.set("2024")

        ttk.Label(self.compare_filter_frame, text="À :").pack(side="left", padx=5)
        self.compare2_end_month_var = tk.StringVar()
        self.compare2_end_month_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare2_end_month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5)
        self.compare2_end_month_combobox.pack(side="left", padx=5)
        self.compare2_end_month_combobox.set("06")

        self.compare2_end_year_var = tk.StringVar()
        self.compare2_end_year_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare2_end_year_var, values=[str(i) for i in range(2000, 2030)], width=7)
        self.compare2_end_year_combobox.pack(side="left", padx=5)
        self.compare2_end_year_combobox.set("2024")

        ttk.Label(self.compare_filter_frame, text="Niveau de regroupement :").pack(side="left", padx=5)
        self.compare_grouping_var = tk.StringVar()
        self.compare_grouping_combobox = ttk.Combobox(self.compare_filter_frame, textvariable=self.compare_grouping_var, values=["Niveau 1", "Niveau 2", "Niveau 3", "Niveau 4", "Niveau 5"], width=10)
        self.compare_grouping_combobox.pack(side="left", padx=5)
        self.compare_grouping_combobox.set("Niveau 5")

        ttk.Label(self.compare_filter_frame, text="Objectif (%):").pack(side="left", padx=5)
        self.target_var = tk.StringVar(value="5")
        self.target_entry = ttk.Entry(self.compare_filter_frame, textvariable=self.target_var, width=5)
        self.target_entry.pack(side="left", padx=5)

        ttk.Button(self.compare_filter_frame, text="Comparer", command=self.compare_periods).pack(side="left", padx=10)
        ttk.Button(self.compare_filter_frame, text="Exporter en CSV", command=self.export_to_csv).pack(side="left", padx=10)

        # Treeview pour afficher la comparaison
        self.compare_tree = ttk.Treeview(self.compare_frame, columns=("Category", "Meter", "Period1", "Period2", "Difference", "TargetDiff"), show="headings")
        self.compare_tree.heading("Category", text="Catégorie")
        self.compare_tree.heading("Meter", text="Compteur")
        self.compare_tree.heading("Period1", text="Période 1")
        self.compare_tree.heading("Period2", text="Période 2")
        self.compare_tree.heading("Difference", text="Différence")
        self.compare_tree.heading("TargetDiff", text="Écart Objectif (%)")
        self.compare_tree.column("Category", width=200)
        self.compare_tree.column("Meter", width=150)
        self.compare_tree.column("Period1", width=100)
        self.compare_tree.column("Period2", width=100)
        self.compare_tree.column("Difference", width=100)
        self.compare_tree.column("TargetDiff", width=120)
        self.compare_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def export_to_csv(self):
        """Exporte les données du Treeview en fichier CSV avec un délimiteur adapté."""
        # Vérifier s'il y a des données à exporter
        if not self.compare_tree.get_children():
            messagebox.showwarning("Aucune donnée", "Aucune donnée à exporter. Veuillez d'abord comparer les périodes.")
            return

        # Demander à l'utilisateur où sauvegarder le fichier
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            title="Enregistrer sous",
            initialfile="comparaison_periodes.csv"
        )
        if not file_path:
            return  # L'utilisateur a annulé

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file, delimiter=';')  # Utiliser le point-virgule comme délimiteur
                # Écrire les en-têtes
                headers = [self.compare_tree.heading(col)["text"] for col in self.compare_tree["columns"]]
                writer.writerow(headers)
                # Écrire les données
                for item in self.compare_tree.get_children():
                    row = self.compare_tree.item(item)["values"]
                    writer.writerow(row)
            messagebox.showinfo("Succès", f"Données exportées avec succès dans {file_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exportation : {str(e)}")

    def compare_periods(self):
        """Compare les consommations entre deux périodes."""
        for item in self.compare_tree.get_children():
            self.compare_tree.delete(item)

        period1_start_date = f"{self.compare1_start_year_var.get()}-{self.compare1_start_month_var.get()}"
        period1_end_date = f"{self.compare1_end_year_var.get()}-{self.compare1_end_month_var.get()}"
        period2_start_date = f"{self.compare2_start_year_var.get()}-{self.compare2_start_month_var.get()}"
        period2_end_date = f"{self.compare2_end_year_var.get()}-{self.compare2_end_month_var.get()}"

        # Déterminer le niveau de regroupement
        grouping_level = int(self.compare_grouping_var.get().split()[-1])  # Ex: "Niveau 1" -> 1

        # Récupérer l'objectif
        try:
            target = float(self.target_var.get())
        except ValueError:
            messagebox.showwarning("Erreur", "L'objectif doit être un nombre.")
            return

        # Charger les index de base
        self.cursor.execute("SELECT meter_id, base_index FROM base_indices")
        base_indices = {row[0]: row[1] for row in self.cursor.fetchall()}

        # Charger les relevés pour les deux périodes
        self.cursor.execute("SELECT meter_id, date, meter_index FROM readings WHERE date BETWEEN ? AND ? ORDER BY date", (period1_start_date, period1_end_date))
        period1_readings = self.cursor.fetchall()
        self.cursor.execute("SELECT meter_id, date, meter_index FROM readings WHERE date BETWEEN ? AND ? ORDER BY date", (period2_start_date, period2_end_date))
        period2_readings = self.cursor.fetchall()

        # Organiser les relevés par compteur
        meter_readings1 = {}
        for meter_id, date, index in period1_readings:
            if meter_id not in meter_readings1:
                meter_readings1[meter_id] = []
            meter_readings1[meter_id].append((date, index))

        meter_readings2 = {}
        for meter_id, date, index in period2_readings:
            if meter_id not in meter_readings2:
                meter_readings2[meter_id] = []
            meter_readings2[meter_id].append((date, index))

        # Calculer les consommations pour chaque période
        meter_consumptions1 = {}
        meter_consumptions2 = {}
        for meter in self.meters:
            meter_id = meter[0]
            base_index = base_indices.get(meter_id, 0)

            # Période 1
            total_consumption1 = 0
            if meter_id in meter_readings1:
                readings = sorted(meter_readings1[meter_id], key=lambda x: x[0])
                prev_index = base_index
                for date, index in readings:
                    if index >= prev_index:
                        consumption = index - prev_index
                        total_consumption1 += consumption
                    prev_index = index
            meter_consumptions1[meter_id] = total_consumption1

            # Période 2
            total_consumption2 = 0
            if meter_id in meter_readings2:
                readings = sorted(meter_readings2[meter_id], key=lambda x: x[0])
                prev_index = base_index
                for date, index in readings:
                    if index >= prev_index:
                        consumption = index - prev_index
                        total_consumption2 += consumption
                    prev_index = index
            meter_consumptions2[meter_id] = total_consumption2

        # Regrouper les consommations par catégorie et par niveau
        category_totals_by_level1 = {}  # Pour la période 1: {category_id: {level: total}}
        category_totals_by_level2 = {}  # Pour la période 2: {category_id: {level: total}}
        top_level_totals1 = {}  # Pour les totaux par catégorie principale (niveau 1) période 1
        top_level_totals2 = {}  # Pour les totaux par catégorie principale (niveau 1) période 2

        # Données pour les graphiques
        graph_data_12_1 = {}  # Niveaux 1-2, période 1
        graph_data_12_2 = {}  # Niveaux 1-2, période 2
        graph_data_34_1 = {}  # Niveaux 3-4, période 1
        graph_data_34_2 = {}  # Niveaux 3-4, période 2
        graph_data_5_1 = {}   # Niveau 5 (compteurs), période 1
        graph_data_5_2 = {}   # Niveau 5 (compteurs), période 2

        for meter in self.meters:
            meter_id = meter[0]
            consumption1 = meter_consumptions1.get(meter_id, 0)
            consumption2 = meter_consumptions2.get(meter_id, 0)
            if consumption1 == 0 and consumption2 == 0:
                continue

            category_id = meter[3]
            category_hierarchy = self.get_category_hierarchy(category_id)
            top_level_category = self.get_top_level_category(category_id)

            # Ajouter aux totaux des catégories principales
            if top_level_category not in top_level_totals1:
                top_level_totals1[top_level_category] = 0
                top_level_totals2[top_level_category] = 0
            top_level_totals1[top_level_category] += consumption1
            top_level_totals2[top_level_category] += consumption2

            # Ajouter les totaux pour chaque niveau de la hiérarchie
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

                # Ajouter aux données des graphiques pour les niveaux 1-2 et 3-4
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

            # Ajouter les compteurs au graphique de niveau 5, indépendamment du niveau de la catégorie
            meter_name = meter[1]
            if meter_name not in graph_data_5_1:
                graph_data_5_1[meter_name] = 0
                graph_data_5_2[meter_name] = 0
            graph_data_5_1[meter_name] += consumption1
            graph_data_5_2[meter_name] += consumption2

        # Organiser les données par catégorie principale pour l'affichage
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

        # Afficher les données dans l'ordre demandé : compteurs (si niveau 5), sous-totaux, puis total
        row_count = 0
        for top_level_category in sorted(grouped_by_top_level1.keys()):
            categories_by_level1 = grouped_by_top_level1[top_level_category]
            categories_by_level2 = grouped_by_top_level2[top_level_category]

            # Afficher les compteurs si le niveau de regroupement est 5
            if grouping_level == 5:
                # Trier les compteurs par catégorie complète (longueur décroissante)
                meter_list = []
                for meter in self.meters:
                    meter_id = meter[0]
                    consumption1 = meter_consumptions1.get(meter_id, 0)
                    consumption2 = meter_consumptions2.get(meter_id, 0)
                    if consumption1 == 0 and consumption2 == 0:
                        continue
                    category_id = meter[3]
                    meter_top_level = self.get_top_level_category(category_id)
                    if meter_top_level != top_level_category:
                        continue
                    difference = consumption2 - consumption1
                    # Calculer l'écart en pourcentage
                    if consumption1 > 0:
                        target_diff = ((consumption2 - consumption1) / consumption1) * 100
                    else:
                        target_diff = float('inf') if consumption2 > 0 else 0
                    # Déterminer la couleur en fonction de l'écart
                    if target_diff < 0:
                        color_tag = "Green"
                    elif 0 <= target_diff <= 0.5:
                        color_tag = "Yellow"
                    else:
                        color_tag = "Red"
                    category_name = self.get_category_name(category_id, max_level=grouping_level)
                    meter_list.append((category_name, meter[1], consumption1, consumption2, difference, target_diff, color_tag))

                # Trier les compteurs par catégorie (longueur décroissante)
                meter_list.sort(key=lambda x: (-x[0].count(">"), x[0], x[1]))

                for category_name, meter_name, consumption1, consumption2, difference, target_diff, color_tag in meter_list:
                    tag = "OddRow" if row_count % 2 else "EvenRow"
                    self.compare_tree.insert("", tk.END, values=(
                        category_name,
                        meter_name,
                        f"{consumption1:,} kWh".replace(",", " "),
                        f"{consumption2:,} kWh".replace(",", " "),
                        f"{difference:+,} kWh".replace(",", " "),
                        f"{target_diff:+.2f}%"
                    ), tags=(color_tag, tag))
                    row_count += 1

            # Afficher les sous-totaux des catégories intermédiaires
            if grouping_level > 1:
                # Trier les catégories par longueur décroissante
                category_list = []
                for level in sorted(categories_by_level1.keys()):
                    if level > grouping_level:
                        continue
                    for category_name in categories_by_level1[level]:
                        if category_name == top_level_category and level == 1:
                            continue  # Sauter le niveau 1 ici, il sera affiché comme "Total"
                        total1 = categories_by_level1[level][category_name]
                        total2 = categories_by_level2[level][category_name]
                        difference = total2 - total1
                        # Calculer l'écart en pourcentage
                        if total1 > 0:
                            target_diff = ((total2 - total1) / total1) * 100
                        else:
                            target_diff = float('inf') if total2 > 0 else 0
                        # Déterminer la couleur en fonction de l'écart
                        if target_diff < 0:
                            color_tag = "Green"
                        elif 0 <= target_diff <= 0.5:
                            color_tag = "Yellow"
                        else:
                            color_tag = "Red"
                        category_list.append((category_name, level, total1, total2, difference, target_diff, color_tag))

                # Trier par longueur décroissante (nombre de ">") puis par nom
                category_list.sort(key=lambda x: (-x[0].count(">"), x[0]))

                for category_name, level, total1, total2, difference, target_diff, color_tag in category_list:
                    tag = "OddRow" if row_count % 2 else "EvenRow"
                    self.compare_tree.insert("", tk.END, values=(
                        category_name,
                        "Sous-total",
                        f"{total1:,} kWh".replace(",", " "),
                        f"{total2:,} kWh".replace(",", " "),
                        f"{difference:+,} kWh".replace(",", " "),
                        f"{target_diff:+.2f}%"
                    ), tags=("SubTotalRow", color_tag, tag))
                    row_count += 1

            # Afficher le total de la catégorie principale
            total1 = top_level_totals1[top_level_category]
            total2 = top_level_totals2[top_level_category]
            difference = total2 - total1
            # Calculer l'écart en pourcentage
            if total1 > 0:
                target_diff = ((total2 - total1) / total1) * 100
            else:
                target_diff = float('inf') if total2 > 0 else 0
            # Déterminer la couleur en fonction de l'écart
            if target_diff < 0:
                color_tag = "Green"
            elif 0 <= target_diff <= 0.5:
                color_tag = "Yellow"
            else:
                color_tag = "Red"
            self.compare_tree.insert("", tk.END, values=(
                top_level_category,
                "Total",
                f"{total1:,} kWh".replace(",", " "),
                f"{total2:,} kWh".replace(",", " "),
                f"{difference:+,} kWh".replace(",", " "),
                f"{target_diff:+.2f}%"
            ), tags=("TotalRow", color_tag))

        # Afficher les graphiques dans une nouvelle fenêtre
        self.show_graphs_in_new_window(grouping_level, graph_data_12_1, graph_data_12_2, graph_data_34_1, graph_data_34_2, graph_data_5_1, graph_data_5_2, period1_start_date, period1_end_date, period2_start_date, period2_end_date)

    def show_graphs_in_new_window(self, grouping_level, graph_data_12_1, graph_data_12_2, graph_data_34_1, graph_data_34_2, graph_data_5_1, graph_data_5_2, period1_start_date, period1_end_date, period2_start_date, period2_end_date):
        """Affiche un seul graphique dans une nouvelle fenêtre, avec un sélecteur de niveau."""
        # Créer une nouvelle fenêtre
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Graphique de Comparaison")
        graph_window.resizable(True, True)
        graph_window.geometry("1000x900")

        # PanedWindow pour organiser les éléments côte à côte
        main_pane = ttk.PanedWindow(graph_window, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True)

        # Frame principal pour le graphique (plus besoin de défilement)
        graph_container = ttk.Frame(main_pane)
        main_pane.add(graph_container, weight=3)

        # Frame pour les statistiques et les options
        stats_frame = ttk.Frame(main_pane)
        main_pane.add(stats_frame, weight=1)

        # Sélecteur de niveau d'affichage
        level_frame = ttk.LabelFrame(stats_frame, text="Niveau d'Affichage")
        level_frame.pack(fill="x", padx=5, pady=5)

        display_level_var = tk.StringVar(value="Niveaux 1-2")
        display_level_combobox = ttk.Combobox(level_frame, textvariable=display_level_var, values=["Niveaux 1-2", "Niveaux 3-4", "Niveau 5"], state="readonly")
        display_level_combobox.pack(fill="x", padx=5, pady=2)

        # Filtrage par catégorie
        filter_frame = ttk.LabelFrame(stats_frame, text="Filtrer par Catégorie")
        filter_frame.pack(fill="x", padx=5, pady=5)

        filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=filter_var)
        filter_entry.pack(fill="x", padx=5, pady=2)

        # Sélecteurs de couleur
        color_frame = ttk.LabelFrame(stats_frame, text="Couleurs des Périodes")
        color_frame.pack(fill="x", padx=5, pady=5)

        self.color1 = "skyblue"
        self.color2 = "lightcoral"

        def choose_color1():
            color = colorchooser.askcolor(title="Choisir la couleur de la Période 1")[1]
            if color:
                self.color1 = color
                update_graph()

        def choose_color2():
            color = colorchooser.askcolor(title="Choisir la couleur de la Période 2")[1]
            if color:
                self.color2 = color
                update_graph()

        ttk.Button(color_frame, text="Couleur Période 1", command=choose_color1).pack(fill="x", padx=5, pady=2)
        ttk.Button(color_frame, text="Couleur Période 2", command=choose_color2).pack(fill="x", padx=5, pady=2)

        # Résumé statistique
        stats_label_frame = ttk.LabelFrame(stats_frame, text="Résumé Statistique")
        stats_label_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.stats_text = tk.Text(stats_label_frame, height=10, width=30)
        self.stats_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Initialiser le graphique unique
        fig, ax = plt.subplots(figsize=(8, 6))
        canvas = FigureCanvasTkAgg(fig, master=graph_container)
        toolbar = NavigationToolbar2Tk(canvas, graph_container)
        toolbar.update()
        toolbar.pack(fill="x")
        canvas.get_tk_widget().pack(fill="both", expand=True)

        def update_graph():
            """Met à jour le graphique en fonction du niveau d'affichage sélectionné."""
            ax.clear()

            # Appliquer le filtrage
            filter_text = filter_var.get().lower()
            filtered_12_1 = {k: v for k, v in graph_data_12_1.items() if filter_text in k.lower()}
            filtered_12_2 = {k: v for k, v in graph_data_12_2.items() if filter_text in k.lower()}
            filtered_34_1 = {k: v for k, v in graph_data_34_1.items() if filter_text in k.lower()}
            filtered_34_2 = {k: v for k, v in graph_data_34_2.items() if filter_text in k.lower()}
            filtered_5_1 = {k: v for k, v in graph_data_5_1.items() if filter_text in k.lower()}
            filtered_5_2 = {k: v for k, v in graph_data_5_2.items() if filter_text in k.lower()}

            # Sélectionner le niveau d'affichage
            display_level = display_level_var.get()
            if display_level == "Niveaux 1-2":
                categories = sorted(filtered_12_1.keys(), key=lambda x: (-x.count(">"), x))
                values_1 = [filtered_12_1[cat] for cat in categories]
                values_2 = [filtered_12_2[cat] for cat in categories]
                title = f"Consommation Niveaux 1-2 Du {period1_start_date} à {period1_end_date} et Du {period2_start_date} à {period2_end_date}"
                stats_values_1 = list(graph_data_12_1.values())
                stats_values_2 = list(graph_data_12_2.values())
            elif display_level == "Niveaux 3-4":
                categories = sorted(filtered_34_1.keys(), key=lambda x: (-x.count(">"), x))
                values_1 = [filtered_34_1[cat] for cat in categories]
                values_2 = [filtered_34_2[cat] for cat in categories]
                title = f"Consommation Niveaux 3-4 Du {period1_start_date} à {period1_end_date} et Du {period2_start_date} à {period2_end_date}"
                stats_values_1 = list(graph_data_34_1.values())
                stats_values_2 = list(graph_data_34_2.values())
            else:  # Niveau 5
                categories = sorted(filtered_5_1.keys(), key=lambda x: x)
                values_1 = [filtered_5_1[cat] for cat in categories]
                values_2 = [filtered_5_2[cat] for cat in categories]
                title = f"Consommation Niveau 5 Du {period1_start_date} à {period1_end_date} et Du {period2_start_date} à {period2_end_date}"
                stats_values_1 = list(graph_data_5_1.values())
                stats_values_2 = list(graph_data_5_2.values())

            # Afficher le graphique
            x = range(len(categories))
            bar_width = 0.35
            bars1 = ax.bar([i - bar_width/2 for i in x], values_1, bar_width, label="Période 1", color=self.color1)
            bars2 = ax.bar([i + bar_width/2 for i in x], values_2, bar_width, label="Période 2", color=self.color2)
            for bar in bars1:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height + 0.5, f"{int(height):,}".replace(",", " "), ha="center", va="bottom")
            for bar in bars2:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height + 0.5, f"{int(height):,}".replace(",", " "), ha="center", va="bottom")
            ax.set_xticks(x)
            ax.set_xticklabels(categories, rotation=45, ha="right")
            ax.set_title(title)
            ax.set_ylabel("Consommation (kWh)")
            ax.legend()
            fig.tight_layout()
            canvas.draw()

            # Mettre à jour les statistiques
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, f"{display_level}:\n")
            self.stats_text.insert(tk.END, f"Période 1 - Moyenne: {np.mean(stats_values_1):,.2f} kWh\n")
            self.stats_text.insert(tk.END, f"Période 2 - Moyenne: {np.mean(stats_values_2):,.2f} kWh\n")

        # Afficher le graphique initial
        update_graph()

        # Mettre à jour le graphique lors de la modification du filtre ou du niveau d'affichage
        filter_var.trace("w", lambda *args: update_graph())
        display_level_var.trace("w", lambda *args: update_graph())

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = MeterConsumptionApp(root)
    root.mainloop()