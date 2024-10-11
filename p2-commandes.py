import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Chemin vers la base de données SQLite (relatif à l'emplacement du script)
DB_PATH = "commandes.db"
ATTACHMENTS_DIR = "attachments"
CONFIG_FILE = "config-commande-p2.txt"

def create_attachments_dir():
    """Créer le dossier pour les pièces jointes si nécessaire."""
    if not os.path.exists(ATTACHMENTS_DIR):
        os.makedirs(ATTACHMENTS_DIR)

def init_db():
    """Initialiser la base de données et créer la table si elle n'existe pas."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commandes (
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
        )
    ''')
    conn.commit()
    conn.close()

class CommandeApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Suivi des Commandes")
        self.geometry("1280x800")

        # Initialiser la base de données
        init_db()
        create_attachments_dir()

        # Créer la frame principale
        main_frame = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=1)

        # Volet de gauche
        self.left_frame = ttk.Frame(main_frame, width=900)
        main_frame.add(self.left_frame)
        self.left_frame.pack_propagate(False)

        # Volet de droite
        self.right_frame = ttk.Frame(main_frame, width=300)
        main_frame.add(self.right_frame)
        self.right_frame.pack_propagate(False)

        # Créer les champs du volet gauche
        self.create_left_panel()

        # Créer les boutons du volet droit
        self.create_right_panel()

        # Créer les labels pour afficher les totaux
        self.create_totals_section()

        # Charger les commandes existantes
        self.load_commandes()

    def load_types_commande(self):
        """Charger les types de commande depuis le fichier de configuration."""
        if not os.path.exists(CONFIG_FILE):
            messagebox.showerror("Erreur", f"Le fichier de configuration {CONFIG_FILE} est introuvable.")
            return []

        # Ouvrir le fichier avec l'encodage utf-8
        with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip()]

    def create_left_panel(self):
        """Créer les champs dans le volet gauche."""
        search_frame = ttk.Frame(self.left_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        # Barre de recherche pour les différents champs
        ttk.Label(search_frame, text="Compte").pack(side=tk.LEFT, padx=5)
        self.search_compte_var = tk.StringVar()
        compte_entry = ttk.Entry(search_frame, textvariable=self.search_compte_var)
        compte_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(search_frame, text="Année").pack(side=tk.LEFT, padx=5)
        self.search_annee_var = tk.StringVar()
        annee_entry = ttk.Entry(search_frame, textvariable=self.search_annee_var)
        annee_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(search_frame, text="Fournisseur").pack(side=tk.LEFT, padx=5)
        self.search_fournisseur_var = tk.StringVar()
        fournisseur_entry = ttk.Entry(search_frame, textvariable=self.search_fournisseur_var)
        fournisseur_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(search_frame, text="Numéro BDC").pack(side=tk.LEFT, padx=5)
        self.search_bdc_var = tk.StringVar()
        bdc_entry = ttk.Entry(search_frame, textvariable=self.search_bdc_var)
        bdc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(search_frame, text="Type Commande").pack(side=tk.LEFT, padx=5)
        self.search_type_var = tk.StringVar()
        type_entry = ttk.Entry(search_frame, textvariable=self.search_type_var)
        type_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(search_frame, text="Rechercher", command=self.search_commandes).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Exporter", command=self.export_to_text).pack(side=tk.LEFT, padx=5)

        # Création de la Treeview
        self.commandes_list = ttk.Treeview(self.left_frame, columns=(
            "id", "annee", "compte", "type_commande", "commande", "livree", 
            "receptionnee", "fournisseur", "cout_materiel", "cout_soustraitance", 
            "notes", "numero_devis", "numero_bdc", "documents"), show="headings")

        # Configuration des colonnes avec tri et alignement
        for col in self.commandes_list["columns"]:
            self.commandes_list.heading(col, text=col.capitalize(), command=lambda c=col: self.sort_column(c, False))
            self.commandes_list.column(col, anchor=tk.W, width=120)  # Ajuster la largeur des colonnes pour un bon alignement
        
        self.commandes_list.pack(fill=tk.BOTH, expand=1)

        self.commandes_list.bind("<<TreeviewSelect>>", self.load_selected_commande)

    def create_right_panel(self):
        """Créer les champs dans le volet droit pour ajouter/modifier une commande."""
        button_frame = ttk.Frame(self.right_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Créer Nouveau", command=self.create_new_commande).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Enregistrer", command=self.save_commande).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Copier", command=self.copy_commande).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Supprimer", command=self.delete_commande).pack(side=tk.LEFT, padx=5)

        # Champ pour afficher l'ID de la commande
        ttk.Label(self.right_frame, text="ID :").pack(anchor=tk.W)
        self.id_entry = ttk.Entry(self.right_frame, state='readonly')
        self.id_entry.pack(fill=tk.X)

        ttk.Label(self.right_frame, text="Année :").pack(anchor=tk.W)
        self.year_entry = ttk.Entry(self.right_frame)
        self.year_entry.pack(fill=tk.X)

        ttk.Label(self.right_frame, text="Compte :").pack(anchor=tk.W)
        self.account_entry = ttk.Entry(self.right_frame)
        self.account_entry.pack(fill=tk.X)

        ttk.Label(self.right_frame, text="Type Commande :").pack(anchor=tk.W)
        self.type_combobox = ttk.Combobox(self.right_frame, values=self.load_types_commande())  # Charger les types de commande
        self.type_combobox.pack(fill=tk.X)

        self.commanded_var = tk.IntVar()
        ttk.Checkbutton(self.right_frame, text="Commandée :", variable=self.commanded_var).pack(anchor=tk.W)

        self.delivered_var = tk.IntVar()
        ttk.Checkbutton(self.right_frame, text="Livrée :", variable=self.delivered_var).pack(anchor=tk.W)

        self.received_var = tk.IntVar()
        ttk.Checkbutton(self.right_frame, text="Réceptionnée :", variable=self.received_var).pack(anchor=tk.W)

        ttk.Label(self.right_frame, text="Fournisseur :").pack(anchor=tk.W)
        self.supplier_entry = ttk.Entry(self.right_frame)
        self.supplier_entry.pack(fill=tk.X)

        ttk.Label(self.right_frame, text="Coût Matériel :").pack(anchor=tk.W)
        self.material_cost_entry = ttk.Entry(self.right_frame)
        self.material_cost_entry.pack(fill=tk.X)

        ttk.Label(self.right_frame, text="Coût Sous-Traitance :").pack(anchor=tk.W)
        self.subcontracting_cost_entry = ttk.Entry(self.right_frame)
        self.subcontracting_cost_entry.pack(fill=tk.X)

        ttk.Label(self.right_frame, text="Notes :").pack(anchor=tk.W)
        self.notes_entry = ttk.Entry(self.right_frame)
        self.notes_entry.pack(fill=tk.X)

        ttk.Label(self.right_frame, text="Numéro de Devis :").pack(anchor=tk.W)
        self.quote_number_entry = ttk.Entry(self.right_frame)
        self.quote_number_entry.pack(fill=tk.X)

        ttk.Label(self.right_frame, text="Numéro BDC :").pack(anchor=tk.W)
        self.bdc_number_entry = ttk.Entry(self.right_frame)
        self.bdc_number_entry.pack(fill=tk.X)

        # Ajouter un cadre pour les boutons de gestion des pièces jointes
        document_button_frame = ttk.Frame(self.right_frame)
        document_button_frame.pack(pady=5)

        # Ajouter des boutons pour gérer les pièces jointes
        ttk.Button(document_button_frame, text="Ajouter Document", command=self.add_document).pack(side=tk.LEFT, padx=5)
        ttk.Button(document_button_frame, text="Ouvrir Document", command=self.open_document).pack(side=tk.LEFT, padx=5)
        ttk.Button(document_button_frame, text="Supprimer Document", command=self.remove_document).pack(side=tk.LEFT, padx=5)

        # Liste des pièces jointes
        ttk.Label(self.right_frame, text="Documents").pack(anchor=tk.W)
        self.documents_listbox = tk.Listbox(self.right_frame)
        self.documents_listbox.pack(fill=tk.X, pady=5)

    def create_totals_section(self):
        """Créer les labels pour afficher les totaux."""
        total_frame = ttk.Frame(self.left_frame)
        total_frame.pack(fill=tk.X, padx=10, pady=10)

        self.total_material_label = ttk.Label(total_frame, text="Total Coût Matériel: 0.00")
        self.total_material_label.pack(side=tk.LEFT, padx=5)

        self.total_subcontracting_label = ttk.Label(total_frame, text="Total Coût Sous-Traitance: 0.00")
        self.total_subcontracting_label.pack(side=tk.LEFT, padx=5)

        self.total_count_label = ttk.Label(total_frame, text="Total Commandes: 0")
        self.total_count_label.pack(side=tk.LEFT, padx=5)

    def load_commandes(self):
        """Charger les commandes depuis la base de données."""
        self.commandes_list.delete(*self.commandes_list.get_children())
        total_material = 0.0
        total_subcontracting = 0.0

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM commandes ORDER BY annee ASC")
        commandes = cursor.fetchall()

        for commande in commandes:
            self.commandes_list.insert("", "end", values=commande)  # Inclut l'ID
            total_material += commande[8]  # Coût Matériel
            total_subcontracting += commande[9]  # Coût Sous-Traitance

        conn.close()

        # Mettre à jour les labels de totaux
        self.update_totals(total_material, total_subcontracting, len(commandes))

    def load_selected_commande(self, event):
        """Charger les détails de la commande sélectionnée dans le volet droit."""
        selected_item = self.commandes_list.selection()
        if selected_item:
            commande = self.commandes_list.item(selected_item, 'values')
            self.id_entry.configure(state='normal')
            self.id_entry.delete(0, tk.END)
            self.id_entry.insert(0, commande[0])  # Afficher l'ID
            self.id_entry.configure(state='readonly')  # Rendre l'ID en lecture seule
            self.year_entry.delete(0, tk.END)
            self.year_entry.insert(0, commande[1])
            self.account_entry.delete(0, tk.END)
            self.account_entry.insert(0, commande[2])
            self.type_combobox.set(commande[3])  # Remplir la combobox
            self.commanded_var.set(commande[4])  # Commandée
            self.delivered_var.set(commande[5])  # Livrée
            self.received_var.set(commande[6])  # Réceptionnée
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

            # Charger les documents
            self.documents_listbox.delete(0, tk.END)  # Vider la liste
            for doc in commande[13].split(','):
                if doc.strip():
                    self.documents_listbox.insert(tk.END, doc.strip())  # Ajouter les documents

    def search_commandes(self):
        """Rechercher des commandes basées sur l'année, le compte, le fournisseur, le numéro BDC et le type de commande."""
        self.commandes_list.delete(*self.commandes_list.get_children())
        total_material = 0.0
        total_subcontracting = 0.0

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Construire la requête en fonction des champs de recherche
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

        for commande in commandes:
            self.commandes_list.insert("", "end", values=commande)  # Inclut l'ID
            total_material += commande[8]  # Coût Matériel
            total_subcontracting += commande[9]  # Coût Sous-Traitance

        conn.close()

        # Mettre à jour les labels de totaux
        self.update_totals(total_material, total_subcontracting, len(commandes))

    def update_totals(self, total_material, total_subcontracting, count):
        """Mettre à jour les labels pour afficher les totaux et le nombre de commandes."""
        self.total_material_label.config(text=f"Total Coût Matériel: {total_material:.2f}")
        self.total_subcontracting_label.config(text=f"Total Coût Sous-Traitance: {total_subcontracting:.2f}")
        self.total_count_label.config(text=f"Total Commandes: {count}")

    def export_to_text(self):
        """Exporter le contenu de la Treeview dans un fichier texte."""
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if not file_path:
            return  # Si l'utilisateur annule

        with open(file_path, 'w') as file:
            # Écrire les totaux en haut du fichier
            file.write("----\n")
            file.write("Total Coût Matériel: " + self.total_material_label.cget("text").split(": ")[1] + "\n")
            file.write("Total Coût Sous-Traitance: " + self.total_subcontracting_label.cget("text").split(": ")[1] + "\n")
            file.write("Total Commandes: " + self.total_count_label.cget("text").split(": ")[1] + "\n")
            file.write("----\n\n")

            # Écrire les données de la Treeview
            for child in self.commandes_list.get_children():
                values = self.commandes_list.item(child)["values"]
                file.write(f"Année : {values[1]}\n")
                file.write(f"Compte : {values[2]}\n")
                file.write(f"Type_commande : {values[3]}\n")
                file.write(f"Commande : {values[4]}\n")
                file.write(f"Livree : {values[5]}\n")
                file.write(f"Receptionnee : {values[6]}\n")
                file.write(f"Fournisseur : {values[7]}\n")
                file.write(f"Cout_materiel : {values[8]}\n")
                file.write(f"Cout_sous_traitance : {values[9]}\n")
                file.write(f"Notes : {values[10]}\n")
                file.write(f"Numéro_devis : {values[11]}\n")
                file.write(f"Numero_bdc : {values[12]}\n")
                file.write("----\n")

        messagebox.showinfo("Succès", "Exportation réussie !")

    def sort_column(self, col, reverse):
        """Trier les commandes selon la colonne spécifiée."""
        # Obtenir les valeurs de la colonne
        commandes = [(self.commandes_list.set(k, col), k) for k in self.commandes_list.get_children('')]
        commandes.sort(reverse=reverse)

        for index, (val, k) in enumerate(commandes):
            self.commandes_list.move(k, '', index)

        # Inverser l'ordre du tri pour la prochaine sélection
        self.commandes_list.heading(col, command=lambda: self.sort_column(col, not reverse))

    def create_new_commande(self):
        """Créer une nouvelle commande."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        data = (
            self.year_entry.get(),
            self.account_entry.get(),
            self.type_combobox.get(),  # Obtenir le type de commande depuis la combobox
            self.commanded_var.get(),
            self.delivered_var.get(),
            self.received_var.get(),
            self.supplier_entry.get(),
            float(self.material_cost_entry.get() or 0),
            float(self.subcontracting_cost_entry.get() or 0),
            self.notes_entry.get(),
            self.quote_number_entry.get(),
            self.bdc_number_entry.get(),
            ""  # Documents laissés vides
        )

        cursor.execute("""
            INSERT INTO commandes (annee, compte, type_commande, commande, livree, receptionnee, fournisseur, 
                                   cout_materiel, cout_soustraitance, notes, numero_devis, numero_bdc, documents)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", data)
        conn.commit()
        conn.close()

        self.load_commandes()
        self.clear_form()

    def save_commande(self):
        """Modifier la commande actuelle."""
        selected_item = self.commandes_list.selection()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner une commande à modifier.")
            return

        commande_id = self.commandes_list.item(selected_item)["values"][0]  # Récupérer l'ID
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        documents = ",".join(self.documents_listbox.get(0, tk.END))  # Obtenir les chemins des documents

        data = (
            self.year_entry.get(),
            self.account_entry.get(),
            self.type_combobox.get(),  # Obtenir le type de commande depuis la combobox
            self.commanded_var.get(),
            self.delivered_var.get(),
            self.received_var.get(),
            self.supplier_entry.get(),
            float(self.material_cost_entry.get() or 0),
            float(self.subcontracting_cost_entry.get() or 0),
            self.notes_entry.get(),
            self.quote_number_entry.get(),
            self.bdc_number_entry.get(),
            documents,  # Mettre à jour la liste des documents
            commande_id  # ID de l'enregistrement à modifier
        )

        cursor.execute("""
            UPDATE commandes 
            SET annee=?, compte=?, type_commande=?, commande=?, livree=?, receptionnee=?, fournisseur=?, 
                cout_materiel=?, cout_soustraitance=?, notes=?, numero_devis=?, numero_bdc=?, documents=? 
            WHERE id=?""", data)
        conn.commit()
        conn.close()

        self.load_commandes()
        self.clear_form()

    def copy_commande(self):
        """Copier la commande sélectionnée."""
        selected_item = self.commandes_list.selection()
        if selected_item:
            commande = self.commandes_list.item(selected_item, 'values')
            # Créer un nouveau formulaire
            self.clear_form()  # Effacer le formulaire avant de remplir les champs
            self.year_entry.insert(0, commande[1])
            self.account_entry.insert(0, commande[2])
            self.type_combobox.set(commande[3])  # Remplir la combobox
            self.commanded_var.set(commande[4])  # Commandée
            self.delivered_var.set(commande[5])  # Livrée
            self.received_var.set(commande[6])  # Réceptionnée
            self.supplier_entry.insert(0, commande[7])
            self.material_cost_entry.insert(0, commande[8])
            self.subcontracting_cost_entry.insert(0, commande[9])
            self.notes_entry.insert(0, commande[10])
            self.quote_number_entry.insert(0, commande[11])
            self.bdc_number_entry.insert(0, commande[12])

            # Copier les documents
            self.documents_listbox.delete(0, tk.END)  # Vider la liste
            for doc in commande[13].split(','):
                if doc.strip():
                    self.documents_listbox.insert(tk.END, doc.strip())  # Ajouter les documents copiés

            # Enregistrer le nouvel enregistrement (dupliquer) dans la base de données
            self.create_new_commande()  # On enregistre le nouvel enregistrement

    def add_document(self):
        """Ajouter un document à la commande."""
        file_paths = filedialog.askopenfilenames(title="Sélectionner des documents", initialdir=os.getcwd())
        for file_path in file_paths:
            if file_path:
                # Déplacer le fichier dans le répertoire des pièces jointes
                file_name = os.path.basename(file_path)
                destination = os.path.join(ATTACHMENTS_DIR, file_name)
                if not os.path.exists(destination):  # Pour éviter les conflits de noms
                    os.rename(file_path, destination)
                self.documents_listbox.insert(tk.END, destination)  # Ajouter le chemin dans la liste

    def open_document(self):
        """Ouvrir le document sélectionné."""
        selected_item = self.documents_listbox.curselection()
        if selected_item:
            document = self.documents_listbox.get(selected_item)
            os.startfile(document)  # Ouvrir le chemin complet

    def remove_document(self):
        """Supprimer le document sélectionné."""
        selected_item = self.documents_listbox.curselection()
        if selected_item:
            self.documents_listbox.delete(selected_item)  # Supprimer de la liste
        else:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un document à supprimer.")

    def delete_commande(self):
        """Supprimer la commande sélectionnée."""
        selected_item = self.commandes_list.selection()
        if selected_item:
            confirm = messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer cette commande ?")
            if confirm:
                commande_id = self.commandes_list.item(selected_item)["values"][0]  # Récupérer l'ID de la commande
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM commandes WHERE id=?", (commande_id,))
                conn.commit()
                conn.close()
                self.load_commandes()
                self.clear_form()
        else:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner une commande à supprimer.")

    def clear_form(self):
        """Effacer les champs du formulaire."""
        self.id_entry.configure(state='normal')  # Permettre la modification de l'ID
        self.id_entry.delete(0, tk.END)
        self.id_entry.configure(state='readonly')  # Rendre l'ID en lecture seule
        self.year_entry.delete(0, tk.END)
        self.account_entry.delete(0, tk.END)
        self.type_combobox.set("")  # Réinitialiser la combobox
        self.commanded_var.set(0)
        self.delivered_var.set(0)
        self.received_var.set(0)
        self.supplier_entry.delete(0, tk.END)
        self.material_cost_entry.delete(0, tk.END)
        self.subcontracting_cost_entry.delete(0, tk.END)
        self.notes_entry.delete(0, tk.END)
        self.quote_number_entry.delete(0, tk.END)
        self.bdc_number_entry.delete(0, tk.END)
        self.documents_listbox.delete(0, tk.END)  # Vider la liste des documents

if __name__ == "__main__":
    app = CommandeApp()
    app.mainloop()