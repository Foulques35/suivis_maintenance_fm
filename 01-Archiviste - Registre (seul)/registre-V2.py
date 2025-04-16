import os
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry, Calendar
from datetime import datetime, timedelta
import locale
import webbrowser

# Configuration de la locale pour les jours en français
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

# Chemins dynamiques
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db/events.db")
ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")
CONFIG_PATH = os.path.join(BASE_DIR, "config.txt")

# Charger la configuration
def load_config():
    config = {"Nature": [], "Site": []}
    current_section = None
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line.startswith("[") and line.endswith("]"):
                    current_section = line[1:-1]
                elif line and current_section in config:
                    config[current_section].append(line)
    return config

# Initialisation et mise à jour de la base de données
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, end_date TEXT, name TEXT NOT NULL,
        time_spent REAL, nature TEXT, site TEXT, description TEXT, attachments TEXT, finished INTEGER DEFAULT 0,
        recurrent INTEGER DEFAULT 0, periodicity TEXT
    )''')
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN recurrent INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN periodicity TEXT")
    except sqlite3.OperationalError:
        pass
    for col in ["date", "name", "description", "site", "nature"]:
        cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{col} ON events({col});')
    conn.commit()
    conn.close()

def create_attachments_dir():
    if not os.path.exists(ATTACHMENTS_DIR):
        os.makedirs(ATTACHMENTS_DIR)

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Projet Archiviste - Registre")
        self.geometry("1400x1000")
        self.configure(bg="white")

        style = ttk.Style(self)
        style.theme_use("clam")

        self.config = load_config()
        init_db()
        create_attachments_dir()
        self.attachments = []

        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(paned, width=900)
        paned.add(self.left_frame, weight=3)

        self.right_frame = ttk.Frame(paned, width=200)
        paned.add(self.right_frame, weight=1)

        button_frame = ttk.Frame(self.left_frame)
        button_frame.pack(anchor="nw", padx=10, pady=(10, 5))
        ttk.Button(button_frame, text="Vue Agenda", command=self.open_calendar_view).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Vue Planning", command=self.open_planning_view).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exporter", command=self.export_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Détaillé", command=self.export_detailed_data).pack(side=tk.LEFT, padx=5)
        ttk.Separator(self.left_frame, orient="horizontal").pack(fill="x", pady=5)

        search_frame = ttk.LabelFrame(self.left_frame, text="Recherche", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        first_line = ttk.Frame(search_frame)
        first_line.pack(fill=tk.X, pady=5)
        self.add_search_field(first_line, "Date", "search_date_var")
        self.add_search_field(first_line, "Site", "search_site_var")
        self.add_search_field(first_line, "Nature", "search_nature_var")
        ttk.Separator(search_frame, orient="horizontal").pack(fill="x", pady=5)
        second_line = ttk.Frame(search_frame)
        second_line.pack(fill=tk.X, pady=5)
        self.add_search_field(second_line, "Événement", "search_name_var")
        self.add_search_field(second_line, "Description", "search_desc_var")
        self.add_search_field(second_line, "Terminé", "search_finished_var")
        ttk.Button(second_line, text="Rechercher", command=self.search_events).pack(side=tk.LEFT, padx=5)

        filter_frame = ttk.LabelFrame(self.left_frame, text="Filtrer par Date", padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        self.filter_var = tk.StringVar(value="Pas de filtre")
        self.date_filter_combobox = ttk.Combobox(filter_frame, textvariable=self.filter_var, values=[
            "Pas de filtre", "Hier", "Aujourd'hui", "Demain", "Semaine dernière", "Cette semaine",
            "Semaine prochaine", "Ce mois-ci", "Mois prochain", "Mois précédent", "Cette année",
            "Année dernière", "Année suivante"
        ], state="readonly")
        self.date_filter_combobox.pack(fill=tk.X)
        self.date_filter_combobox.bind("<<ComboboxSelected>>", self.apply_date_filter)
        ttk.Separator(self.left_frame, orient="horizontal").pack(fill="x", pady=5)

        self.event_list = ttk.Treeview(self.left_frame, columns=("date", "site", "nature", "name", "finished"),
                                       show="headings", height=20)
        self.event_list.heading("date", text="Date", command=lambda: self.sort_column(self.event_list, "date", False))
        self.event_list.heading("site", text="Site", command=lambda: self.sort_column(self.event_list, "site", False))
        self.event_list.heading("nature", text="Nature", command=lambda: self.sort_column(self.event_list, "nature", False))
        self.event_list.heading("name", text="Événement", command=lambda: self.sort_column(self.event_list, "name", False))
        self.event_list.heading("finished", text="Terminé", command=lambda: self.sort_column(self.event_list, "finished", False))
        self.event_list.column("date", width=150, anchor="w", stretch=True)
        self.event_list.column("site", width=100, anchor="w", stretch=True)
        self.event_list.column("nature", width=100, anchor="w", stretch=True)
        self.event_list.column("name", width=200, anchor="w", stretch=True)
        self.event_list.column("finished", width=80, anchor="w", stretch=True)
        self.event_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.event_list.bind("<ButtonRelease-1>", self.load_event_details)

        self.create_right_panel()
        self.load_events()
        self.selected_event_id = None

    def add_search_field(self, frame, label, var_name):
        ttk.Label(frame, text=label).pack(side=tk.LEFT, padx=5)
        setattr(self, var_name, tk.StringVar())
        entry = ttk.Entry(frame, textvariable=getattr(self, var_name))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        entry.bind("<Return>", lambda e: self.search_events())
        getattr(self, var_name).trace("w", lambda *args: self.search_events())

    def create_right_panel(self):
        panel = ttk.LabelFrame(self.right_frame, text="Détails de l'Événement", padding=10)
        panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for label, entry_var in [("Date", "date_entry"), ("Date de Fin", "end_date_entry")]:
            ttk.Label(panel, text=label).pack(anchor="w", pady=2)
            setattr(self, entry_var, DateEntry(panel, date_pattern="y-mm-dd", width=15))
            getattr(self, entry_var).pack(fill=tk.X, pady=2)
            btn_frame = ttk.Frame(panel)
            btn_frame.pack(anchor="w", pady=2)
            for text, cmd in [("Aujourd'hui", f"set_{entry_var.split('_')[0]}_today"), ("Demain", f"set_{entry_var.split('_')[0]}_tommorow"),
                              ("Semaine Pro.", f"set_{entry_var.split('_')[0]}_next_week"), ("Mois Pro.", f"set_{entry_var.split('_')[0]}_next_month")]:
                ttk.Button(btn_frame, text=text, command=getattr(self, cmd)).pack(side=tk.LEFT, padx=2)
            ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=5)

        action_frame = ttk.Frame(panel)
        action_frame.pack(fill=tk.X, pady=5)
        for text, cmd in [("Sauvegarder", self.save_event), ("Créer Nouveau", self.create_new_event), ("Supprimer", self.delete_event)]:
            ttk.Button(action_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=5)
        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=5)

        for label, var_name, config_key in [("Site", "site_var", "Site"), ("Nature", "nature_var", "Nature")]:
            ttk.Label(panel, text=label).pack(anchor="w", pady=2)
            setattr(self, var_name, tk.StringVar())
            combobox = ttk.Combobox(panel, textvariable=getattr(self, var_name), values=self.config[config_key], state="readonly")
            combobox.pack(fill=tk.X, pady=2)
        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=5)

        ttk.Label(panel, text="Nom de l'Événement").pack(anchor="w", pady=2)
        self.name_entry = ttk.Entry(panel)
        self.name_entry.pack(fill=tk.X, pady=2)
        ttk.Label(panel, text="Description").pack(anchor="w", pady=2)
        self.description_text = tk.Text(panel, height=6, font=("Helvetica", 10))
        self.description_text.pack(fill=tk.X, pady=2)
        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=5)

        self.recurrent_var = tk.IntVar()
        ttk.Checkbutton(panel, text="Récurrent", variable=self.recurrent_var, command=self.toggle_periodicity).pack(anchor="w", pady=2)
        ttk.Label(panel, text="Périodicité").pack(anchor="w", pady=2)
        self.periodicity_var = tk.StringVar()
        self.periodicity_combobox = ttk.Combobox(panel, textvariable=self.periodicity_var, values=["Quotidienne", "Hebdomadaire", "Mensuelle", "Trimestrielle", "Annuelle"], state="disabled")
        self.periodicity_combobox.pack(fill=tk.X, pady=2)
        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=5)

        ttk.Label(panel, text="Temps Passé (heures)").pack(anchor="w", pady=2)
        self.time_spent_entry = ttk.Entry(panel)
        self.time_spent_entry.pack(fill=tk.X, pady=2)
        self.finished_var = tk.IntVar()
        ttk.Checkbutton(panel, text="Terminé", variable=self.finished_var).pack(anchor="w", pady=5)
        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=5)

        ttk.Label(panel, text="Pièces Jointes").pack(anchor="w", pady=2)
        self.attachment_listbox = tk.Listbox(panel, height=4, font=("Helvetica", 10))
        self.attachment_listbox.pack(fill=tk.X, pady=2)
        for text, cmd in [("Ajouter", self.add_attachments), ("Supprimer", self.remove_attachment), ("Ouvrir", self.open_attachment)]:
            ttk.Button(panel, text=f"{text} Pièce Jointe", command=cmd).pack(fill=tk.X, pady=2)

    def toggle_periodicity(self):
        state = "normal" if self.recurrent_var.get() else "disabled"
        self.periodicity_combobox.config(state=state)

    def set_date_today(self): self.date_entry.set_date(datetime.now())
    def set_date_tommorow(self): self.date_entry.set_date(datetime.now() + timedelta(days=1))
    def set_date_next_week(self): self.date_entry.set_date(datetime.now() + timedelta(weeks=1))
    def set_date_next_month(self): self.date_entry.set_date(datetime.now() + timedelta(days=30))
    def set_end_today(self): self.end_date_entry.set_date(datetime.now())
    def set_end_tommorow(self): self.end_date_entry.set_date(datetime.now() + timedelta(days=1))
    def set_end_next_week(self): self.end_date_entry.set_date(datetime.now() + timedelta(weeks=1))
    def set_end_next_month(self): self.end_date_entry.set_date(datetime.now() + timedelta(days=30))

    def open_calendar_view(self):
        window = tk.Toplevel(self)
        window.title("Vue Agenda")
        window.geometry("1000x600")
        window.configure(bg="white")

        left_frame = ttk.Frame(window)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10, pady=10)

        right_frame = ttk.LabelFrame(window, text="Événements du jour", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        cal = Calendar(left_frame, selectmode='day', date_pattern='y-mm-dd', font=("Helvetica", 12))
        cal.pack(pady=10)

        event_tree = ttk.Treeview(right_frame, columns=("name", "site", "nature", "duration"), show="headings", height=15)
        event_tree.heading("name", text="Événement", command=lambda: self.sort_column(event_tree, "name", False))
        event_tree.heading("site", text="Site", command=lambda: self.sort_column(event_tree, "site", False))
        event_tree.heading("nature", text="Nature", command=lambda: self.sort_column(event_tree, "nature", False))
        event_tree.heading("duration", text="Durée", command=lambda: self.sort_column(event_tree, "duration", False))
        event_tree.column("name", width=200, anchor="w", stretch=True)
        event_tree.column("site", width=100, anchor="w", stretch=True)
        event_tree.column("nature", width=100, anchor="w", stretch=True)
        event_tree.column("duration", width=80, anchor="w", stretch=True)
        event_tree.pack(fill=tk.BOTH, expand=True)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT date, end_date, name FROM events")
        events = cursor.fetchall()
        for start, end, name in events:
            try:
                start_date = datetime.strptime(start, "%Y-%m-%d")
                end_date = datetime.strptime(end, "%Y-%m-%d") if end else start_date
                current = start_date
                while current <= end_date:
                    cal.calevent_create(current, name.strip(), "event")
                    current += timedelta(days=1)
            except ValueError:
                pass
        conn.close()

        def update_events(event):
            selected_date = cal.get_date()
            event_tree.delete(*event_tree.get_children())
            events = self.get_events_for_day(selected_date)
            for i, evt in enumerate(events):
                duration = f"{evt[4] or 0} h" if evt[4] else "N/A"
                tag = f"event{i}"
                event_tree.insert("", "end", values=(evt[0], evt[2], evt[3], duration), tags=(tag,))
                event_tree.tag_configure(tag, background="#ffffff" if i % 2 == 0 else "#f0f0f0")
            right_frame.config(text=f"Événements du {selected_date}")

        cal.bind("<<CalendarSelected>>", update_events)

        def load_event_details_from_calendar(evt):
            sel = event_tree.selection()
            if sel:
                values = event_tree.item(sel, "values")
                event_name = values[0].strip()
                selected_date = cal.get_date()
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT id, end_date, site, nature, name, description, time_spent, attachments, finished FROM events WHERE date = ? AND TRIM(LOWER(REPLACE(name, ' ', ''))) LIKE LOWER(REPLACE(?, ' ', ''))", (selected_date, f"%{event_name}%"))
                event = cursor.fetchone()
                conn.close()
                if event:
                    self.selected_event_id = event[0]
                    self.date_entry.set_date(selected_date)
                    self.end_date_entry.set_date(event[1])
                    self.site_var.set(event[2])
                    self.nature_var.set(event[3])
                    self.name_entry.delete(0, tk.END)
                    self.name_entry.insert(0, event[4])
                    self.time_spent_entry.delete(0, tk.END)
                    self.time_spent_entry.insert(0, event[6] if event[6] else "")
                    self.description_text.delete("1.0", tk.END)
                    self.description_text.insert("1.0", event[5] if event[5] else "")
                    self.attachment_listbox.delete(0, tk.END)
                    self.attachments = event[7].split(",") if event[7] and event[7] != "None" else []
                    for att in self.attachments:
                        self.attachment_listbox.insert(tk.END, att)
                    self.finished_var.set(event[8])
                    window.destroy()

        event_tree.bind("<ButtonRelease-1>", load_event_details_from_calendar)

    def open_planning_view(self):
        window = tk.Toplevel(self)
        window.title("Vue Planning")
        window.geometry("1400x1000")

        # Utilisation d'un PanedWindow vertical pour les volets principaux
        main_paned = ttk.PanedWindow(window, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame pour le bouton "Marquer comme terminé" au-dessus des volets centraux
        button_frame = ttk.Frame(main_paned)
        main_paned.add(button_frame, weight=0)
        ttk.Button(button_frame, text="Marquer comme terminé", command=lambda: self.mark_as_finished(last_tree, non_rec_tree, rec_tree, upcoming_tree)).pack(pady=5)

        # PanedWindow horizontal pour Dernière Occurrence, Événements Récurrents, et À Venir
        upper_paned = ttk.PanedWindow(main_paned, orient=tk.HORIZONTAL)
        main_paned.add(upper_paned, weight=3)

        # Volet "Dernière Occurrence"
        last_frame = ttk.LabelFrame(upper_paned, text="Dernière Occurrence", padding=10)
        upper_paned.add(last_frame, weight=1)
        last_tree = ttk.Treeview(last_frame, columns=("id", "date", "site", "nature", "name"), show="headings", height=20)
        last_tree.heading("id", text="ID", command=lambda: self.sort_column(last_tree, "id", False))
        last_tree.heading("date", text="Date", command=lambda: self.sort_column(last_tree, "date", False))
        last_tree.heading("site", text="Site", command=lambda: self.sort_column(last_tree, "site", False))
        last_tree.heading("nature", text="Nature", command=lambda: self.sort_column(last_tree, "nature", False))
        last_tree.heading("name", text="Événement", command=lambda: self.sort_column(last_tree, "name", False))
        last_tree.column("id", width=0, stretch=tk.NO)
        last_tree.column("date", width=150, anchor="w", stretch=True)
        last_tree.column("site", width=150, anchor="w", stretch=True)
        last_tree.column("nature", width=150, anchor="w", stretch=True)
        last_tree.column("name", width=300, anchor="w", stretch=True)
        last_tree.pack(fill=tk.BOTH, expand=True)

        # Volet "Événements Récurrents Non Terminés"
        rec_frame = ttk.LabelFrame(upper_paned, text="Événements Récurrents Non Terminés", padding=10)
        upper_paned.add(rec_frame, weight=1)
        rec_tree = ttk.Treeview(rec_frame, columns=("id", "date", "site", "nature", "name"), show="headings", height=15)
        rec_tree.heading("id", text="ID", command=lambda: self.sort_column(rec_tree, "id", False))
        rec_tree.heading("date", text="Date", command=lambda: self.sort_column(rec_tree, "date", False))
        rec_tree.heading("site", text="Site", command=lambda: self.sort_column(rec_tree, "site", False))
        rec_tree.heading("nature", text="Nature", command=lambda: self.sort_column(rec_tree, "nature", False))
        rec_tree.heading("name", text="Événement", command=lambda: self.sort_column(rec_tree, "name", False))
        rec_tree.column("id", width=0, stretch=tk.NO)
        rec_tree.column("date", width=150, anchor="w", stretch=True)
        rec_tree.column("site", width=150, anchor="w", stretch=True)
        rec_tree.column("nature", width=150, anchor="w", stretch=True)
        rec_tree.column("name", width=300, anchor="w", stretch=True)
        rec_tree.pack(fill=tk.BOTH, expand=True)

        # Volet "À Venir"
        upcoming_frame = ttk.LabelFrame(upper_paned, text="À Venir", padding=10)
        upper_paned.add(upcoming_frame, weight=1)
        upcoming_tree = ttk.Treeview(upcoming_frame, columns=("id", "date", "site", "nature", "name"), show="headings", height=20)
        upcoming_tree.heading("id", text="ID", command=lambda: self.sort_column(upcoming_tree, "id", False))
        upcoming_tree.heading("date", text="Date", command=lambda: self.sort_column(upcoming_tree, "date", False))
        upcoming_tree.heading("site", text="Site", command=lambda: self.sort_column(upcoming_tree, "site", False))
        upcoming_tree.heading("nature", text="Nature", command=lambda: self.sort_column(upcoming_tree, "nature", False))
        upcoming_tree.heading("name", text="Événement", command=lambda: self.sort_column(upcoming_tree, "name", False))
        upcoming_tree.column("id", width=0, stretch=tk.NO)
        upcoming_tree.column("date", width=150, anchor="w", stretch=True)
        upcoming_tree.column("site", width=150, anchor="w", stretch=True)
        upcoming_tree.column("nature", width=150, anchor="w", stretch=True)
        upcoming_tree.column("name", width=300, anchor="w", stretch=True)
        upcoming_tree.pack(fill=tk.BOTH, expand=True)

        # Volet "Événements Non Récurrents Non Terminés" en bas, indépendant
        non_rec_frame = ttk.LabelFrame(main_paned, text="Événements Non Récurrents Non Terminés", padding=10)
        main_paned.add(non_rec_frame, weight=1)
        non_rec_tree = ttk.Treeview(non_rec_frame, columns=("id", "date", "site", "nature", "name"), show="headings", height=15)
        non_rec_tree.heading("id", text="ID", command=lambda: self.sort_column(non_rec_tree, "id", False))
        non_rec_tree.heading("date", text="Date", command=lambda: self.sort_column(non_rec_tree, "date", False))
        non_rec_tree.heading("site", text="Site", command=lambda: self.sort_column(non_rec_tree, "site", False))
        non_rec_tree.heading("nature", text="Nature", command=lambda: self.sort_column(non_rec_tree, "nature", False))
        non_rec_tree.heading("name", text="Événement", command=lambda: self.sort_column(non_rec_tree, "name", False))
        non_rec_tree.column("id", width=0, stretch=tk.NO)
        non_rec_tree.column("date", width=150, anchor="w", stretch=True)
        non_rec_tree.column("site", width=150, anchor="w", stretch=True)
        non_rec_tree.column("nature", width=150, anchor="w", stretch=True)
        non_rec_tree.column("name", width=300, anchor="w", stretch=True)
        non_rec_tree.pack(fill=tk.BOTH, expand=True)

        # Bouton Enregistrer
        save_button_frame = ttk.Frame(window)
        save_button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(save_button_frame, text="Enregistrer", command=lambda: self.save_planning_changes(last_tree, non_rec_tree, rec_tree, upcoming_tree)).pack(side=tk.RIGHT, padx=10)

        # Structure pour stocker les modifications
        self.planning_date_entries = {}

        # Chargement initial des données et adaptation des colonnes
        self.refresh_planning(last_tree, non_rec_tree, rec_tree, upcoming_tree)
        self.adjust_column_widths(window, [last_tree, rec_tree, upcoming_tree, non_rec_tree])

        # Redimensionnement dynamique des colonnes
        window.bind("<Configure>", lambda e: self.adjust_column_widths(window, [last_tree, rec_tree, upcoming_tree, non_rec_tree]))

        # Double-clic pour éditer la date
        def edit_date(event, tree, prefix):
            item = tree.identify_row(event.y)
            if item:
                col = tree.identify_column(event.x)
                if col == "#2":  # Colonne "Date"
                    event_id = tree.item(item, "values")[0]
                    name = tree.item(item, "values")[4]
                    site = tree.item(item, "values")[2]
                    nature = tree.item(item, "values")[3]
                    date = tree.item(item, "values")[1]  # Récupérer la date pour les événements à venir
                    if prefix == "upcoming":
                        key = f"{prefix}_{event_id}_{name}_{nature}_{site}_{date}"
                    else:
                        key = f"{prefix}_{event_id}_{name}_{nature}_{site}"
                    if key in self.planning_date_entries:
                        entry = self.planning_date_entries[key]
                        entry.place(x=tree.bbox(item, column=1)[0], y=tree.bbox(item)[1], width=150)
                        entry.focus_set()
                        entry.bind("<Return>", lambda e: entry.place_forget())
                        entry.bind("<FocusOut>", lambda e: entry.place_forget())

        last_tree.bind("<Double-1>", lambda e: edit_date(e, last_tree, "last"))
        non_rec_tree.bind("<Double-1>", lambda e: edit_date(e, non_rec_tree, "nonrec"))
        rec_tree.bind("<Double-1>", lambda e: edit_date(e, rec_tree, "rec"))
        upcoming_tree.bind("<Double-1>", lambda e: edit_date(e, upcoming_tree, "upcoming"))

    def sort_column(self, tree, col, reverse):
        # Récupérer les données triées
        data = [(tree.set(k, col), k) for k in tree.get_children('')]
        
        # Trier selon le type de données (dates ou texte)
        try:
            data.sort(key=lambda x: datetime.strptime(x[0], "%Y-%m-%d") if col == "date" else x[0], reverse=reverse)
        except ValueError:
            data.sort(key=lambda x: x[0], reverse=reverse)  # Tri par défaut pour texte ou autres cas

        # Réorganiser les éléments dans le Treeview
        for index, (val, k) in enumerate(data):
            tree.move(k, '', index)

        # Inverser l'ordre au prochain clic
        tree.heading(col, command=lambda: self.sort_column(tree, col, not reverse))

    def adjust_column_widths(self, window, trees):
        # Ajuster la largeur des colonnes en fonction de la largeur de chaque frame parent
        for tree in trees:
            frame = tree.master
            frame_width = frame.winfo_width() if frame.winfo_width() > 0 else 300  # Valeur par défaut si non défini
            total_columns = 4  # Exclure la colonne "id"
            base_width = int(frame_width // total_columns)  # Forcer un entier

            # Ajuster les largeurs avec un minimum pour éviter les problèmes d'affichage
            min_width = 50
            tree.column("date", width=max(int(base_width * 1.5), min_width), anchor="w", stretch=True)
            tree.column("site", width=max(base_width, min_width), anchor="w", stretch=True)
            tree.column("nature", width=max(base_width, min_width), anchor="w", stretch=True)
            tree.column("name", width=max(int(base_width * 2), min_width), anchor="w", stretch=True)

    def apply_filters(self):
        # Cette méthode est supprimée car nous ne voulons plus de filtres
        pass

    def mark_as_finished(self, last_tree, non_rec_tree, rec_tree, upcoming_tree):
        # Déterminer quel Treeview est actif (sélectionné)
        selected_trees = [non_rec_tree, rec_tree]
        active_tree = None
        for tree in selected_trees:
            if tree.selection():
                active_tree = tree
                break

        if not active_tree:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un événement à marquer comme terminé.")
            return

        item = active_tree.selection()[0]
        event_id = active_tree.item(item, "values")[0]
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Vérifier si l'événement est récurrent
        cursor.execute("SELECT date, site, nature, name, recurrent, finished, periodicity FROM events WHERE id=?", (event_id,))
        event = cursor.fetchone()
        if not event:
            messagebox.showerror("Erreur", "Événement non trouvé.")
            conn.close()
            return

        date, site, nature, name, recurrent, finished, periodicity = event

        # Mettre à jour l'événement sélectionné comme terminé
        cursor.execute("UPDATE events SET finished=1 WHERE id=?", (event_id,))

        # Si récurrent, créer une nouvelle occurrence avec la date suivante
        if recurrent:
            old_date = datetime.strptime(date, "%Y-%m-%d")
            next_date = self.calculate_next_date(old_date, periodicity)
            cursor.execute("INSERT INTO events (date, site, nature, name, finished, recurrent, periodicity) VALUES (?, ?, ?, ?, 0, 1, ?)",
                           (next_date.strftime("%Y-%m-%d"), site, nature, name, periodicity))

        conn.commit()
        conn.close()

        # Rafraîchir dynamiquement la vue Planning avec les nouveaux enregistrements
        self.refresh_planning(last_tree, non_rec_tree, rec_tree, upcoming_tree)

    def save_planning_changes(self, last_tree, non_rec_tree, rec_tree, upcoming_tree):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Mise à jour des événements non récurrents non terminés
        for item in non_rec_tree.get_children():
            event_id = non_rec_tree.item(item, "values")[0]
            name = non_rec_tree.item(item, "values")[4]
            nature = non_rec_tree.item(item, "values")[3]
            site = non_rec_tree.item(item, "values")[2]
            key = f"nonrec_{event_id}_{name}_{nature}_{site}"
            new_date = self.planning_date_entries[key].get()
            cursor.execute("UPDATE events SET date=? WHERE id=?", (new_date, event_id))

        # Mise à jour des événements récurrents non terminés
        for item in rec_tree.get_children():
            event_id = rec_tree.item(item, "values")[0]
            name = rec_tree.item(item, "values")[4]
            nature = rec_tree.item(item, "values")[3]
            site = rec_tree.item(item, "values")[2]
            key = f"rec_{event_id}_{name}_{nature}_{site}"
            new_date = self.planning_date_entries[key].get()
            cursor.execute("UPDATE events SET date=? WHERE id=?", (new_date, event_id))

        # Mise à jour des dernières occurrences
        for item in last_tree.get_children():
            event_id = last_tree.item(item, "values")[0]
            name = last_tree.item(item, "values")[4]
            nature = last_tree.item(item, "values")[3]
            site = last_tree.item(item, "values")[2]
            key = f"last_{event_id}_{name}_{nature}_{site}"
            new_date = self.planning_date_entries[key].get()
            cursor.execute("UPDATE events SET date=? WHERE id=?", (new_date, event_id))

        # Mise à jour des événements à venir
        for item in upcoming_tree.get_children():
            event_id = upcoming_tree.item(item, "values")[0]
            name = upcoming_tree.item(item, "values")[4]
            nature = upcoming_tree.item(item, "values")[3]
            site = upcoming_tree.item(item, "values")[2]
            date = upcoming_tree.item(item, "values")[1]  # Récupérer la date spécifique
            key = f"upcoming_{event_id}_{name}_{nature}_{site}_{date}"
            new_date = self.planning_date_entries[key].get()
            cursor.execute("UPDATE events SET date=? WHERE id=?", (new_date, event_id))

        conn.commit()
        conn.close()

        # Rafraîchir dynamiquement la vue Planning après les modifications
        self.refresh_planning(last_tree, non_rec_tree, rec_tree, upcoming_tree)

    def calculate_next_date(self, date, periodicity):
        if periodicity == "Quotidienne":
            new_date = date + timedelta(days=1)
        elif periodicity == "Hebdomadaire":
            new_date = date + timedelta(weeks=1)
        elif periodicity == "Mensuelle":
            new_date = date.replace(month=date.month % 12 + 1, year=date.year + (date.month // 12))
        elif periodicity == "Trimestrielle":
            new_date = date.replace(month=(date.month + 3 - 1) % 12 + 1, year=date.year + ((date.month + 2) // 12))
        elif periodicity == "Annuelle":
            new_date = date.replace(year=date.year + 1)
        else:
            new_date = date

        while new_date.weekday() >= 5:  # Éviter les week-ends
            new_date += timedelta(days=1)
        return new_date

    def refresh_planning(self, last_tree, non_rec_tree, rec_tree, upcoming_tree):
        last_tree.delete(*last_tree.get_children())
        non_rec_tree.delete(*non_rec_tree.get_children())
        rec_tree.delete(*rec_tree.get_children())
        upcoming_tree.delete(*upcoming_tree.get_children())
        self.planning_date_entries.clear()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        # Événements non récurrents (uniquement non terminés)
        cursor.execute("SELECT id, date, site, nature, name, finished FROM events WHERE recurrent=0 AND finished=0 ORDER BY date ASC")
        non_rec_events = cursor.fetchall()
        for i, (event_id, date, site, nature, name, finished) in enumerate(non_rec_events):
            key = f"{event_id}_{name}_{nature}_{site}"
            bg_color = "#ffcccc" if datetime.strptime(date, "%Y-%m-%d") < datetime.now() else "#ffffff" if i % 2 == 0 else "#f0f0f0"
            non_rec_tree.insert("", "end", values=(event_id, date, site, nature, name), tags=(f"nonrec{i}",))
            non_rec_tree.tag_configure(f"nonrec{i}", background=bg_color)
            self.planning_date_entries[f"nonrec_{key}"] = ttk.Entry(non_rec_tree, width=15)
            self.planning_date_entries[f"nonrec_{key}"].insert(0, date)
            non_rec_tree.set(non_rec_tree.get_children()[-1], "date", date)

        # Événements récurrents avec regroupement (non terminés avant ou à aujourd’hui)
        cursor.execute("SELECT MIN(id) as id, MIN(date) as date, site, nature, name, finished, recurrent, periodicity FROM events WHERE recurrent=1 AND date <= ? GROUP BY name, nature, site, periodicity HAVING finished=0 ORDER BY date ASC", (today,))
        rec_events = cursor.fetchall()
        for i, (event_id, date, site, nature, name, finished, recurrent, periodicity) in enumerate(rec_events):
            key = f"{event_id}_{name}_{nature}_{site}"
            bg_color = "#ffcccc" if datetime.strptime(date, "%Y-%m-%d") < datetime.now() else "#ffffff" if i % 2 == 0 else "#f0f0f0"
            rec_tree.insert("", "end", values=(event_id, date, site, nature, name), tags=(f"rec{i}",))
            rec_tree.tag_configure(f"rec{i}", background=bg_color)
            self.planning_date_entries[f"rec_{key}"] = ttk.Entry(rec_tree, width=15)
            self.planning_date_entries[f"rec_{key}"].insert(0, date)
            rec_tree.set(rec_tree.get_children()[-1], "date", date)

        # Dernière Occurrence (uniquement les récurrents terminés avant ou à aujourd’hui)
        cursor.execute("SELECT id, date, site, nature, name FROM events WHERE recurrent=1 AND finished=1 AND date <= ? ORDER BY date DESC", (today,))
        last_events = cursor.fetchall()
        print(f"Dernière Occurrence - Résultats de la requête : {last_events}")  # Débogage
        for i, (event_id, date, site, nature, name) in enumerate(last_events):
            key = f"{event_id}_{name}_{nature}_{site}"
            last_tree.insert("", "end", values=(event_id, date, site, nature, name), tags=(f"last{i}",))
            last_tree.tag_configure(f"last{i}", background="#ffffff" if i % 2 == 0 else "#f0f0f0")
            self.planning_date_entries[f"last_{key}"] = ttk.Entry(last_tree, width=15)
            self.planning_date_entries[f"last_{key}"].insert(0, date)
            last_tree.set(last_tree.get_children()[-1], "date", date)

        # À Venir (uniquement les récurrents futurs non terminés)
        cursor.execute("SELECT id, date, site, nature, name FROM events WHERE recurrent=1 AND finished=0 AND date > ? ORDER BY date ASC", (today,))
        upcoming_events = cursor.fetchall()
        for i, (event_id, date, site, nature, name) in enumerate(upcoming_events):
            key = f"{event_id}_{name}_{nature}_{site}_{date}"
            upcoming_tree.insert("", "end", values=(event_id, date, site, nature, name), tags=(f"upcoming{i}",))
            upcoming_tree.tag_configure(f"upcoming{i}", background="#ffffff" if i % 2 == 0 else "#f0f0f0")
            self.planning_date_entries[f"upcoming_{key}"] = ttk.Entry(upcoming_tree, width=15)
            self.planning_date_entries[f"upcoming_{key}"].insert(0, date)
            upcoming_tree.set(upcoming_tree.get_children()[-1], "date", date)

        conn.close()

    def get_events_for_day(self, date):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, site, nature, time_spent, finished FROM events WHERE date <= ? AND (end_date IS NULL OR end_date >= ?)", (date, date))
        events = cursor.fetchall()
        conn.close()
        return events

    def export_data(self):
        file_path = filedialog.asksaveasfilename(initialfile=f"registre_export_{datetime.now().strftime('%Y%m%d')}.txt", defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    for row_id in self.event_list.get_children():
                        row = self.event_list.item(row_id, "values")
                        f.write(f"{row[0]}, {row[1]}, {row[2]}, {row[3]}, {row[4]}\n")
                messagebox.showinfo("Succès", f"Exporté dans {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec de l'exportation : {e}")

    def export_detailed_data(self):
        file_path = filedialog.asksaveasfilename(initialfile=f"registre_detaillé_export_{datetime.now().strftime('%Y%m%d')}.txt", defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    for row_id in self.event_list.get_children():
                        row = self.event_list.item(row_id, "values")
                        event_date = row[0].split(" - ")[0]
                        event_name = row[3].strip()
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("SELECT date, end_date, site, nature, name, description, time_spent, attachments, finished FROM events WHERE date = ? AND TRIM(LOWER(REPLACE(name, ' ', ''))) LIKE LOWER(REPLACE(?, ' ', ''))", (event_date, f"%{event_name}%"))
                        event = cursor.fetchone()
                        conn.close()
                        if event:
                            finished = "Oui" if event[8] else "Non"
                            date_str = self.format_date_with_day(event[0]) if event[0] else ""
                            end_date_str = self.format_date_with_day(event[1]) if event[1] else ""
                            f.write(f"----\nDate: {date_str}\nDate de Fin: {end_date_str}\nSite: {event[2]}\nNature: {event[3]}\nNom: {event[4]}\nDescription: {event[5] or 'Aucune'}\nTemps passé: {event[6] or 0} heures\nPièces jointes: {event[7] or 'Aucune'}\nTerminé: {finished}\n----\n\n")
                messagebox.showinfo("Succès", f"Exporté dans {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec de l'exportation : {e}")

    def add_attachments(self):
        filepaths = filedialog.askopenfilenames()
        for filepath in filepaths:
            filename = os.path.basename(filepath)
            dest = os.path.join(ATTACHMENTS_DIR, filename)
            os.rename(filepath, dest)
            if filename not in self.attachments:
                self.attachments.append(filename)
                self.attachment_listbox.insert(tk.END, filename)

    def remove_attachment(self):
        sel = self.attachment_listbox.curselection()
        if sel:
            filename = self.attachment_listbox.get(sel)
            self.attachments.remove(filename)
            self.attachment_listbox.delete(sel)

    def open_attachment(self):
        sel = self.event_list.selection()
        if sel:
            event_date = self.event_list.item(sel, "values")[0].split(" - ")[0]
            event_name = self.event_list.item(sel, "values")[3].strip()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT attachments FROM events WHERE date = ? AND TRIM(LOWER(REPLACE(name, ' ', ''))) LIKE LOWER(REPLACE(?, ' ', ''))", (event_date, f"%{event_name}%"))
            attachments = cursor.fetchone()[0]
            conn.close()
            if attachments and attachments != "None":
                for attachment in attachments.split(","):
                    filepath = os.path.join(ATTACHMENTS_DIR, attachment)
                    if os.path.exists(filepath):
                        webbrowser.open(filepath)
                    else:
                        messagebox.showerror("Erreur", f"Pièce jointe {attachment} introuvable")
            else:
                messagebox.showerror("Erreur", "Aucune pièce jointe")
        else:
            messagebox.showerror("Erreur", "Sélectionnez un événement")

    def delete_event(self):
        if self.selected_event_id and messagebox.askyesno("Confirmation", "Supprimer cet événement ?"):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE id = ?", (self.selected_event_id,))
            conn.commit()
            conn.close()
            self.reset_form()
            self.apply_current_filter()
            messagebox.showinfo("Succès", "Événement supprimé")

    def save_event(self):
        date = self.date_entry.get()
        end_date = self.end_date_entry.get()
        site = self.site_var.get()
        nature = self.nature_var.get()
        name = self.name_entry.get().strip()
        time_spent = self.time_spent_entry.get()
        description = self.description_text.get("1.0", tk.END).strip()
        attachments = ",".join(self.attachments) if self.attachments else "None"
        finished = self.finished_var.get()
        recurrent = self.recurrent_var.get()
        periodicity = self.periodicity_var.get() if recurrent else None

        if not name:
            messagebox.showerror("Erreur", "Le nom est obligatoire")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if self.selected_event_id:
            cursor.execute("UPDATE events SET date=?, end_date=?, site=?, nature=?, name=?, time_spent=?, description=?, attachments=?, finished=?, recurrent=?, periodicity=? WHERE id=?",
                           (date, end_date, site, nature, name, time_spent, description, attachments, finished, recurrent, periodicity, self.selected_event_id))
        else:
            cursor.execute("INSERT INTO events (date, end_date, site, nature, name, time_spent, description, attachments, finished, recurrent, periodicity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (date, end_date, site, nature, name, time_spent, description, attachments, finished, recurrent, periodicity))
        conn.commit()
        conn.close()
        self.reset_form()
        self.apply_current_filter()
        messagebox.showinfo("Succès", "Événement sauvegardé")

    def create_new_event(self):
        self.selected_event_id = None
        self.save_event()

    def reset_form(self):
        self.date_entry.set_date(None)
        self.end_date_entry.set_date(None)
        self.site_var.set("")
        self.nature_var.set("")
        self.name_entry.delete(0, tk.END)
        self.time_spent_entry.delete(0, tk.END)
        self.description_text.delete("1.0", tk.END)
        self.attachment_listbox.delete(0, tk.END)
        self.attachments = []
        self.finished_var.set(0)
        self.recurrent_var.set(0)
        self.periodicity_combobox.config(state="disabled")
        self.periodicity_var.set("")
        self.selected_event_id = None

    def apply_current_filter(self):
        if self.filter_var.get() != "Pas de filtre":
            self.apply_date_filter()
        elif any(var.get() for var in [self.search_date_var, self.search_site_var, self.search_nature_var, 
                                       self.search_name_var, self.search_desc_var, self.search_finished_var]):
            self.search_events()
        else:
            self.load_events()

    def load_event_details(self, event):
        sel = self.event_list.selection()
        if sel:
            values = self.event_list.item(sel, "values")
            event_date = values[0].split(" - ")[0] if values[0] else None
            event_name = values[3].strip()

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, end_date, site, nature, name, description, time_spent, attachments, finished, recurrent, periodicity FROM events WHERE date = ? AND TRIM(LOWER(REPLACE(name, ' ', ''))) LIKE LOWER(REPLACE(?, ' ', ''))", (event_date, f"%{event_name}%"))
            event = cursor.fetchone()
            conn.close()

            if event:
                self.selected_event_id = event[0]
                self.date_entry.set_date(event_date)
                self.end_date_entry.set_date(event[1])
                self.site_var.set(event[2])
                self.nature_var.set(event[3])
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, event[4])
                self.time_spent_entry.delete(0, tk.END)
                self.time_spent_entry.insert(0, event[6] if event[6] else "")
                self.description_text.delete("1.0", tk.END)
                self.description_text.insert("1.0", event[5] if event[5] else "")
                self.attachment_listbox.delete(0, tk.END)
                self.attachments = event[7].split(",") if event[7] and event[7] != "None" else []
                for att in self.attachments:
                    self.attachment_listbox.insert(tk.END, att)
                self.finished_var.set(event[8])
                self.recurrent_var.set(event[9])
                self.periodicity_combobox.config(state="normal" if event[9] else "disabled")
                self.periodicity_var.set(event[10] if event[10] else "")

    def load_events(self):
        self.event_list.delete(*self.event_list.get_children())
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT date, site, nature, name, finished FROM events ORDER BY date ASC")
        for i, event in enumerate(cursor.fetchall()):
            finished = "Oui" if event[4] else "Non"
            date_str = self.format_date_with_day(event[0]) if event[0] else ""
            tag = f"row{i}"
            self.event_list.insert("", "end", values=(date_str, event[1], event[2], event[3], finished), tags=(tag,))
            self.event_list.tag_configure(tag, background="#ffffff" if i % 2 == 0 else "#f0f0f0")
        conn.close()

    def search_events(self):
        self.event_list.delete(*self.event_list.get_children())
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT date, site, nature, name, finished FROM events WHERE 1=1"
        params = []
        for var, col in [(self.search_date_var, "date"), (self.search_site_var, "site"), (self.search_nature_var, "nature"),
                         (self.search_name_var, "name"), (self.search_desc_var, "description")]:
            if var.get():
                query += f" AND LOWER({col}) LIKE LOWER(?)"
                params.append(f"%{var.get()}%")
        if self.search_finished_var.get().lower() in ["oui", "non"]:
            query += " AND finished = ?"
            params.append(1 if self.search_finished_var.get().lower() == "oui" else 0)
        cursor = conn.cursor()
        cursor.execute(query, params)
        for i, event in enumerate(cursor.fetchall()):
            finished = "Oui" if event[4] else "Non"
            date_str = self.format_date_with_day(event[0]) if event[0] else ""
            tag = f"row{i}"
            self.event_list.insert("", "end", values=(date_str, event[1], event[2], event[3], finished), tags=(tag,))
            self.event_list.tag_configure(tag, background="#ffffff" if i % 2 == 0 else "#f0f0f0")
        conn.close()

    def apply_date_filter(self, event=None):
        today = datetime.now()
        filter_choice = self.filter_var.get()
        filters = {
            "Aujourd'hui": (today, today), "Demain": (today + timedelta(days=1), today + timedelta(days=1)),
            "Hier": (today - timedelta(days=1), today - timedelta(days=1)),
            "Cette semaine": (today - timedelta(days=today.weekday()), today + timedelta(days=6 - today.weekday())),
            "Semaine dernière": (today - timedelta(days=today.weekday() + 7), today - timedelta(days=today.weekday() + 1)),
            "Semaine prochaine": (today - timedelta(days=7 - today.weekday()), today + timedelta(days=13 - today.weekday())),
            "Ce mois-ci": (today.replace(day=1), (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)),
            "Mois prochain": ((today.replace(day=28) + timedelta(days=4)).replace(day=1), (today.replace(day=28) + timedelta(days=35)).replace(day=1) - timedelta(days=1)),
            "Mois précédent": ((today.replace(day=1) - timedelta(days=1)).replace(day=1), today.replace(day=1) - timedelta(days=1)),
            "Cette année": (today.replace(month=1, day=1), today.replace(month=12, day=31)),
            "Année dernière": (today.replace(year=today.year - 1, month=1, day=1), today.replace(year=today.year - 1, month=12, day=31)),
            "Année suivante": (today.replace(year=today.year + 1, month=1, day=1), today.replace(year=today.year + 1, month=12, day=31))
        }
        start_date, end_date = filters.get(filter_choice, (None, None))
        self.load_filtered_events(start_date, end_date)

    def load_filtered_events(self, start_date, end_date):
        self.event_list.delete(*self.event_list.get_children())
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        query = "SELECT date, site, nature, name, finished FROM events"
        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            cursor.execute(query, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        else:
            cursor.execute(query)
        for i, event in enumerate(cursor.fetchall()):
            finished = "Oui" if event[4] else "Non"
            date_str = self.format_date_with_day(event[0]) if event[0] else ""
            tag = f"row{i}"
            self.event_list.insert("", "end", values=(date_str, event[1], event[2], event[3], finished), tags=(tag,))
            self.event_list.tag_configure(tag, background="#ffffff" if i % 2 == 0 else "#f0f0f0")
        conn.close()

    def sort_column(self, tree, col, reverse):
        # Récupérer les données triées
        data = [(tree.set(k, col), k) for k in tree.get_children('')]
        
        # Trier selon le type de données (dates ou texte)
        try:
            data.sort(key=lambda x: datetime.strptime(x[0], "%Y-%m-%d") if col == "date" else x[0], reverse=reverse)
        except ValueError:
            data.sort(key=lambda x: x[0], reverse=reverse)  # Tri par défaut pour texte ou autres cas

        # Réorganiser les éléments dans le Treeview
        for index, (val, k) in enumerate(data):
            tree.move(k, '', index)

        # Inverser l'ordre au prochain clic
        tree.heading(col, command=lambda: self.sort_column(tree, col, not reverse))

    def format_date_with_day(self, date_str):
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d - %A") if date_str else ""

    def is_weekend(self, date_str):
        return datetime.strptime(date_str, "%Y-%m-%d").weekday() >= 5 if date_str else False

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()