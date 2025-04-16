import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
from datetime import datetime

class MeterGraphs:
    def __init__(self, parent):
        self.parent = parent
        self.conn = None  # Connexion à la base de données (sera passée par ArchivisteApp)
        self.cursor = None

        self.main_frame = ttk.LabelFrame(self.parent, text="Graphiques des Relevés")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Frame pour les filtres
        self.filters_frame = ttk.Frame(self.main_frame)
        self.filters_frame.pack(fill="x", padx=5, pady=5)

        # Liste déroulante pour les compteurs
        ttk.Label(self.filters_frame, text="Compteur :").pack(side="left", padx=5)
        self.meter_combobox = ttk.Combobox(self.filters_frame, state="readonly")
        self.meter_combobox.pack(side="left", padx=5)
        self.meter_combobox.bind("<<ComboboxSelected>>", self.update_parameters_combobox)

        # Liste déroulante pour les paramètres
        ttk.Label(self.filters_frame, text="Paramètre :").pack(side="left", padx=5)
        self.parameter_combobox = ttk.Combobox(self.filters_frame, state="readonly")
        self.parameter_combobox.pack(side="left", padx=5)
        self.parameter_combobox.bind("<<ComboboxSelected>>", self.plot_graph)

        # Frame pour le graphique
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.main_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_meters_to_combobox(self):
        if not self.conn or not self.cursor:
            messagebox.showwarning("Erreur", "Connexion à la base de données non initialisée.")
            return
        self.cursor.execute("SELECT id, name FROM meters")
        meters = self.cursor.fetchall()
        if not meters:
            messagebox.showinfo("Information", "Aucun compteur n'est disponible. Ajoutez des compteurs dans l'onglet 'Gestion relevés'.")
            self.meter_combobox["values"] = []
            self.parameter_combobox["values"] = []
            return
        meter_names = [meter[1] for meter in meters]
        self.meter_combobox["values"] = meter_names
        if meter_names:
            self.meter_combobox.current(0)
            self.update_parameters_combobox()

    def update_parameters_combobox(self, event=None):
        if not self.conn or not self.cursor:
            return
        selected_meter = self.meter_combobox.get()
        if not selected_meter:
            self.parameter_combobox["values"] = []
            return
        self.cursor.execute("SELECT id FROM meters WHERE name = ?", (selected_meter,))
        meter_id = self.cursor.fetchone()
        if not meter_id:
            self.parameter_combobox["values"] = []
            return
        meter_id = meter_id[0]
        self.cursor.execute("SELECT name FROM parameters WHERE meter_id = ?", (meter_id,))
        parameters = self.cursor.fetchall()
        if not parameters:
            messagebox.showinfo("Information", f"Aucun paramètre n'est disponible pour le compteur '{selected_meter}'. Ajoutez des paramètres dans l'onglet 'Gestion relevés'.")
            self.parameter_combobox["values"] = []
            return
        parameter_names = [param[0] for param in parameters]
        self.parameter_combobox["values"] = parameter_names
        if parameter_names:
            self.parameter_combobox.current(0)
            self.plot_graph()

    def plot_graph(self, event=None):
        if not self.conn or not self.cursor:
            return
        selected_meter = self.meter_combobox.get()
        selected_parameter = self.parameter_combobox.get()
        if not selected_meter or not selected_parameter:
            return

        self.cursor.execute("SELECT id FROM meters WHERE name = ?", (selected_meter,))
        meter_id = self.cursor.fetchone()
        if not meter_id:
            return
        meter_id = meter_id[0]
        
        self.cursor.execute("SELECT id FROM parameters WHERE meter_id = ? AND name = ?", (meter_id, selected_parameter))
        parameter_id = self.cursor.fetchone()
        if not parameter_id:
            return
        parameter_id = parameter_id[0]

        self.cursor.execute("SELECT date, value FROM readings WHERE meter_id = ? AND parameter_id = ? ORDER BY date", (meter_id, parameter_id))
        readings = self.cursor.fetchall()

        self.ax.clear()
        if not readings:
            self.ax.set_title(f"Relevés pour {selected_meter} - {selected_parameter} (Aucune donnée)")
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Valeur")
            self.canvas.draw()
            return

        dates = [datetime.strptime(reading[0], '%Y-%m-%d') for reading in readings]
        values = [reading[1] for reading in readings]

        self.ax.plot(dates, values, marker='o')
        self.ax.set_title(f"Relevés pour {selected_meter} - {selected_parameter}")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Valeur")
        self.canvas.draw()