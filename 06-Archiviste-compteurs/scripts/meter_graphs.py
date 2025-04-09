import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as mpatches
import numpy as np

class MeterGraphs:
    def __init__(self, parent):
        self.parent = parent
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Frame pour les filtres
        self.filter_frame = ttk.LabelFrame(self.main_frame, text="Options de visualisation")
        self.filter_frame.pack(fill="x", pady=5)

        # Niveau d'affichage
        ttk.Label(self.filter_frame, text="Niveau d'affichage :").pack(side="left", padx=5)
        self.display_level_var = tk.StringVar(value="Niveau 1")
        self.display_level_combobox = ttk.Combobox(self.filter_frame, textvariable=self.display_level_var, values=["Niveau 1", "Niveau 2", "Niveau 3", "Niveau 4", "Niveau 5"], state="readonly")
        self.display_level_combobox.pack(side="left", padx=5)

        # Filtre par catégorie
        ttk.Label(self.filter_frame, text="Filtrer par catégorie :").pack(side="left", padx=5)
        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(self.filter_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side="left", padx=5, fill="x", expand=True)

        # Option d'affichage des étiquettes
        self.show_labels_var = tk.BooleanVar(value=True)
        self.show_labels_checkbutton = ttk.Checkbutton(self.filter_frame, text="Afficher les étiquettes", variable=self.show_labels_var)
        self.show_labels_checkbutton.pack(side="left", padx=10)

        # Frame pour le graphique
        self.graph_frame = ttk.Frame(self.main_frame)
        self.graph_frame.pack(fill="both", expand=True)

        # Initialisation du graphique avec deux axes Y
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.ax2 = self.ax.twinx()  # Axe Y secondaire pour les lignes
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.graph_frame)
        self.toolbar.update()
        self.toolbar.pack(fill="x")
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.color1 = "skyblue"
        self.color2 = "lightcoral"

        # Variables pour stocker les données
        self.grouping_level = None
        self.graph_data_by_month = None
        self.period1_start_date = None
        self.period1_end_date = None
        self.period2_start_date = None
        self.period2_end_date = None
        self.is_monthly = None
        self.graph_data_cumulative = None

        # Dictionnaire pour stocker les préférences d'affichage (barre ou ligne) par catégorie
        self.display_type = {}  # Exemple : {"catégorie_période": "line"} ou {"catégorie_période": "bar"}

        # Binding des événements pour mettre à jour le graphique
        self.filter_var.trace("w", lambda *args: self.update_graph())
        self.display_level_var.trace("w", lambda *args: self.update_graph())
        self.show_labels_var.trace("w", lambda *args: self.update_graph())

        # Gestionnaire de clic pour basculer entre barres et lignes
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def update_data(self, grouping_level, graph_data_by_month, period1_start_date, period1_end_date, period2_start_date, period2_end_date, is_monthly=True, graph_data_cumulative=None):
        """Met à jour les données pour le graphique."""
        self.grouping_level = grouping_level
        self.graph_data_by_month = graph_data_by_month
        self.period1_start_date = period1_start_date
        self.period1_end_date = period1_end_date
        self.period2_start_date = period2_start_date
        self.period2_end_date = period2_end_date
        self.is_monthly = is_monthly
        self.graph_data_cumulative = graph_data_cumulative
        # Réinitialise les préférences d'affichage pour les nouvelles données
        self.display_type = {}
        self.update_graph()

    def toggle_display_type(self, category, period):
        """Bascule entre l'affichage en barres et en lignes pour une catégorie donnée."""
        key = f"{category}_{period}"
        if key not in self.display_type or self.display_type[key] == "bar":
            self.display_type[key] = "line"
        else:
            self.display_type[key] = "bar"
        self.update_graph()

    def on_click(self, event):
        """Gère le clic droit sur une barre ou une ligne pour basculer entre barres et lignes."""
        if event.button != 3:  # Clic droit uniquement
            return

        # Vérifie si le clic est sur une barre
        for artist in self.ax.get_children():
            if isinstance(artist, plt.Rectangle) and artist.contains(event)[0]:
                if hasattr(artist, 'category') and hasattr(artist, 'period'):
                    self.toggle_display_type(artist.category, artist.period)
                    return

        # Vérifie si le clic est sur une ligne
        for artist in self.ax2.get_children():
            if isinstance(artist, plt.Line2D) and artist.contains(event)[0]:
                if hasattr(artist, 'category') and hasattr(artist, 'period'):
                    self.toggle_display_type(artist.category, artist.period)
                    return

    def update_graph(self):
        """Met à jour le graphique en fonction des données et des filtres."""
        if not self.grouping_level:  # Si pas de données, affiche un message
            self.ax.clear()
            self.ax2.clear()
            self.ax.text(0.5, 0.5, "Aucune donnée disponible.\nVeuillez comparer des périodes dans l'onglet Rapports.", ha='center', va='center', fontsize=12)
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax2.set_yticks([])
            self.canvas.draw()
            return

        self.ax.clear()
        self.ax2.clear()
        display_level = self.display_level_var.get()
        level_num = int(display_level.split()[-1])
        title = f"Consommation Niveau {level_num} ({'Mois par Mois' if self.is_monthly else 'Cumul'})"

        # Listes pour stocker les éléments des légendes (barres et lignes séparément)
        legend_elements_bars = []
        legend_elements_lines = []
        legend_labels_bars = set()  # Pour éviter les doublons dans la légende des barres
        legend_labels_lines = set()  # Pour éviter les doublons dans la légende des lignes

        if self.is_monthly:
            filter_text = self.filter_var.get().lower()
            filtered_data = {}
            for month_pair in self.graph_data_by_month:
                month1, month2 = month_pair
                filtered_data[month_pair] = {
                    "12": {"period1": {}, "period2": {}},
                    "34": {"period1": {}, "period2": {}},
                    "5": {"period1": {}, "period2": {}}
                }
                for level in ["12", "34", "5"]:
                    for period in ["period1", "period2"]:
                        for cat, val in self.graph_data_by_month[month_pair][level][period].items():
                            if filter_text in cat.lower():
                                filtered_data[month_pair][level][period][cat] = val

            month_pairs = sorted(self.graph_data_by_month.keys(), key=lambda x: x[0])
            categories = set()
            if level_num <= 2:
                data_source = "12"
            elif 3 <= level_num <= 4:
                data_source = "34"
            else:
                data_source = "5"

            for month_pair in month_pairs:
                for cat in filtered_data[month_pair][data_source]["period1"].keys():
                    if level_num == 5 or (cat.count(" > ") + 1) == level_num:
                        categories.add(cat)
                for cat in filtered_data[month_pair][data_source]["period2"].keys():
                    if level_num == 5 or (cat.count(" > ") + 1) == level_num:
                        categories.add(cat)
            categories = sorted(categories)

            if not categories:
                self.ax.text(0.5, 0.5, "Aucune donnée pour ce niveau", ha='center', va='center', fontsize=12, color='red')
                self.ax.set_xticks([])
                self.ax.set_yticks([])
                self.ax2.set_yticks([])
                self.ax.set_title(title)
                self.ax.set_ylabel("Consommation (Barres)")
                self.ax2.set_ylabel("Consommation (Lignes)", rotation=270, labelpad=15)
                self.fig.tight_layout()
                self.canvas.draw()
                return

            x = np.arange(len(month_pairs))
            bar_width = 0.3 / len(categories)
            spacing = 0.5  # Espacement entre les groupes de barres
            colors = plt.cm.tab20(np.linspace(0, 1, len(categories)))

            max_height_bars = 0
            max_height_lines = 0
            for cat in categories:
                values_1 = [filtered_data[month_pair][data_source]["period1"].get(cat, 0) for month_pair in month_pairs]
                values_2 = [filtered_data[month_pair][data_source]["period2"].get(cat, 0) for month_pair in month_pairs]
                key1 = f"{cat}_period1"
                key2 = f"{cat}_period2"
                display_type1 = self.display_type.get(key1, "bar")
                display_type2 = self.display_type.get(key2, "bar")
                if display_type1 == "bar":
                    max_height_bars = max(max_height_bars, max(values_1, default=0))
                else:
                    max_height_lines = max(max_height_lines, max(values_1, default=0))
                if display_type2 == "bar":
                    max_height_bars = max(max_height_bars, max(values_2, default=0))
                else:
                    max_height_lines = max(max_height_lines, max(values_2, default=0))

            for i, cat in enumerate(categories):
                values_1 = [filtered_data[month_pair][data_source]["period1"].get(cat, 0) for month_pair in month_pairs]
                values_2 = [filtered_data[month_pair][data_source]["period2"].get(cat, 0) for month_pair in month_pairs]
                key1 = f"{cat}_period1"
                key2 = f"{cat}_period2"
                display_type1 = self.display_type.get(key1, "bar")
                display_type2 = self.display_type.get(key2, "bar")

                # Position ajustée pour éviter le chevauchement
                offset = i * (bar_width * 2 + spacing/len(categories))
                label1 = f"{cat} - Période 1"
                label2 = f"{cat} - Période 2"

                if display_type1 == "bar":
                    bars1 = self.ax.bar(x + offset, values_1, bar_width, color=colors[i], alpha=0.8, label='_nolegend_')
                    if label1 not in legend_labels_bars:
                        # Utilise un Patch pour représenter la barre dans la légende
                        legend_elements_bars.append(mpatches.Patch(color=colors[i], alpha=0.8, label=label1))
                        legend_labels_bars.add(label1)
                    if self.show_labels_var.get():
                        for j, (bar, value) in enumerate(zip(bars1, values_1)):
                            if value > 0:
                                offset_height = (i % 2) * 0.1 * max_height_bars
                                self.ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + offset_height, f"{cat}: {int(value):,}", 
                                             ha='center', va='bottom', fontsize=6, rotation=90)
                    for bar in bars1:
                        bar.set_picker(5)
                        bar.category = cat
                        bar.period = "period1"
                else:
                    line1 = self.ax2.plot(x, values_1, label=label1, color=colors[i], marker='o', linestyle='-', alpha=0.8)
                    if label1 not in legend_labels_lines:
                        legend_elements_lines.append(line1[0])
                        legend_labels_lines.add(label1)
                    line1[0].set_picker(5)
                    line1[0].category = cat
                    line1[0].period = "period1"

                if display_type2 == "bar":
                    bars2 = self.ax.bar(x + offset + bar_width + 0.02, values_2, bar_width, color=colors[i], alpha=0.4, label='_nolegend_')
                    if label2 not in legend_labels_bars:
                        # Utilise un Patch pour représenter la barre dans la légende
                        legend_elements_bars.append(mpatches.Patch(color=colors[i], alpha=0.4, label=label2))
                        legend_labels_bars.add(label2)
                    if self.show_labels_var.get():
                        for j, (bar, value) in enumerate(zip(bars2, values_2)):
                            if value > 0:
                                offset_height = ((i + 1) % 2) * 0.1 * max_height_bars
                                self.ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + offset_height, f"{cat}: {int(value):,}", 
                                             ha='center', va='bottom', fontsize=6, rotation=90)
                    for bar in bars2:
                        bar.set_picker(5)
                        bar.category = cat
                        bar.period = "period2"
                else:
                    line2 = self.ax2.plot(x, values_2, label=label2, color=colors[i], marker='o', linestyle='--', alpha=0.4)
                    if label2 not in legend_labels_lines:
                        legend_elements_lines.append(line2[0])
                        legend_labels_lines.add(label2)
                    line2[0].set_picker(5)
                    line2[0].category = cat
                    line2[0].period = "period2"

            self.ax.set_ylim(0, max_height_bars * 1.3 if max_height_bars > 0 else 1)
            self.ax2.set_ylim(0, max_height_lines * 1.3 if max_height_lines > 0 else 1)
            self.ax.set_xticks(x)
            self.ax.set_xticklabels([f"{month1} vs {month2}" for month1, month2 in month_pairs], rotation=45, ha="right")
            self.ax.set_title(title)
            self.ax.set_ylabel("Consommation (Barres)")
            self.ax2.set_ylabel("Consommation (Lignes)", rotation=270, labelpad=15)

            # Ajoute la légende des barres
            num_bars = len(legend_elements_bars) if legend_elements_bars else 0  # Définit num_bars même si aucune barre
            if legend_elements_bars:
                self.ax.legend(handles=legend_elements_bars, bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')

            # Ajoute la légende des lignes en dessous, si des lignes existent
            if legend_elements_lines:
                num_lines = len(legend_elements_lines)
                # Ajuste la position de la légende des lignes pour éviter la superposition
                self.ax2.legend(handles=legend_elements_lines, bbox_to_anchor=(1.05, 1 - (num_bars * 0.03 + 0.1)), loc='upper left', fontsize='small', title="Lignes")

            self.fig.tight_layout()
            self.canvas.draw()

        else:
            filter_text = self.filter_var.get().lower()
            filtered_data = {
                "12": {"period1": {}, "period2": {}},
                "34": {"period1": {}, "period2": {}},
                "5": {"period1": {}, "period2": {}}
            }
            for level in ["12", "34", "5"]:
                for period in ["period1", "period2"]:
                    for cat, val in self.graph_data_cumulative[level][period].items():
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
                if level_num == 5 or (cat.count(" > ") + 1) == level_num:
                    categories.add(cat)
            for cat in filtered_data[data_source]["period2"].keys():
                if level_num == 5 or (cat.count(" > ") + 1) == level_num:
                    categories.add(cat)
            categories = sorted(categories)

            if not categories:
                self.ax.text(0.5, 0.5, "Aucune donnée pour ce niveau", ha='center', va='center', fontsize=12, color='red')
                self.ax.set_xticks([])
                self.ax.set_yticks([])
                self.ax2.set_yticks([])
                self.ax.set_title(title)
                self.ax.set_ylabel("Consommation (Barres)")
                self.ax2.set_ylabel("Consommation (Lignes)", rotation=270, labelpad=15)
                self.fig.tight_layout()
                self.canvas.draw()
                return

            x = np.arange(len(categories))
            bar_width = 0.7
            values_1 = [filtered_data[data_source]["period1"].get(cat, 0) for cat in categories]
            values_2 = [filtered_data[data_source]["period2"].get(cat, 0) for cat in categories]

            max_height_bars = 0
            max_height_lines = 0
            for i, cat in enumerate(categories):
                key1 = f"{cat}_period1"
                key2 = f"{cat}_period2"
                display_type1 = self.display_type.get(key1, "bar")
                display_type2 = self.display_type.get(key2, "bar")
                if display_type1 == "bar":
                    max_height_bars = max(max_height_bars, values_1[i])
                else:
                    max_height_lines = max(max_height_lines, values_1[i])
                if display_type2 == "bar":
                    max_height_bars = max(max_height_bars, values_2[i])
                else:
                    max_height_lines = max(max_height_lines, values_2[i])

            for i, cat in enumerate(categories):
                key1 = f"{cat}_period1"
                key2 = f"{cat}_period2"
                display_type1 = self.display_type.get(key1, "bar")
                display_type2 = self.display_type.get(key2, "bar")
                label1 = f"{cat} - Période 1"
                label2 = f"{cat} - Période 2"

                if display_type1 == "bar":
                    bars1 = self.ax.bar(x[i] - bar_width/2, values_1[i], bar_width, color=self.color1, label='_nolegend_')
                    if label1 not in legend_labels_bars:
                        legend_elements_bars.append(mpatches.Patch(color=self.color1, label=label1))
                        legend_labels_bars.add(label1)
                    if self.show_labels_var.get() and values_1[i] > 0:
                        self.ax.text(x[i] - bar_width/2, values_1[i], f"{cat}: {int(values_1[i]):,}", 
                                     ha='center', va='bottom', fontsize=6, rotation=90)
                    for bar in bars1:
                        bar.set_picker(5)
                        bar.category = cat
                        bar.period = "period1"
                else:
                    line1 = self.ax2.plot(x[i], values_1[i], label=label1, color=self.color1, marker='o', linestyle='-')
                    if label1 not in legend_labels_lines:
                        legend_elements_lines.append(line1[0])
                        legend_labels_lines.add(label1)
                    line1[0].set_picker(5)
                    line1[0].category = cat
                    line1[0].period = "period1"

                if display_type2 == "bar":
                    bars2 = self.ax.bar(x[i] + bar_width/2, values_2[i], bar_width, color=self.color2, label='_nolegend_')
                    if label2 not in legend_labels_bars:
                        legend_elements_bars.append(mpatches.Patch(color=self.color2, label=label2))
                        legend_labels_bars.add(label2)
                    if self.show_labels_var.get() and values_2[i] > 0:
                        self.ax.text(x[i] + bar_width/2, values_2[i], f"{cat}: {int(values_2[i]):,}", 
                                     ha='center', va='bottom', fontsize=6, rotation=90)
                    for bar in bars2:
                        bar.set_picker(5)
                        bar.category = cat
                        bar.period = "period2"
                else:
                    line2 = self.ax2.plot(x[i], values_2[i], label=label2, color=self.color2, marker='o', linestyle='--')
                    if label2 not in legend_labels_lines:
                        legend_elements_lines.append(line2[0])
                        legend_labels_lines.add(label2)
                    line2[0].set_picker(5)
                    line2[0].category = cat
                    line2[0].period = "period2"

            self.ax.set_ylim(0, max_height_bars * 1.3 if max_height_bars > 0 else 1)
            self.ax2.set_ylim(0, max_height_lines * 1.3 if max_height_lines > 0 else 1)
            self.ax.set_xticks(x)
            self.ax.set_xticklabels(categories, rotation=45, ha="right")
            self.ax.set_title(title)
            self.ax.set_ylabel("Consommation (Barres)")
            self.ax2.set_ylabel("Consommation (Lignes)", rotation=270, labelpad=15)

            # Ajoute la légende des barres
            num_bars = len(legend_elements_bars) if legend_elements_bars else 0  # Définit num_bars même si aucune barre
            if legend_elements_bars:
                self.ax.legend(handles=legend_elements_bars, bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')

            # Ajoute la légende des lignes en dessous, si des lignes existent
            if legend_elements_lines:
                num_lines = len(legend_elements_lines)
                # Ajuste la position de la légende des lignes pour éviter la superposition
                self.ax2.legend(handles=legend_elements_lines, bbox_to_anchor=(1.05, 1 - (num_bars * 0.03 + 0.1)), loc='upper left', fontsize='small', title="Lignes")

            self.fig.tight_layout()
            self.canvas.draw()