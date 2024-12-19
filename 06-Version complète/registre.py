import os
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry, Calendar
from datetime import datetime, timedelta
import locale
import webbrowser

# Configuration de la locale pour obtenir les jours de la semaine en français
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

# Chemin dynamique basé sur l'emplacement du fichier Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chemin vers la base de données SQLite (relatif à l'emplacement du script)
DB_PATH = os.path.join(BASE_DIR, "db/events.db")
ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")
CONFIG_PATH = os.path.join(BASE_DIR, "config.txt")  # Chemin du fichier de configuration

# Lecture du fichier de configuration pour les listes de choix uniques
def load_config():
    config = {
        "Nature": [],
        "Site": []
    }
    
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

def init_db():
    """Initialiser la base de données et créer la table si elle n'existe pas, avec des index pour les champs recherchés"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            end_date TEXT,
            name TEXT NOT NULL,
            time_spent REAL,
            nature TEXT,
            site TEXT,
            description TEXT,
            attachments TEXT,
            finished INTEGER DEFAULT 0
        )
    ''')
    # Création des index pour les champs couramment recherchés
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON events(date);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON events(name);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_description ON events(description);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_site ON events(site);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_nature ON events(nature);')

    conn.commit()
    conn.close()

def create_attachments_dir():
    """Créer le dossier des pièces jointes si nécessaire"""
    if not os.path.exists(ATTACHMENTS_DIR):
        os.makedirs(ATTACHMENTS_DIR)

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Projet Archiviste - registre")
        self.geometry("1280x800")

        # Charger la configuration pour les listes de choix uniques
        self.config = load_config()

        # Initialiser la base de données
        init_db()
        create_attachments_dir()

        # Stocker les pièces jointes temporaires
        self.attachments = []

        # Frame principale
        main_frame = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=1)

        # Volet de gauche
        self.left_frame = ttk.Frame(main_frame, width=900)
        main_frame.add(self.left_frame)
        self.left_frame.pack_propagate(False)

        # Volet de droite
        self.right_frame = ttk.Frame(main_frame, width=200)
        main_frame.add(self.right_frame)
        self.right_frame.pack_propagate(False)

        # Disposition des boutons "Vue agenda" et "Exporter"
        button_frame = ttk.Frame(self.left_frame)
        button_frame.pack(anchor=tk.W, padx=10, pady=10)
        ttk.Button(button_frame, text="Vue agenda", command=self.open_calendar_view).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exporter", command=self.export_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export détaillé", command=self.export_detailed_data).pack(side=tk.LEFT, padx=5)

        # Barre de recherche : nom, description, terminé
        search_frame = ttk.Frame(self.left_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        # Première ligne de recherche : Date, Site, Nature
        first_line_search_frame = ttk.Frame(search_frame)
        first_line_search_frame.pack(fill=tk.X, padx=5, pady=5)

        # Barre de recherche pour Date
        ttk.Label(first_line_search_frame, text="Date").pack(side=tk.LEFT, padx=5)
        self.search_date_var = tk.StringVar()
        search_date_entry = ttk.Entry(first_line_search_frame, textvariable=self.search_date_var)
        search_date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Barre de recherche pour Site
        ttk.Label(first_line_search_frame, text="Site").pack(side=tk.LEFT, padx=5)
        self.search_site_var = tk.StringVar()
        search_site_entry = ttk.Entry(first_line_search_frame, textvariable=self.search_site_var)
        search_site_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Barre de recherche pour Nature
        ttk.Label(first_line_search_frame, text="Nature").pack(side=tk.LEFT, padx=5)
        self.search_nature_var = tk.StringVar()
        search_nature_entry = ttk.Entry(first_line_search_frame, textvariable=self.search_nature_var)
        search_nature_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Deuxième ligne de recherche : Événement, Description, Terminé
        second_line_search_frame = ttk.Frame(search_frame)
        second_line_search_frame.pack(fill=tk.X, padx=5, pady=5)

        # Barre de recherche pour Événement
        ttk.Label(second_line_search_frame, text="Événement").pack(side=tk.LEFT, padx=5)
        self.search_name_var = tk.StringVar()
        search_name_entry = ttk.Entry(second_line_search_frame, textvariable=self.search_name_var)
        search_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Barre de recherche pour Description
        ttk.Label(second_line_search_frame, text="Description").pack(side=tk.LEFT, padx=5)
        self.search_desc_var = tk.StringVar()
        search_desc_entry = ttk.Entry(second_line_search_frame, textvariable=self.search_desc_var)
        search_desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Barre de recherche pour Terminé
        ttk.Label(second_line_search_frame, text="Terminé").pack(side=tk.LEFT, padx=5)
        self.search_finished_var = tk.StringVar()
        search_finished_entry = ttk.Entry(second_line_search_frame, textvariable=self.search_finished_var)
        search_finished_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Bouton Rechercher
        ttk.Button(second_line_search_frame, text="Rechercher", command=self.search_events).pack(side=tk.LEFT, padx=5)

        # Filtre des dates
        ttk.Label(self.left_frame, text="Filtrer par Date").pack(anchor=tk.W)
        self.filter_var = tk.StringVar()
        self.date_filter_combobox = ttk.Combobox(self.left_frame, textvariable=self.filter_var)
        self.date_filter_combobox['values'] = [
            "Pas de filtre", "Hier", "Aujourd'hui", "Demain", "Semaine dernière", "Cette semaine", "Semaine prochaine", "Ce mois-ci", "Mois prochain",
            "Mois précédent", "Cette année", "Année dernière", "Année suivante"
        ]
        self.date_filter_combobox.current(0)
        self.date_filter_combobox.pack(fill=tk.X)
        self.date_filter_combobox.bind("<Double-Button-1>", lambda e: self.date_filter_combobox.event_generate('<Down>'))
        self.date_filter_combobox.bind("<<ComboboxSelected>>", self.apply_date_filter)

        # Liste des événements
        self.event_list = ttk.Treeview(self.left_frame, columns=(
            "date", "end_date", "site", "nature", "name", "description", "finished", "time_spent", "attachments"),
            show="headings")

        # Configuration des colonnes
        self.event_list.heading("date", text="Date", command=lambda: self.sort_column("date", False))
        self.event_list.heading("end_date", text="Date de Fin", command=lambda: self.sort_column("end_date", False))
        self.event_list.heading("site", text="Site", command=lambda: self.sort_column("site", False))
        self.event_list.heading("nature", text="Nature", command=lambda: self.sort_column("nature", False))
        self.event_list.heading("name", text="Événement", command=lambda: self.sort_column("name", False))
        self.event_list.heading("description", text="Description", command=lambda: self.sort_column("description", False))
        self.event_list.heading("finished", text="Terminé", command=lambda: self.sort_column("finished", False))
        self.event_list.heading("time_spent", text="Temps Passé", command=lambda: self.sort_column("time_spent", False))
        self.event_list.heading("attachments", text="Pièces Jointes", command=lambda: self.sort_column("attachments", False))
        self.event_list.pack(fill=tk.BOTH, expand=1)

        self.event_list.bind("<ButtonRelease-1>", self.load_event_details)

        # Étiquette pour afficher la somme du "Temps Passé"
        #self.time_spent_sum_label = ttk.Label(self.left_frame, text="Total Temps Passé : 0")
        #self.time_spent_sum_label.pack(anchor=tk.W, pady=10)

        self.load_events()

        # Ajouter les champs du volet droit dans le même ordre que les colonnes
        self.create_right_panel()

        # Variable pour stocker l'ID de l'événement sélectionné
        self.selected_event_id = None

    def open_calendar_view(self):
        """Ouvre une nouvelle fenêtre pour afficher la vue agenda"""
        calendar_window = tk.Toplevel(self)
        calendar_window.title("Vue agenda")
        calendar_window.geometry("1000x600")

        # Agenda en colonne gauche
        left_calendar_frame = ttk.Frame(calendar_window)
        left_calendar_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # Volet de droite pour afficher les événements du jour sélectionné
        right_event_frame = ttk.Frame(calendar_window)
        right_event_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        # Créer le calendrier
        cal = Calendar(left_calendar_frame, selectmode='day', date_pattern='y-mm-dd', font=("Arial", 14), width=15, height=7)
        cal.pack(pady=20)

        # Ajouter les événements sélectionnés dans le calendrier
        def show_events_for_selected_date():
            selected_date = cal.get_date()
            for widget in right_event_frame.winfo_children():
                widget.destroy()  # Clear previous events

            events = self.get_events_for_day(selected_date)
            if events:
                for event in events:
                    ttk.Label(right_event_frame, text=f"Site: {event[2]}").pack(anchor=tk.W)
                    ttk.Label(right_event_frame, text=f"Événement: {event[0]}").pack(anchor=tk.W)
                    ttk.Label(right_event_frame, text=f"Description: {event[1]}").pack(anchor=tk.W)
                    ttk.Label(right_event_frame, text=f"Nature: {event[3]}").pack(anchor=tk.W)
                    ttk.Label(right_event_frame, text=f"Temps passé: {event[4]} heures").pack(anchor=tk.W)
                    # Ajouter la ligne "Terminé"
                    termine = "Oui" if event[5] == 1 else "Non"
                    ttk.Label(right_event_frame, text=f"Terminé: {termine}").pack(anchor=tk.W)
                    ttk.Separator(right_event_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
            else:
                ttk.Label(right_event_frame, text="Aucun événement pour ce jour").pack(pady=20)

        # Bouton pour voir les événements d'un jour
        ttk.Button(left_calendar_frame, text="Voir événements", command=show_events_for_selected_date).pack(pady=10)

        # Mettre à jour les jours du calendrier avec des événements colorés
        self.update_calendar_with_events(cal)

    def update_calendar_with_events(self, cal):
        """Colorer les cases du calendrier qui ont des événements"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT date, end_date FROM events")
        events = cursor.fetchall()
        conn.close()

        for event in events:
            start_date = datetime.strptime(event[0], "%Y-%m-%d")
            end_date = datetime.strptime(event[1], "%Y-%m-%d") if event[1] else start_date
            current_date = start_date

            # Colorer toutes les dates entre le début et la fin de l'événement
            while current_date <= end_date:
                cal.calevent_create(current_date, 'Event', 'event')
                current_date += timedelta(days=1)

        cal.tag_configure('event', background='lightblue', foreground='black')

    def get_events_for_day(self, selected_date):
        """Récupère les événements pour un jour donné"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, site, nature, time_spent, finished FROM events WHERE date <= ? AND (end_date IS NULL OR end_date >= ?)",
                       (selected_date, selected_date))
        events = cursor.fetchall()
        conn.close()
        return events

    def export_data(self):
        """Exporter les données filtrées dans un fichier texte avec un nom de fichier par défaut."""
        from datetime import datetime
        
        # Définir un nom de fichier par défaut basé sur la date actuelle
        default_file_name = f"registre_export_{datetime.now().strftime('%Y%m%d')}.txt"
        
        # Ouvrir une boîte de dialogue pour enregistrer le fichier
        file_path = filedialog.asksaveasfilename(
            initialfile=default_file_name,  # Nom par défaut
            defaultextension=".txt", 
            filetypes=[("Text files", "*.txt")]
        )
        
        if not file_path:
            return  # Si l'utilisateur annule l'exportation

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                # Exporter les données ligne par ligne
                for row_id in self.event_list.get_children():
                    row_data = self.event_list.item(row_id, "values")
                    f.write(", ".join(row_data) + "\n")
            
            messagebox.showinfo("Exportation réussie", f"Les données ont été exportées dans {file_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'exportation : {e}")


    def export_detailed_data(self):
        """Exporter les données filtrées avec un format détaillé et un nom de fichier par défaut."""
        from datetime import datetime

        # Définir un nom de fichier par défaut basé sur la date actuelle
        default_file_name = f"registre_detaillé_export_{datetime.now().strftime('%Y%m%d')}.txt"

        # Ouvrir une boîte de dialogue pour enregistrer le fichier
        file_path = filedialog.asksaveasfilename(
            initialfile=default_file_name,  # Nom par défaut
            defaultextension=".txt", 
            filetypes=[("Text files", "*.txt")]
        )

        if not file_path:
            return  # Si l'utilisateur annule l'exportation

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                # Exporter les données détaillées ligne par ligne
                for row_id in self.event_list.get_children():
                    row_data = self.event_list.item(row_id, "values")
                    # Obtenir une description détaillée
                    description = self.get_event_description(row_data[0], row_data[4])
                    f.write(
                        f"----\n"
                        f"Date: {row_data[0]}\n"
                        f"Site: {row_data[2]}\n"
                        f"Nature: {row_data[3]}\n"
                        f"Nom de l'événement: {row_data[4]}\n"
                        f"Description: {description}\n"
                        f"Temps passé: {row_data[7]} heures\n"
                        f"Terminé: {row_data[6]}\n"
                        f"----\n\n"
                    )
            messagebox.showinfo("Exportation réussie", f"Les données détaillées ont été exportées dans {file_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'exportation : {e}")


    def get_event_description(self, date, name):
        """Récupérer la description de l'événement en fonction de la date et du nom"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM events WHERE date = ? AND name = ?", (date, name))
        description = cursor.fetchone()
        conn.close()
        return description[0] if description else "Aucune description"

    def create_right_panel(self):
        """Créer les champs dans le volet droit pour ajouter/modifier un événement"""
        # Date
        ttk.Label(self.right_frame, text="Date").pack(anchor=tk.W)
        self.date_entry = DateEntry(self.right_frame, date_pattern='y-mm-dd')
        self.date_entry.pack(fill=tk.X)

        # Frame pour les boutons de sélection rapide de la date
        date_buttons_frame = ttk.Frame(self.right_frame)
        date_buttons_frame.pack(anchor=tk.W, pady=5)

        # Boutons de sélection rapide de la date
        ttk.Button(date_buttons_frame, text="Aujourd'hui", command=self.set_today).pack(side=tk.LEFT, padx=5)
        ttk.Button(date_buttons_frame, text="Demain", command=self.set_tommorow).pack(side=tk.LEFT, padx=5)
        ttk.Button(date_buttons_frame, text="Semaine Pro.", command=self.set_next_week).pack(side=tk.LEFT, padx=5)
        ttk.Button(date_buttons_frame, text="Mois Pro.", command=self.set_next_month).pack(side=tk.LEFT, padx=5)

        # Date de fin (nouvelle ligne)
        ttk.Label(self.right_frame, text="Date de Fin").pack(anchor=tk.W)
        self.end_date_entry = DateEntry(self.right_frame, date_pattern='y-mm-dd')
        self.end_date_entry.pack(fill=tk.X)

        # Boutons de sélection rapide pour Date de Fin
        end_date_buttons_frame = ttk.Frame(self.right_frame)
        end_date_buttons_frame.pack(anchor=tk.W, pady=5)
        ttk.Button(end_date_buttons_frame, text="Aujourd'hui", command=self.set_end_today).pack(side=tk.LEFT, padx=5)
        ttk.Button(end_date_buttons_frame, text="Demain", command=self.set_end_tommorow).pack(side=tk.LEFT, padx=5)
        ttk.Button(end_date_buttons_frame, text="Semaine Pro.", command=self.set_end_next_week).pack(side=tk.LEFT, padx=5)
        ttk.Button(end_date_buttons_frame, text="Mois Pro.", command=self.set_end_next_month).pack(side=tk.LEFT, padx=5)

        # Frame pour les boutons Sauvegarder, Créer Nouveau, et Supprimer l'Événement
        action_buttons_frame = ttk.Frame(self.right_frame)
        action_buttons_frame.pack(anchor=tk.W, pady=5)

        # Boutons Sauvegarder, Créer Nouveau, et Supprimer
        ttk.Button(action_buttons_frame, text="Sauvegarder", command=self.save_event).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_buttons_frame, text="Créer Nouveau", command=self.create_new_event).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_buttons_frame, text="Supprimer l'Événement", command=self.delete_event).pack(side=tk.LEFT, padx=5)

        # Site
        ttk.Label(self.right_frame, text="Site").pack(anchor=tk.W)
        self.site_var = tk.StringVar()
        self.site_combobox = ttk.Combobox(self.right_frame, textvariable=self.site_var, values=self.config["Site"])
        self.site_combobox.pack(fill=tk.X)
        self.site_combobox.bind("<Double-Button-1>", lambda e: self.site_combobox.event_generate('<Down>'))

        # Nature
        ttk.Label(self.right_frame, text="Nature").pack(anchor=tk.W)
        self.nature_var = tk.StringVar()
        self.nature_combobox = ttk.Combobox(self.right_frame, textvariable=self.nature_var, values=self.config["Nature"])
        self.nature_combobox.pack(fill=tk.X)
        self.nature_combobox.bind("<Double-Button-1>", lambda e: self.nature_combobox.event_generate('<Down>'))
        self.nature_combobox.bind("<<ComboboxSelected>>", self.update_nature_color)

        # Nom de l'événement
        ttk.Label(self.right_frame, text="Nom de l'événement").pack(anchor=tk.W)
        self.name_entry = ttk.Entry(self.right_frame)
        self.name_entry.pack(fill=tk.X)

        # Description riche
        ttk.Label(self.right_frame, text="Description").pack(anchor=tk.W)
        self.description_text = tk.Text(self.right_frame, height=20)
        self.description_text.pack(fill=tk.X)

        # Champs Terminé et Temps passé (après Description)
        ttk.Label(self.right_frame, text="Temps Passé (en heures)").pack(anchor=tk.W)
        self.time_spent_entry = ttk.Entry(self.right_frame)
        self.time_spent_entry.pack(fill=tk.X)

        self.finished_var = tk.IntVar()
        ttk.Checkbutton(self.right_frame, text="Terminé", variable=self.finished_var).pack(anchor=tk.W, pady=10)

        # Gestion des pièces jointes
        ttk.Label(self.right_frame, text="Pièces Jointes").pack(anchor=tk.W)
        self.attachment_listbox = tk.Listbox(self.right_frame, height=5)
        self.attachment_listbox.pack(fill=tk.X)
        ttk.Button(self.right_frame, text="Ajouter des Pièces Jointes", command=self.add_attachments).pack(pady=5)
        ttk.Button(self.right_frame, text="Supprimer la Pièce Jointe Sélectionnée", command=self.remove_attachment).pack(pady=5)

        # Bouton pour ouvrir les pièces jointes
        ttk.Button(self.right_frame, text="Ouvrir la Pièce Jointe", command=self.open_attachment).pack(pady=5)

    def update_nature_color(self, event=None):
        """Mettre à jour la couleur du texte en fonction de la nature sélectionnée"""
        nature = self.nature_var.get()
        if nature == "Correctif":
            self.nature_combobox.configure(foreground="red")
        elif nature == "Préventif":
            self.nature_combobox.configure(foreground="blue")
        elif nature == "Travaux":
            self.nature_combobox.configure(foreground="brown")
        else:
            self.nature_combobox.configure(foreground="black")

    def set_today(self):
        self.date_entry.set_date(datetime.now())
        
    def set_tommorow(self):
        self.date_entry.set_date(datetime.now()  + timedelta(days=1))

    def set_next_week(self):
        self.date_entry.set_date(datetime.now() + timedelta(weeks=1))

    def set_next_month(self):
        self.date_entry.set_date(datetime.now() + timedelta(days=30))

    def set_end_today(self):
        self.end_date_entry.set_date(datetime.now())
        
    def set_end_tommorow(self):
        self.end_date_entry.set_date(datetime.now() + timedelta(days=1))

    def set_end_next_week(self):
        self.end_date_entry.set_date(datetime.now() + timedelta(weeks=1))

    def set_end_next_month(self):
        self.end_date_entry.set_date(datetime.now() + timedelta(days=30))

    def add_attachments(self):
        """Ouvrir une boîte de dialogue pour sélectionner plusieurs pièces jointes"""
        filepaths = filedialog.askopenfilenames()
        for filepath in filepaths:
            if filepath:
                filename = os.path.basename(filepath)
                dest = os.path.join(ATTACHMENTS_DIR, filename)
                os.rename(filepath, dest)
                if filename not in self.attachments:  # Ne pas ajouter de doublons
                    self.attachments.append(filename)
                    self.attachment_listbox.insert(tk.END, filename)

    def remove_attachment(self):
        """Supprimer la pièce jointe sélectionnée"""
        selected_index = self.attachment_listbox.curselection()
        if selected_index:
            filename = self.attachment_listbox.get(selected_index)
            self.attachments.remove(filename)
            self.attachment_listbox.delete(selected_index)

    def open_attachment(self):
        """Ouvrir la pièce jointe de l'événement sélectionné"""
        selected_item = self.event_list.selection()
        if selected_item:
            event = self.event_list.item(selected_item, 'values')
            attachments = event[8]  # Pièce jointe est à l'indice 7
            if attachments and attachments != "None":
                for attachment in attachments.split(','):
                    filepath = os.path.join(ATTACHMENTS_DIR, attachment)
                    if os.path.exists(filepath):
                        webbrowser.open(filepath)
                    else:
                        messagebox.showerror("Erreur", f"Pièce jointe {attachment} introuvable.")
            else:
                messagebox.showerror("Erreur", "Aucune pièce jointe pour cet événement.")
        else:
            messagebox.showerror("Erreur", "Veuillez sélectionner un événement.")

    def delete_event(self):
        """Supprimer l'événement sélectionné"""
        if self.selected_event_id:
            confirm = messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer cet événement ?")
            if confirm:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM events WHERE id = ?", (self.selected_event_id,))
                conn.commit()
                conn.close()
                self.reset_form()
                self.load_events()
                messagebox.showinfo("Succès", "Événement supprimé avec succès")
        else:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un événement à supprimer")

    def save_event(self):
        """Sauvegarder un nouvel événement ou mettre à jour un événement existant"""
        date = self.date_entry.get()
        end_date = self.end_date_entry.get()
        site = self.site_var.get()
        nature = self.nature_var.get()
        name = self.name_entry.get()
        time_spent = self.time_spent_entry.get()
        description = self.description_text.get("1.0", tk.END).strip()
        attachments = ",".join(self.attachments)
        finished = self.finished_var.get()

        if not name:
            messagebox.showerror("Erreur", "Le nom de l'événement est obligatoire")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if self.selected_event_id is None:
            # Insertion d'un nouvel événement
            cursor.execute('''
                INSERT INTO events (date, end_date, site, nature, name, time_spent, description, attachments, finished)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date if date else None, end_date if end_date else None, site, nature, name, time_spent, description, attachments, finished))
        else:
            # Mise à jour de l'événement sélectionné
            cursor.execute('''
                UPDATE events
                SET date = ?, end_date = ?, site = ?, nature = ?, name = ?, time_spent = ?, description = ?, attachments = ?, finished = ?
                WHERE id = ?
            ''', (date if date else None, end_date if end_date else None, site, nature, name, time_spent, description, attachments, finished, self.selected_event_id))

        conn.commit()
        conn.close()

        self.reset_form()
        self.load_events()  # Recharge les événements
        self.apply_date_filter()  # Réapplique le filtre actif
        messagebox.showinfo("Succès", "Événement sauvegardé avec succès")

    def create_new_event(self):
        """Créer un nouvel événement à partir des données actuelles (sans modifier l'existant)"""
        self.selected_event_id = None  # On annule la sélection de l'événement actuel
        self.save_event()  # On sauvegarde les nouvelles données comme un nouvel événement

    def reset_form(self):
        """Réinitialiser les champs du formulaire après enregistrement"""
        self.date_entry.set_date(None)
        self.end_date_entry.set_date(None)
        self.site_combobox.set("")
        self.nature_combobox.set("")
        self.name_entry.delete(0, tk.END)
        self.time_spent_entry.delete(0, tk.END)
        self.description_text.delete("1.0", tk.END)
        self.attachment_listbox.delete(0, tk.END)
        self.attachments = []  
        self.finished_var.set(0)
        self.selected_event_id = None

    def load_event_details(self, event):
        """Charger les détails de l'événement sélectionné dans le volet droit"""
        selected_item = self.event_list.selection()
        if selected_item:
            # Récupérer les valeurs de l'événement sélectionné dans le Treeview
            event = self.event_list.item(selected_item, 'values')

            event_date_str = event[0].split(" - ")[0] if event[0] else None
            end_date_str = event[1].split(" - ")[0] if event[1] else None
            event_site = event[2]
            event_nature = event[3]
            event_name = event[4]
            event_description = event[5]
            event_finished = event[6]
            event_time_spent = event[7]
            event_attachments = event[8].split(",") if event[8] else []

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM events WHERE date = ? AND name = ?", (event_date_str, event_name))
            selected_event = cursor.fetchone()
            conn.close()

            if selected_event:
                self.selected_event_id = selected_event[0]

                self.date_entry.set_date(event_date_str if event_date_str else None)
                self.end_date_entry.set_date(end_date_str if end_date_str else None)
                self.site_combobox.set(event_site)
                self.nature_combobox.set(event_nature)
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, event_name)
                self.time_spent_entry.delete(0, tk.END)
                self.time_spent_entry.insert(0, event_time_spent)
                self.description_text.delete("1.0", tk.END)
                self.description_text.insert(tk.END, event_description)
                self.attachment_listbox.delete(0, tk.END)
                self.attachments = event_attachments
                for attachment in event_attachments:
                    self.attachment_listbox.insert(tk.END, attachment)
                self.finished_var.set(1 if event_finished == "Oui" else 0)

    def load_events(self):
        """Charger tous les événements depuis la base de données"""
        self.event_list.delete(*self.event_list.get_children())

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, date, end_date, site, nature, name, description, time_spent, attachments, finished FROM events ORDER BY date ASC")
        events = cursor.fetchall()

        total_time_spent = 0

        for event in events:
            finished_text = "Oui" if event[9] == 1 else "Non"
            event_date = self.format_date_with_day(event[1]) if event[1] else ""
            end_date = self.format_date_with_day(event[2]) if event[2] else ""

            row_tag = "weekend" if self.is_weekend(event[1]) else ""
            self.event_list.insert("", "end", values=(event_date, end_date, event[3], event[4], event[5], event[6], finished_text, event[7], event[8]), tags=(row_tag,))
            self.event_list.tag_configure("weekend", background="lightgrey")

            total_time_spent += float(str(event[7]).replace(',', '.')) if event[7] else 0

        #self.time_spent_sum_label.config(text=f"Total Temps Passé : {total_time_spent:.2f} heures")
        conn.close()

    def search_events(self):
        """Rechercher des événements basés sur les champs de recherche"""
        self.event_list.delete(*self.event_list.get_children())

        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT id, date, end_date, site, nature, name, description, time_spent, attachments, finished
            FROM events WHERE 1=1
        """
        params = []

        # Ajout des conditions pour chaque champ de recherche avec LOWER() pour insensibilité à la casse
        if self.search_date_var.get():
            query += " AND date LIKE ?"
            params.append(f'%{self.search_date_var.get()}%')
        if self.search_site_var.get():
            query += " AND LOWER(site) LIKE LOWER(?)"
            params.append(f'%{self.search_site_var.get()}%')
        if self.search_nature_var.get():
            query += " AND LOWER(nature) LIKE LOWER(?)"
            params.append(f'%{self.search_nature_var.get()}%')
        if self.search_name_var.get():
            query += " AND LOWER(name) LIKE LOWER(?)"
            params.append(f'%{self.search_name_var.get()}%')
        if self.search_desc_var.get():
            query += " AND LOWER(description) LIKE LOWER(?)"
            params.append(f'%{self.search_desc_var.get()}%')
        if self.search_finished_var.get().lower() in ["oui", "non"]:
            finished_value = 1 if self.search_finished_var.get().lower() == "oui" else 0
            query += " AND finished = ?"
            params.append(finished_value)

        cursor = conn.cursor()
        cursor.execute(query, params)
        events = cursor.fetchall()

        total_time_spent = 0

        for event in events:
            finished_text = "Oui" if event[9] == 1 else "Non"
            event_date = self.format_date_with_day(event[1]) if event[1] else ""
            end_date = self.format_date_with_day(event[2]) if event[2] else ""
            row_tag = "weekend" if self.is_weekend(event[1]) else ""
            self.event_list.insert("", "end", values=(event_date, end_date, event[3], event[4], event[5], event[6], finished_text, event[7], event[8]), tags=(row_tag,))
            self.event_list.tag_configure("weekend", background="lightgrey")

            try:
                total_time_spent += float(event[7])
            except ValueError:
                pass  # Ignorer les valeurs invalides pour `time_spent`

        conn.close()

    def apply_date_filter(self, event=None):
        """Appliquer le filtre de date selon le choix dans la liste déroulante"""
        filter_choice = self.filter_var.get()
        today = datetime.now()

        if filter_choice == "Aujourd'hui":
            start_date = end_date = today
        elif filter_choice == "Demain":
            start_date = end_date = today + timedelta(days=1)
        elif filter_choice == "Hier":
            start_date = end_date = today - timedelta(days=1)
        elif filter_choice == "Cette semaine":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif filter_choice == "Semaine dernière":
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = start_date + timedelta(days=6)
        elif filter_choice == "Semaine prochaine":
            start_date = today + timedelta(days=7 - today.weekday())
            end_date = start_date + timedelta(days=6)
        elif filter_choice == "Ce mois-ci":
            start_date = today.replace(day=1)
            end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        elif filter_choice == "Mois prochain":
            next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
            start_date = next_month
            end_date = (next_month + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        elif filter_choice == "Mois précédent":
            start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            end_date = today.replace(day=1) - timedelta(days=1)
        elif filter_choice == "Cette année":
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
        elif filter_choice == "Année dernière":
            start_date = today.replace(year=today.year - 1, month=1, day=1)
            end_date = today.replace(year=today.year - 1, month=12, day=31)
        elif filter_choice == "Année suivante":
            start_date = today.replace(year=today.year + 1, month=1, day=1)
            end_date = today.replace(year=today.year + 1, month=12, day=31)
            
        else:
            start_date = end_date = None
            
        self.load_filtered_events(start_date, end_date)

    def load_filtered_events(self, start_date, end_date):
        """Charger les événements en fonction du filtre de dates"""
        self.event_list.delete(*self.event_list.get_children())

        conn = sqlite3.connect(DB_PATH)
        query = "SELECT id, date, end_date, site, nature, name, description, time_spent, attachments, finished FROM events"
        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            cursor = conn.cursor()
            cursor.execute(query, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        else:
            cursor = conn.cursor()
            cursor.execute(query)
        events = cursor.fetchall()

        total_time_spent = 0

        for event in events:
            finished_text = "Oui" if event[9] == 1 else "Non"
            event_date = self.format_date_with_day(event[1]) if event[1] else ""
            end_date = self.format_date_with_day(event[2]) if event[2] else ""
            row_tag = "weekend" if self.is_weekend(event[1]) else ""
            self.event_list.insert("", "end", values=(event_date, end_date, event[3], event[4], event[5], event[6], finished_text, event[7], event[8]), tags=(row_tag,))
            self.event_list.tag_configure("weekend", background="lightgrey")

        try:
            total_time_spent += float(event[7])
        except ValueError:
        # Gérer l'erreur (par exemple, ignorer la valeur ou définir une valeur par défaut)
            pass

        #self.time_spent_sum_label.config(text=f"Total Temps Passé : {total_time_spent:.2f} heures")
        conn.close()

    def sort_column(self, col, reverse):
        """Trier les événements selon la colonne spécifiée"""
        events = [(self.event_list.set(k, col), k) for k in self.event_list.get_children('')]
        events.sort(reverse=reverse)

        for index, (val, k) in enumerate(events):
            self.event_list.move(k, '', index)

        self.event_list.heading(col, command=lambda: self.sort_column(col, not reverse))

    def format_date_with_day(self, date_str):
        """Convertir une date (format yyyy-mm-dd) en une chaîne incluant la date et le jour de la semaine"""
        if date_str:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime("%Y-%m-%d - %A")
        return ""

    def is_weekend(self, date_str):
        """Vérifier si une date est un week-end"""
        if date_str:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.weekday() >= 5
        return False


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
