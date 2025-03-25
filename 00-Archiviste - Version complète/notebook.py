import os
import platform
from pathlib import Path
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import re
import logging
from datetime import datetime

# Configuration de la locale pour les jours en français (optionnel)
import locale
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

# Configuration de la journalisation
logging.basicConfig(filename='app.log', level=logging.DEBUG, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Chemins dynamiques
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMANDES_DB_PATH = os.path.join(BASE_DIR, "db", "commandes.db")
DEVIS_DB_PATH = os.path.join(BASE_DIR, "db", "p5-suivis-devis.db")
COMMANDES_ATTACHMENTS_DIR = "P2-Commandes"
DEVIS_ATTACHMENTS_DIR = "P5-Devis"

def create_attachments_dirs():
    """Créer les dossiers pour les pièces jointes si nécessaire."""
    for dir_path in [COMMANDES_ATTACHMENTS_DIR, DEVIS_ATTACHMENTS_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logging.info(f"Dossier des pièces jointes créé : {dir_path}")

def init_commandes_db():
    """Initialiser la base de données pour les commandes."""
    try:
        if not os.path.exists(os.path.dirname(COMMANDES_DB_PATH)):
            os.makedirs(os.path.dirname(COMMANDES_DB_PATH))
        conn = sqlite3.connect(COMMANDES_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS commandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            annee TEXT,
            compte TEXT,
            type_commande TEXT,
            commande INTEGER,
            livree INTEGER,
            receptionnee INTEGER,
            fournisseur TEXT,
            cout_materiel REAL,
            cout_soustraitance REAL,
            notes TEXT,
            numero_devis TEXT,
            numero_bdc TEXT,
            documents TEXT
        )''')
        conn.commit()
        conn.close()
        logging.info(f"Base de données commandes initialisée : {COMMANDES_DB_PATH}")
    except sqlite3.Error as e:
        logging.error(f"Erreur lors de l'initialisation de commandes.db : {e}")

def init_devis_db():
    """Initialiser la base de données pour les devis."""
    try:
        if not os.path.exists(os.path.dirname(DEVIS_DB_PATH)):
            os.makedirs(os.path.dirname(DEVIS_DB_PATH))
        conn = sqlite3.connect(DEVIS_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS commandes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ref_devis TEXT,
                compte TEXT,
                devis_accepte INTEGER,
                commande INTEGER,
                livraison INTEGER,
                reception INTEGER,
                achats REAL,
                vente REAL,
                notes TEXT,
                documents TEXT
            )''')
        conn.commit()
        conn.close()
        logging.info(f"Base de données devis initialisée : {DEVIS_DB_PATH}")
    except sqlite3.Error as e:
        logging.error(f"Erreur lors de l'initialisation de p5-suivis-devis.db : {e}")

def read_config():
    """Lire le fichier de configuration pour les types de commande."""
    types_commande = []
    CONFIG_FILE = "config-commande-p2.txt"
    if not os.path.exists(CONFIG_FILE):
        logging.error("Fichier de configuration introuvable.")
        return []
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                types_commande.append(line)
        logging.info(f"Types de commande chargés : {types_commande}")
    except Exception as e:
        logging.error(f"Erreur de lecture du fichier de configuration : {e}")
    return types_commande

class CommandeApp(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.types_commande = read_config()
        init_commandes_db()
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_frame = ttk.Frame(main_frame, width=900)
        main_frame.add(self.left_frame, weight=3)
        self.left_frame.pack_propagate(False)

        self.right_frame = ttk.Frame(main_frame, width=300)
        main_frame.add(self.right_frame, weight=1)
        self.right_frame.pack_propagate(False)

        self.search_compte_var = tk.StringVar()
        self.search_annee_var = tk.StringVar()
        self.search_fournisseur_var = tk.StringVar()
        self.search_bdc_var = tk.StringVar()
        self.search_type_var = tk.StringVar()

        self.search_compte_var.trace("w", self.search_commandes_dynamic)
        self.search_annee_var.trace("w", self.search_commandes_dynamic)
        self.search_fournisseur_var.trace("w", self.search_commandes_dynamic)
        self.search_bdc_var.trace("w", self.search_commandes_dynamic)
        self.search_type_var.trace("w", self.search_commandes_dynamic)

        self.create_left_panel()
        self.create_right_panel()
        self.create_totals_section()
        self.load_commandes()

    def create_left_panel(self):
        search_frame_1 = ttk.LabelFrame(self.left_frame, text="Filtres de recherche", padding=10)
        search_frame_1.pack(fill=tk.X, padx=10, pady=5)

        fields = [
            ("Compte", self.search_compte_var),
            ("Année", self.search_annee_var),
            ("Fournisseur", self.search_fournisseur_var),
            ("Numéro BDC", self.search_bdc_var)
        ]
        for label_text, var in fields:
            frame = ttk.Frame(search_frame_1)
            frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT, padx=2)
            ttk.Entry(frame, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        search_frame_2 = ttk.Frame(self.left_frame)
        search_frame_2.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(search_frame_2, text="Type Commande").pack(side=tk.LEFT, padx=5)
        type_entry = ttk.Combobox(search_frame_2, textvariable=self.search_type_var, values=self.types_commande)
        type_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(search_frame_2, text="Rechercher", command=self.search_commandes).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame_2, text="Exporter", command=self.export_to_text).pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.Frame(self.left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.commandes_list = ttk.Treeview(tree_frame, columns=(
            "id", "annee", "compte", "type_commande", "commande", "livree", 
            "receptionnee", "fournisseur", "cout_materiel", "cout_soustraitance", 
            "notes", "numero_devis", "numero_bdc", "documents"), show="headings")

        self.commandes_list.tag_configure('oddrow', background='#f0f0f0')
        self.commandes_list.tag_configure('evenrow', background='#ffffff')

        visible_columns = ["id", "annee", "compte", "type_commande", "commande", "livree", 
                          "receptionnee", "fournisseur", "cout_materiel", "cout_soustraitance", 
                          "notes", "numero_devis", "numero_bdc"]
        for col in visible_columns:
            self.commandes_list.heading(col, text=col.capitalize(), command=lambda c=col: self.sort_column(c, False))
            self.commandes_list.column(col, anchor=tk.W, width=120, minwidth=50, stretch=tk.YES)
        self.commandes_list.column("documents", width=0, stretch=tk.NO)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.commandes_list.yview)
        self.commandes_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.commandes_list.pack(fill=tk.BOTH, expand=True)

        self.commandes_list.bind("<<TreeviewSelect>>", self.load_selected_commande)

    def create_right_panel(self):
        button_frame = ttk.Frame(self.right_frame)
        button_frame.pack(pady=10, padx=10)

        buttons = [
            ("Créer Nouveau", self.create_new_commande),
            ("Enregistrer", self.save_commande),
            ("Copier", self.copy_commande),
            ("Supprimer", self.delete_commande)
        ]
        for text, cmd in buttons:
            ttk.Button(button_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=5)

        form_frame = ttk.LabelFrame(self.right_frame, text="Détails", padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.id_entry = ttk.Entry(form_frame, state='readonly')
        ttk.Label(form_frame, text="ID :").pack(anchor=tk.W, pady=2)
        self.id_entry.pack(fill=tk.X, pady=2)

        self.year_entry = ttk.Entry(form_frame)
        ttk.Label(form_frame, text="Année :").pack(anchor=tk.W, pady=2)
        self.year_entry.pack(fill=tk.X, pady=2)

        self.account_entry = ttk.Entry(form_frame)
        ttk.Label(form_frame, text="Compte :").pack(anchor=tk.W, pady=2)
        self.account_entry.pack(fill=tk.X, pady=2)

        ttk.Label(form_frame, text="Type Commande :").pack(anchor=tk.W, pady=2)
        self.type_combobox = ttk.Combobox(form_frame, values=self.types_commande)
        self.type_combobox.pack(fill=tk.X, pady=2)

        self.commanded_var = tk.IntVar()
        ttk.Checkbutton(form_frame, text="Commandée :", variable=self.commanded_var).pack(anchor=tk.W, pady=2)

        self.delivered_var = tk.IntVar()
        ttk.Checkbutton(form_frame, text="Livrée :", variable=self.delivered_var).pack(anchor=tk.W, pady=2)

        self.received_var = tk.IntVar()
        ttk.Checkbutton(form_frame, text="Réceptionnée :", variable=self.received_var).pack(anchor=tk.W, pady=2)

        self.supplier_entry = ttk.Entry(form_frame)
        ttk.Label(form_frame, text="Fournisseur :").pack(anchor=tk.W, pady=2)
        self.supplier_entry.pack(fill=tk.X, pady=2)

        self.material_cost_entry = ttk.Entry(form_frame)
        ttk.Label(form_frame, text="Coût Matériel :").pack(anchor=tk.W, pady=2)
        self.material_cost_entry.pack(fill=tk.X, pady=2)

        self.subcontracting_cost_entry = ttk.Entry(form_frame)
        ttk.Label(form_frame, text="Coût Sous-Traitance :").pack(anchor=tk.W, pady=2)
        self.subcontracting_cost_entry.pack(fill=tk.X, pady=2)

        self.notes_entry = ttk.Entry(form_frame)
        ttk.Label(form_frame, text="Notes :").pack(anchor=tk.W, pady=2)
        self.notes_entry.pack(fill=tk.X, pady=2)

        self.quote_number_entry = ttk.Entry(form_frame)
        ttk.Label(form_frame, text="Numéro de Devis :").pack(anchor=tk.W, pady=2)
        self.quote_number_entry.pack(fill=tk.X, pady=2)

        self.bdc_number_entry = ttk.Entry(form_frame)
        ttk.Label(form_frame, text="Numéro BDC :").pack(anchor=tk.W, pady=2)
        self.bdc_number_entry.pack(fill=tk.X, pady=2)

        doc_frame = ttk.Frame(form_frame)
        doc_frame.pack(fill=tk.X, pady=5)

        ttk.Button(doc_frame, text="Ajouter Document", command=self.add_document).pack(side=tk.LEFT, padx=5)
        ttk.Button(doc_frame, text="Ouvrir Document", command=self.open_document).pack(side=tk.LEFT, padx=5)
        ttk.Button(doc_frame, text="Supprimer Document", command=self.remove_document).pack(side=tk.LEFT, padx=5)

        ttk.Label(form_frame, text="Documents :").pack(anchor=tk.W, pady=2)
        self.documents_listbox = tk.Listbox(form_frame, height=5)
        self.documents_listbox.pack(fill=tk.X, pady=2)

        ttk.Button(self.right_frame, text="Ouvrir Archiviste", command=self.launch_archiviste).pack(pady=10)

    def create_totals_section(self):
        total_frame = ttk.LabelFrame(self.left_frame, text="Totaux", padding=10)
        total_frame.pack(fill=tk.X, padx=10, pady=5)

        self.total_material_label = ttk.Label(total_frame, text="Total Coût Matériel: 0.00")
        self.total_material_label.pack(side=tk.LEFT, padx=10)

        self.total_subcontracting_label = ttk.Label(total_frame, text="Total Coût Sous-Traitance: 0.00")
        self.total_subcontracting_label.pack(side=tk.LEFT, padx=10)

        self.total_count_label = ttk.Label(total_frame, text="Total Commandes: 0")
        self.total_count_label.pack(side=tk.LEFT, padx=10)

    def load_commandes(self):
        try:
            self.commandes_list.delete(*self.commandes_list.get_children())
            total_material = 0.0
            total_subcontracting = 0.0
            conn = sqlite3.connect(COMMANDES_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM commandes ORDER BY annee ASC")
            commandes = cursor.fetchall()
            for i, commande in enumerate(commandes):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.commandes_list.insert("", "end", values=commande, tags=(tag,))
                total_material += commande[8]
                total_subcontracting += commande[9]
            conn.close()
            self.adjust_column_widths()
            self.update_totals(total_material, total_subcontracting, len(commandes))
        except sqlite3.Error as e:
            logging.error(f"Erreur lors du chargement des commandes : {e}")
            messagebox.showerror("Erreur", f"Impossible de charger les commandes : {e}")

    def adjust_column_widths(self):
        visible_columns = ["id", "annee", "compte", "type_commande", "commande", "livree", 
                          "receptionnee", "fournisseur", "cout_materiel", "cout_soustraitance", 
                          "notes", "numero_devis", "numero_bdc"]
        for col in visible_columns:
            max_width = len(col.capitalize()) * 10
            for item in self.commandes_list.get_children():
                value = str(self.commandes_list.item(item, "values")[self.commandes_list["columns"].index(col)])
                max_width = max(max_width, len(value) * 10)
            self.commandes_list.column(col, width=max_width)

    def load_selected_commande(self, event):
        selected_item = self.commandes_list.selection()
        if selected_item:
            commande = self.commandes_list.item(selected_item, 'values')
            self.id_entry.configure(state='normal')
            self.id_entry.delete(0, tk.END)
            self.id_entry.insert(0, commande[0])
            self.id_entry.configure(state='readonly')
            self.year_entry.delete(0, tk.END)
            self.year_entry.insert(0, commande[1])
            self.account_entry.delete(0, tk.END)
            self.account_entry.insert(0, commande[2])
            self.type_combobox.set(commande[3])
            self.commanded_var.set(commande[4])
            self.delivered_var.set(commande[5])
            self.received_var.set(commande[6])
            self.supplier_entry.delete(0, tk.END)
            self.supplier_entry.insert(0, commande[7])
            self.material_cost_entry.delete(0, tk.END)
            self.material_cost_entry.insert(0, commande[8])
            self.subcontracting_cost_entry.delete(0, tk.END)
            self.subcontracting_cost_entry.insert(0, commande[9])
            self.notes_entry.delete(0, tk.END)
            self.notes_entry.insert(0, commande[10])
            self.quote_number_entry.delete(0, tk.END)
            self.quote_number_entry.insert(0, commande[11])
            self.bdc_number_entry.delete(0, tk.END)
            self.bdc_number_entry.insert(0, commande[12])
            self.documents_listbox.delete(0, tk.END)
            for doc in commande[13].split(','):
                if doc.strip():
                    self.documents_listbox.insert(tk.END, doc.strip())

    def search_commandes(self):
        self.search_commandes_dynamic()

    def search_commandes_dynamic(self, *args):
        try:
            self.commandes_list.delete(*self.commandes_list.get_children())
            total_material = 0.0
            total_subcontracting = 0.0
            conn = sqlite3.connect(COMMANDES_DB_PATH)
            cursor = conn.cursor()
            query = "SELECT * FROM commandes WHERE 1=1"
            params = []
            if self.search_compte_var.get():
                query += " AND compte LIKE ?"
                params.append('%' + self.search_compte_var.get() + '%')
            if self.search_annee_var.get():
                query += " AND annee LIKE ?"
                params.append('%' + self.search_annee_var.get() + '%')
            if self.search_fournisseur_var.get():
                query += " AND fournisseur LIKE ?"
                params.append('%' + self.search_fournisseur_var.get() + '%')
            if self.search_bdc_var.get():
                query += " AND numero_bdc LIKE ?"
                params.append('%' + self.search_bdc_var.get() + '%')
            if self.search_type_var.get():
                query += " AND type_commande LIKE ?"
                params.append('%' + self.search_type_var.get() + '%')
            cursor.execute(query, params)
            commandes = cursor.fetchall()
            for i, commande in enumerate(commandes):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.commandes_list.insert("", "end", values=commande, tags=(tag,))
                total_material += commande[8]
                total_subcontracting += commande[9]
            conn.close()
            self.adjust_column_widths()
            self.update_totals(total_material, total_subcontracting, len(commandes))
        except sqlite3.Error as e:
            logging.error(f"Erreur lors de la recherche dynamique : {e}")
            messagebox.showerror("Erreur", f"Impossible d'effectuer la recherche : {e}")

    def update_totals(self, total_material, total_subcontracting, count):
        self.total_material_label.config(text=f"Total Coût Matériel: {total_material:.2f}")
        self.total_subcontracting_label.config(text=f"Total Coût Sous-Traitance: {total_subcontracting:.2f}")
        self.total_count_label.config(text=f"Total Commandes: {count}")

    def export_to_text(self):
        default_file_name = f"commandes_export_{self.search_annee_var.get() or 'toutes_annees'}.txt"
        file_path = filedialog.asksaveasfilename(
            initialfile=default_file_name,
            defaultextension=".txt", 
            filetypes=[("Text files", "*.txt")]
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write("----\n")
                file.write(f"Total Coût Matériel: {self.total_material_label.cget('text').split(': ')[1]}\n")
                file.write(f"Total Coût Sous-Traitance: {self.total_subcontracting_label.cget('text').split(': ')[1]}\n")
                file.write(f"Total Commandes: {self.total_count_label.cget('text').split(': ')[1]}\n")
                file.write("----\n\n")
                for child in self.commandes_list.get_children():
                    values = self.commandes_list.item(child)["values"]
                    file.write(f"Année : {values[1]}\n")
                    file.write(f"Compte : {values[2]}\n")
                    file.write(f"Type Commande : {values[3]}\n")
                    file.write(f"Commandée : {values[4]}\n")
                    file.write(f"Livrée : {values[5]}\n")
                    file.write(f"Réceptionnée : {values[6]}\n")
                    file.write(f"Fournisseur : {values[7]}\n")
                    file.write(f"Coût Matériel : {values[8]}\n")
                    file.write(f"Coût Sous-Traitance : {values[9]}\n")
                    file.write(f"Notes : {values[10]}\n")
                    file.write(f"Numéro de Devis : {values[11]}\n")
                    file.write(f"Numéro BDC : {values[12]}\n")
                    file.write("----\n")
            messagebox.showinfo("Succès", f"Exportation réussie dans {file_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'exportation : {e}")

    def sort_column(self, col, reverse):
        commandes = [(self.commandes_list.set(k, col), k) for k in self.commandes_list.get_children('')]
        commandes.sort(reverse=reverse)
        for index, (val, k) in enumerate(commandes):
            self.commandes_list.move(k, '', index)
        self.commandes_list.heading(col, command=lambda: self.sort_column(col, not reverse))

    def create_new_commande(self):
        try:
            conn = sqlite3.connect(COMMANDES_DB_PATH)
            cursor = conn.cursor()
            data = (
                self.year_entry.get(),
                self.account_entry.get(),
                self.type_combobox.get(),
                self.commanded_var.get(),
                self.delivered_var.get(),
                self.received_var.get(),
                self.supplier_entry.get(),
                float(self.material_cost_entry.get() or 0),
                float(self.subcontracting_cost_entry.get() or 0),
                self.notes_entry.get(),
                self.quote_number_entry.get(),
                self.bdc_number_entry.get(),
                ""
            )
            cursor.execute("""INSERT INTO commandes (annee, compte, type_commande, commande, livree, receptionnee, fournisseur, 
                              cout_materiel, cout_soustraitance, notes, numero_devis, numero_bdc, documents)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", data)
            conn.commit()
            conn.close()
            self.load_commandes()
            self.clear_form()
            messagebox.showinfo("Succès", "Commande créée avec succès.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'insertion : {e}")

    def save_commande(self):
        selected_item = self.commandes_list.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner une commande à modifier.")
            return
        commande_id = self.commandes_list.item(selected_item[0], "values")[0]
        conn = sqlite3.connect(COMMANDES_DB_PATH)
        cursor = conn.cursor()
        documents = ",".join(self.documents_listbox.get(0, tk.END))
        data = (
            self.year_entry.get(),
            self.account_entry.get(),
            self.type_combobox.get(),
            self.commanded_var.get(),
            self.delivered_var.get(),
            self.received_var.get(),
            self.supplier_entry.get(),
            float(self.material_cost_entry.get() or 0),
            float(self.subcontracting_cost_entry.get() or 0),
            self.notes_entry.get(),
            self.quote_number_entry.get(),
            self.bdc_number_entry.get(),
            documents,
            commande_id
        )
        try:
            cursor.execute("""UPDATE commandes 
                              SET annee=?, compte=?, type_commande=?, commande=?, livree=?, receptionnee=?, fournisseur=?, 
                                  cout_materiel=?, cout_soustraitance=?, notes=?, numero_devis=?, numero_bdc=?, documents=? 
                              WHERE id=?""", data)
            conn.commit()
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'enregistrement : {e}")
        finally:
            conn.close()
        self.load_commandes()
        self.search_commandes()
        self.clear_form()

    def copy_commande(self):
        selected_item = self.commandes_list.selection()
        if selected_item:
            commande = self.commandes_list.item(selected_item, 'values')
            self.clear_form()
            self.year_entry.insert(0, commande[1])
            self.account_entry.insert(0, commande[2])
            self.type_combobox.set(commande[3])
            self.commanded_var.set(commande[4])
            self.delivered_var.set(commande[5])
            self.received_var.set(commande[6])
            self.supplier_entry.insert(0, commande[7])
            self.material_cost_entry.insert(0, commande[8])
            self.subcontracting_cost_entry.insert(0, commande[9])
            self.notes_entry.insert(0, commande[10])
            self.quote_number_entry.insert(0, commande[11])
            self.bdc_number_entry.insert(0, commande[12])
            self.documents_listbox.delete(0, tk.END)
            for doc in commande[13].split(','):
                if doc.strip():
                    self.documents_listbox.insert(tk.END, doc.strip())
            self.create_new_commande()

    def add_document(self):
        file_paths = filedialog.askopenfilenames(title="Sélectionner des documents", initialdir=os.getcwd())
        year = self.year_entry.get().strip() or "Sans_Annee"
        account = self.account_entry.get().strip() or "Sans_Compte"
        supplier = self.supplier_entry.get().strip() or "Sans_Fournisseur"
        # Nettoyer les noms pour éviter les caractères invalides dans les chemins
        year = re.sub(r'[<>:"/\\|?*]', '_', year)
        account = re.sub(r'[<>:"/\\|?*]', '_', account)
        supplier = re.sub(r'[<>:"/\\|?*]', '_', supplier)
        
        for file_path in file_paths:
            if file_path:
                file_name = os.path.basename(file_path)
                # Créer les sous-dossiers basés sur Année, Compte et Fournisseur dans P2-Commandes
                year_dir = os.path.join(COMMANDES_ATTACHMENTS_DIR, year)
                account_dir = os.path.join(year_dir, account)
                supplier_dir = os.path.join(account_dir, supplier)
                if not os.path.exists(supplier_dir):
                    os.makedirs(supplier_dir)
                destination = os.path.join(supplier_dir, file_name)
                if not os.path.exists(destination):
                    os.rename(file_path, destination)
                self.documents_listbox.insert(tk.END, destination)

    def open_document(self):
        selected_item = self.documents_listbox.curselection()
        if selected_item:
            document = self.documents_listbox.get(selected_item)
            document_path = Path(document.replace("\\", "/"))
            try:
                if platform.system() == "Windows":
                    os.startfile(document_path)
                elif platform.system() == "Linux":
                    os.system(f'xdg-open "{document_path}"')
                else:
                    messagebox.showwarning("Avertissement", "Système non pris en charge pour ouvrir des documents.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ouvrir le document : {e}")

    def remove_document(self):
        selected_item = self.documents_listbox.curselection()
        if selected_item:
            self.documents_listbox.delete(selected_item)
        else:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un document à supprimer.")

    def delete_commande(self):
        selected_item = self.commandes_list.selection()
        if selected_item:
            confirm = messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer cette commande ?")
            if confirm:
                commande_id = self.commandes_list.item(selected_item)["values"][0]
                conn = sqlite3.connect(COMMANDES_DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM commandes WHERE id=?", (commande_id,))
                conn.commit()
                conn.close()
                self.load_commandes()
                self.clear_form()

    def clear_form(self):
        self.id_entry.configure(state='normal')
        self.id_entry.delete(0, tk.END)
        self.id_entry.configure(state='readonly')
        self.year_entry.delete(0, tk.END)
        self.account_entry.delete(0, tk.END)
        self.type_combobox.set("")
        self.commanded_var.set(0)
        self.delivered_var.set(0)
        self.received_var.set(0)
        self.supplier_entry.delete(0, tk.END)
        self.material_cost_entry.delete(0, tk.END)
        self.subcontracting_cost_entry.delete(0, tk.END)
        self.notes_entry.delete(0, tk.END)
        self.quote_number_entry.delete(0, tk.END)
        self.bdc_number_entry.delete(0, tk.END)
        self.documents_listbox.delete(0, tk.END)

    def launch_archiviste(self):
        try:
            subprocess.Popen(["python", "archiviste.py"])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer Archiviste : {e}")

class DevisApp(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        init_devis_db()
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_frame = ttk.Frame(main_frame, width=900)
        main_frame.add(self.left_frame, weight=3)
        self.left_frame.pack_propagate(False)

        self.right_frame = ttk.Frame(main_frame, width=300)
        main_frame.add(self.right_frame, weight=1)
        self.right_frame.pack_propagate(False)

        self.search_annee_var = tk.StringVar()
        self.search_compte_var = tk.StringVar()
        self.search_notes_var = tk.StringVar()

        self.search_annee_var.trace("w", self.search_commandes_dynamic)
        self.search_compte_var.trace("w", self.search_commandes_dynamic)
        self.search_notes_var.trace("w", self.search_commandes_dynamic)

        self.create_left_panel()
        self.create_right_panel()
        self.create_totals_section()
        self.load_commandes()

    def create_left_panel(self):
        search_frame = ttk.LabelFrame(self.left_frame, text="Filtres de recherche", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        fields = [
            ("Ref. devis", self.search_annee_var),
            ("Compte", self.search_compte_var),
            ("Notes", self.search_notes_var)
        ]
        for label_text, var in fields:
            frame = ttk.Frame(search_frame)
            frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT, padx=2)
            ttk.Entry(frame, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(search_frame, text="Rechercher", command=self.search_commandes).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Exporter", command=self.export_to_text).pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.Frame(self.left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.commandes_list = ttk.Treeview(tree_frame, columns=(
            "id", "ref_devis", "compte", "devis_accepte", "commande", "livraison", 
            "reception", "achats", "vente", "notes", "documents"), show="headings")

        self.commandes_list.tag_configure('oddrow', background='#f0f0f0')
        self.commandes_list.tag_configure('evenrow', background='#ffffff')

        visible_columns = ["id", "ref_devis", "compte", "devis_accepte", "commande", "livraison", 
                          "reception", "achats", "vente", "notes"]
        for col in visible_columns:
            self.commandes_list.heading(col, text=col.capitalize(), command=lambda c=col: self.sort_column(c, False))
            self.commandes_list.column(col, anchor=tk.W, width=120, minwidth=50, stretch=tk.YES)
        self.commandes_list.column("documents", width=0, stretch=tk.NO)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.commandes_list.yview)
        self.commandes_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.commandes_list.pack(fill=tk.BOTH, expand=True)

        self.commandes_list.bind("<<TreeviewSelect>>", self.load_selected_commande)

    def create_right_panel(self):
        button_frame = ttk.Frame(self.right_frame)
        button_frame.pack(pady=10, padx=10)

        buttons = [
            ("Créer Nouveau", self.create_new_commande),
            ("Enregistrer", self.save_commande),
            ("Copier", self.copy_commande),
            ("Supprimer", self.delete_commande)
        ]
        for text, cmd in buttons:
            ttk.Button(button_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=5)

        form_frame = ttk.LabelFrame(self.right_frame, text="Détails", padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.id_entry = ttk.Entry(form_frame, state='readonly')
        ttk.Label(form_frame, text="ID :").pack(anchor=tk.W, pady=2)
        self.id_entry.pack(fill=tk.X, pady=2)

        self.year_entry = ttk.Entry(form_frame)
        ttk.Label(form_frame, text="Ref. devis :").pack(anchor=tk.W, pady=2)
        self.year_entry.pack(fill=tk.X, pady=2)

        self.account_entry = ttk.Entry(form_frame)
        ttk.Label(form_frame, text="Compte :").pack(anchor=tk.W, pady=2)
        self.account_entry.pack(fill=tk.X, pady=2)

        self.devis_accepte_var = tk.IntVar()
        ttk.Checkbutton(form_frame, text="Devis accepté :", variable=self.devis_accepte_var).pack(anchor=tk.W, pady=2)

        self.commanded_var = tk.IntVar()
        ttk.Checkbutton(form_frame, text="Commande :", variable=self.commanded_var).pack(anchor=tk.W, pady=2)

        self.delivered_var = tk.IntVar()
        ttk.Checkbutton(form_frame, text="Livraison :", variable=self.delivered_var).pack(anchor=tk.W, pady=2)

        self.received_var = tk.IntVar()
        ttk.Checkbutton(form_frame, text="Réception :", variable=self.received_var).pack(anchor=tk.W, pady=2)

        self.material_cost_entry = ttk.Entry(form_frame)
        ttk.Label(form_frame, text="Achats :").pack(anchor=tk.W, pady=2)
        self.material_cost_entry.pack(fill=tk.X, pady=2)

        self.subcontracting_cost_entry = ttk.Entry(form_frame)
        ttk.Label(form_frame, text="Vente :").pack(anchor=tk.W, pady=2)
        self.subcontracting_cost_entry.pack(fill=tk.X, pady=2)

        self.notes_entry = ttk.Entry(form_frame)
        ttk.Label(form_frame, text="Notes :").pack(anchor=tk.W, pady=2)
        self.notes_entry.pack(fill=tk.X, pady=2)

        doc_frame = ttk.Frame(form_frame)
        doc_frame.pack(fill=tk.X, pady=5)

        ttk.Button(doc_frame, text="Ajouter Document", command=self.add_document).pack(side=tk.LEFT, padx=5)
        ttk.Button(doc_frame, text="Ouvrir Document", command=self.open_document).pack(side=tk.LEFT, padx=5)
        ttk.Button(doc_frame, text="Supprimer Document", command=self.remove_document).pack(side=tk.LEFT, padx=5)

        ttk.Label(form_frame, text="Documents :").pack(anchor=tk.W, pady=2)
        self.documents_listbox = tk.Listbox(form_frame, height=5)
        self.documents_listbox.pack(fill=tk.X, pady=2)

        ttk.Button(self.right_frame, text="Ouvrir Archiviste", command=self.launch_archiviste).pack(pady=10)

    def create_totals_section(self):
        total_frame = ttk.LabelFrame(self.left_frame, text="Totaux", padding=10)
        total_frame.pack(fill=tk.X, padx=10, pady=5)

        self.total_material_label = ttk.Label(total_frame, text="Total Achats: 0.00")
        self.total_material_label.pack(side=tk.LEFT, padx=10)

        self.total_subcontracting_label = ttk.Label(total_frame, text="Total Vente: 0.00")
        self.total_subcontracting_label.pack(side=tk.LEFT, padx=10)

        self.total_margin_label = ttk.Label(total_frame, text="Marge Brute: 0.00")
        self.total_margin_label.pack(side=tk.LEFT, padx=10)

        self.ratio_margin_label = ttk.Label(total_frame, text="Ratio Marge: 0.00%")
        self.ratio_margin_label.pack(side=tk.LEFT, padx=10)

        self.total_count_label = ttk.Label(total_frame, text="Total Commandes: 0")
        self.total_count_label.pack(side=tk.LEFT, padx=10)

    def load_commandes(self):
        try:
            self.commandes_list.delete(*self.commandes_list.get_children())
            total_material = 0.0
            total_subcontracting = 0.0
            conn = sqlite3.connect(DEVIS_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM commandes ORDER BY ref_devis ASC")
            commandes = cursor.fetchall()
            for i, commande in enumerate(commandes):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.commandes_list.insert("", "end", values=commande, tags=(tag,))
                if commande[3] == 1:
                    total_material += commande[7]
                    total_subcontracting += commande[8]
            conn.close()
            self.adjust_column_widths()
            total_margin = total_subcontracting - total_material
            ratio_margin = (total_margin / total_subcontracting * 100) if total_subcontracting > 0 else 0.0
            self.update_totals(total_material, total_subcontracting, total_margin, ratio_margin, len(commandes))
        except sqlite3.Error as e:
            logging.error(f"Erreur lors du chargement des devis : {e}")
            messagebox.showerror("Erreur", f"Impossible de charger les devis : {e}")

    def adjust_column_widths(self):
        visible_columns = ["id", "ref_devis", "compte", "devis_accepte", "commande", "livraison", 
                          "reception", "achats", "vente", "notes"]
        for col in visible_columns:
            max_width = len(col.capitalize()) * 10
            for item in self.commandes_list.get_children():
                value = str(self.commandes_list.item(item, "values")[self.commandes_list["columns"].index(col)])
                max_width = max(max_width, len(value) * 10)
            self.commandes_list.column(col, width=max_width)

    def load_selected_commande(self, event):
        selected_item = self.commandes_list.selection()
        if selected_item:
            commande = self.commandes_list.item(selected_item, 'values')
            self.id_entry.configure(state='normal')
            self.id_entry.delete(0, tk.END)
            self.id_entry.insert(0, commande[0])
            self.id_entry.configure(state='readonly')
            self.year_entry.delete(0, tk.END)
            self.year_entry.insert(0, commande[1])
            self.account_entry.delete(0, tk.END)
            self.account_entry.insert(0, commande[2])
            self.devis_accepte_var.set(commande[3])
            self.commanded_var.set(commande[4])
            self.delivered_var.set(commande[5])
            self.received_var.set(commande[6])
            self.material_cost_entry.delete(0, tk.END)
            self.material_cost_entry.insert(0, commande[7])
            self.subcontracting_cost_entry.delete(0, tk.END)
            self.subcontracting_cost_entry.insert(0, commande[8])
            self.notes_entry.delete(0, tk.END)
            self.notes_entry.insert(0, commande[9])
            self.documents_listbox.delete(0, tk.END)
            for doc in commande[10].split(','):
                if doc.strip():
                    self.documents_listbox.insert(tk.END, doc.strip())

    def search_commandes(self):
        self.search_commandes_dynamic()

    def search_commandes_dynamic(self, *args):
        try:
            self.commandes_list.delete(*self.commandes_list.get_children())
            total_material = 0.0
            total_subcontracting = 0.0
            conn = sqlite3.connect(DEVIS_DB_PATH)
            cursor = conn.cursor()
            query = "SELECT * FROM commandes WHERE 1=1"
            params = []
            if self.search_compte_var.get():
                query += " AND compte LIKE ?"
                params.append('%' + self.search_compte_var.get() + '%')
            if self.search_annee_var.get():
                query += " AND ref_devis LIKE ?"
                params.append('%' + self.search_annee_var.get() + '%')
            if self.search_notes_var.get():
                query += " AND notes LIKE ?"
                params.append('%' + self.search_notes_var.get() + '%')
            cursor.execute(query, params)
            commandes = cursor.fetchall()
            for i, commande in enumerate(commandes):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.commandes_list.insert("", "end", values=commande, tags=(tag,))
                if commande[3] == 1:
                    total_material += commande[7]
                    total_subcontracting += commande[8]
            conn.close()
            self.adjust_column_widths()
            total_margin = total_subcontracting - total_material
            ratio_margin = (total_margin / total_subcontracting * 100) if total_subcontracting > 0 else 0.0
            self.update_totals(total_material, total_subcontracting, total_margin, ratio_margin, len(commandes))
        except sqlite3.Error as e:
            logging.error(f"Erreur lors de la recherche dynamique des devis : {e}")
            messagebox.showerror("Erreur", f"Impossible d'effectuer la recherche : {e}")

    def update_totals(self, total_material, total_subcontracting, total_margin, ratio_margin, count):
        self.total_material_label.config(text=f"Total Achats: {total_material:.2f}")
        self.total_subcontracting_label.config(text=f"Total Vente: {total_subcontracting:.2f}")
        self.total_margin_label.config(text=f"Marge Brute: {total_margin:.2f}")
        self.ratio_margin_label.config(text=f"Ratio Marge: {ratio_margin:.2f}%")
        self.total_count_label.config(text=f"Total Commandes: {count}")

    def export_to_text(self):
        default_file_name = f"devis_export_{datetime.now().strftime('%Y%m%d')}.txt"
        file_path = filedialog.asksaveasfilename(
            initialfile=default_file_name,
            defaultextension=".txt", 
            filetypes=[("Text files", "*.txt")]
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write("----\n")
                file.write(f"Total Achats: {self.total_material_label.cget('text').split(': ')[1]}\n")
                file.write(f"Total Vente: {self.total_subcontracting_label.cget('text').split(': ')[1]}\n")
                file.write(f"Marge Brute: {self.total_margin_label.cget('text').split(': ')[1]}\n")
                file.write(f"Ratio Marge: {self.ratio_margin_label.cget('text').split(': ')[1]}\n")
                file.write(f"Total Commandes: {self.total_count_label.cget('text').split(': ')[1]}\n")
                file.write("----\n\n")
                for child in self.commandes_list.get_children():
                    values = self.commandes_list.item(child)["values"]
                    file.write(f"Ref. devis : {values[1]}\n")
                    file.write(f"Compte : {values[2]}\n")
                    file.write(f"Devis accepté : {values[3]}\n")
                    file.write(f"Commande : {values[4]}\n")
                    file.write(f"Livraison : {values[5]}\n")
                    file.write(f"Réception : {values[6]}\n")
                    file.write(f"Achats : {values[7]}\n")
                    file.write(f"Vente : {values[8]}\n")
                    file.write(f"Notes : {values[9]}\n")
                    file.write("----\n")
            messagebox.showinfo("Succès", f"Exportation réussie dans {file_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'exportation : {e}")

    def sort_column(self, col, reverse):
        commandes = [(self.commandes_list.set(k, col), k) for k in self.commandes_list.get_children('')]
        commandes.sort(reverse=reverse)
        for index, (val, k) in enumerate(commandes):
            self.commandes_list.move(k, '', index)
        self.commandes_list.heading(col, command=lambda: self.sort_column(col, not reverse))

    def create_new_commande(self):
        try:
            conn = sqlite3.connect(DEVIS_DB_PATH)
            cursor = conn.cursor()
            if not self.year_entry.get() or not self.account_entry.get():
                messagebox.showwarning("Avertissement", "Veuillez remplir tous les champs obligatoires.")
                return
            achats = float(self.material_cost_entry.get() or 0)
            vente = float(self.subcontracting_cost_entry.get() or 0)
            data = (
                self.year_entry.get(),
                self.account_entry.get(),
                self.devis_accepte_var.get(),
                self.commanded_var.get(),
                self.delivered_var.get(),
                self.received_var.get(),
                achats,
                vente,
                self.notes_entry.get(),
                ""
            )
            cursor.execute(""" INSERT INTO commandes (ref_devis, compte, devis_accepte, commande, livraison, reception, 
                                       achats, vente, notes, documents)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", data)
            conn.commit()
            conn.close()
            self.load_commandes()
            self.clear_form()
            messagebox.showinfo("Succès", "Devis créé avec succès.")
        except sqlite3.Error as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'insertion des données: {e}")

    def save_commande(self):
        selected_item = self.commandes_list.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un devis à modifier.")
            return
        commande_id = self.commandes_list.item(selected_item)["values"][0]
        try:
            conn = sqlite3.connect(DEVIS_DB_PATH)
            cursor = conn.cursor()
            if not self.year_entry.get() or not self.account_entry.get():
                messagebox.showwarning("Avertissement", "Veuillez remplir tous les champs obligatoires.")
                return
            achats = float(self.material_cost_entry.get() or 0)
            vente = float(self.subcontracting_cost_entry.get() or 0)
            documents = ",".join(self.documents_listbox.get(0, tk.END))
            data = (
                self.year_entry.get(),
                self.account_entry.get(),
                self.devis_accepte_var.get(),
                self.commanded_var.get(),
                self.delivered_var.get(),
                self.received_var.get(),
                achats,
                vente,
                self.notes_entry.get(),
                documents,
                commande_id
            )
            cursor.execute(""" UPDATE commandes 
                SET ref_devis=?, compte=?, devis_accepte=?, commande=?, livraison=?, 
                    reception=?, achats=?, vente=?, notes=?, documents=? 
                WHERE id=?""", data)
            conn.commit()
            conn.close()
            self.load_commandes()
            self.search_commandes()
            self.clear_form()
        except sqlite3.Error as e:
            messagebox.showerror("Erreur", f"Erreur lors de la mise à jour des données: {e}")

    def copy_commande(self):
        selected_item = self.commandes_list.selection()
        if selected_item:
            commande = self.commandes_list.item(selected_item, 'values')
            self.clear_form()
            self.year_entry.insert(0, commande[1])
            self.account_entry.insert(0, commande[2])
            self.devis_accepte_var.set(commande[3])
            self.commanded_var.set(commande[4])
            self.delivered_var.set(commande[5])
            self.received_var.set(commande[6])
            self.material_cost_entry.insert(0, commande[7])
            self.subcontracting_cost_entry.insert(0, commande[8])
            self.notes_entry.insert(0, commande[9])
            self.documents_listbox.delete(0, tk.END)
            for doc in commande[10].split(','):
                if doc.strip():
                    self.documents_listbox.insert(tk.END, doc.strip())
            self.create_new_commande()

    def add_document(self):
        file_paths = filedialog.askopenfilenames(title="Sélectionner des documents", initialdir=os.getcwd())
        ref_devis = self.year_entry.get().strip() or "Sans_Ref_Devis"
        account = self.account_entry.get().strip() or "Sans_Compte"
        # Nettoyer le nom pour éviter les caractères invalides dans les chemins
        ref_devis = re.sub(r'[<>:"/\\|?*]', '_', ref_devis)
        account = re.sub(r'[<>:"/\\|?*]', '_', account)
        
        for file_path in file_paths:
            if file_path:
                file_name = os.path.basename(file_path)
                # Créer le sous-dossier basé sur Compte et Ref. devis dans P5-Devis
                account_dir = os.path.join(DEVIS_ATTACHMENTS_DIR, account)
                devis_dir = os.path.join(account_dir, ref_devis)
                if not os.path.exists(devis_dir):
                    os.makedirs(devis_dir)
                destination = os.path.join(devis_dir, file_name)
                if not os.path.exists(destination):
                    os.rename(file_path, destination)
                self.documents_listbox.insert(tk.END, destination)

    def open_document(self):
        selected_item = self.documents_listbox.curselection()
        if selected_item:
            document = self.documents_listbox.get(selected_item)
            document_path = Path(document.replace("\\", "/"))
            try:
                if platform.system() == "Windows":
                    os.startfile(document_path)
                elif platform.system() == "Linux":
                    os.system(f'xdg-open "{document_path}"')
                else:
                    messagebox.showwarning("Avertissement", "Système non pris en charge pour ouvrir des documents.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ouvrir le document : {e}")

    def remove_document(self):
        selected_item = self.documents_listbox.curselection()
        if selected_item:
            self.documents_listbox.delete(selected_item)
        else:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un document à supprimer.")

    def delete_commande(self):
        selected_item = self.commandes_list.selection()
        if selected_item:
            confirm = messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer ce devis ?")
            if confirm:
                commande_id = self.commandes_list.item(selected_item)["values"][0]
                try:
                    conn = sqlite3.connect(DEVIS_DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM commandes WHERE id=?", (commande_id,))
                    conn.commit()
                    conn.close()
                    self.load_commandes()
                    self.clear_form()
                except sqlite3.Error as e:
                    messagebox.showerror("Erreur", f"Impossible de supprimer le devis : {e}")

    def clear_form(self):
        self.id_entry.configure(state='normal')
        self.id_entry.delete(0, tk.END)
        self.id_entry.configure(state='readonly')
        self.year_entry.delete(0, tk.END)
        self.account_entry.delete(0, tk.END)
        self.devis_accepte_var.set(0)
        self.commanded_var.set(0)
        self.delivered_var.set(0)
        self.received_var.set(0)
        self.material_cost_entry.delete(0, tk.END)
        self.subcontracting_cost_entry.delete(0, tk.END)
        self.notes_entry.delete(0, tk.END)
        self.documents_listbox.delete(0, tk.END)

    def launch_archiviste(self):
        try:
            subprocess.Popen(["python", "archiviste.py"])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer Archiviste : {e}")

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestion Multi-Onglets")
        self.geometry("1280x800")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", font=("Helvetica", 10))
        style.configure("TButton", font=("Helvetica", 10), padding=5)
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        style.configure("Treeview", rowheight=25)

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        commandes_tab = CommandeApp(notebook)
        devis_tab = DevisApp(notebook)

        notebook.add(commandes_tab, text="Suivi des Commandes")
        notebook.add(devis_tab, text="Suivi des Devis")

if __name__ == "__main__":
    create_attachments_dirs()  # Créer les dossiers P2-Commandes et P5-Devis au démarrage
    app = MainApp()
    app.mainloop()