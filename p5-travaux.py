import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Chemin vers la base de données SQLite (relatif à l'emplacement du script)
DB_PATH = "p5-suivis-devis.db"
ATTACHMENTS_DIR = "attachments"

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
            ref_devis TEXT,
            compte TEXT,
            devis_accepte INTEGER,  -- Ajout de la colonne pour "Devis accepté"
            commande INTEGER,
            livraison INTEGER,
            reception INTEGER,
            achats REAL,
            vente REAL,
            notes TEXT,
            documents TEXT
        )
    ''')
    conn.commit()
    conn.close()

class CommandeApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Suivi des Devis")
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

    def create_left_panel(self):
        """Créer les champs dans le volet gauche."""
        search_frame = ttk.Frame(self.left_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        # Barre de recherche pour Ref. devis
        ttk.Label(search_frame, text="Ref. devis").pack(side=tk.LEFT, padx=5)
        self.search_annee_var = tk.StringVar()
        annee_entry = ttk.Entry(search_frame, textvariable=self.search_annee_var)
        annee_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Barre de recherche pour Compte
        ttk.Label(search_frame, text="Compte").pack(side=tk.LEFT, padx=5)
        self.search_compte_var = tk.StringVar()
        compte_entry = ttk.Entry(search_frame, textvariable=self.search_compte_var)
        compte_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(search_frame, text="Notes").pack(side=tk.LEFT, padx=5)
        self.search_notes_var = tk.StringVar()
        notes_entry = ttk.Entry(search_frame, textvariable=self.search_notes_var)
        notes_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(search_frame, text="Rechercher", command=self.search_commandes).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Exporter", command=self.export_to_text).pack(side=tk.LEFT, padx=5)

        # Création de la Treeview
        self.commandes_list = ttk.Treeview(self.left_frame, columns=(
            "id", "ref_devis", "compte", "devis_accepte", "commande", "livraison", 
            "reception", "achats", "vente", "notes", "documents"), show="headings")

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

        ttk.Label(self.right_frame, text="Ref. devis :").pack(anchor=tk.W)
        self.year_entry = ttk.Entry(self.right_frame)
        self.year_entry.pack(fill=tk.X)

        ttk.Label(self.right_frame, text="Compte :").pack(anchor=tk.W)
        self.account_entry = ttk.Entry(self.right_frame)
        self.account_entry.pack(fill=tk.X)

        self.devis_accepte_var = tk.IntVar()
        ttk.Checkbutton(self.right_frame, text="Devis accepté :", variable=self.devis_accepte_var).pack(anchor=tk.W)  # Ajout de la case à cocher "Devis accepté"
        
        self.commanded_var = tk.IntVar()
        ttk.Checkbutton(self.right_frame, text="Commande :", variable=self.commanded_var).pack(anchor=tk.W)  # Ajout de la case à cocher "Commande"

        self.delivered_var = tk.IntVar()
        ttk.Checkbutton(self.right_frame, text="Livraison :", variable=self.delivered_var).pack(anchor=tk.W)

        self.received_var = tk.IntVar()
        ttk.Checkbutton(self.right_frame, text="Réception :", variable=self.received_var).pack(anchor=tk.W)

        ttk.Label(self.right_frame, text="Achats :").pack(anchor=tk.W)
        self.material_cost_entry = ttk.Entry(self.right_frame)
        self.material_cost_entry.pack(fill=tk.X)

        ttk.Label(self.right_frame, text="Vente :").pack(anchor=tk.W)
        self.subcontracting_cost_entry = ttk.Entry(self.right_frame)
        self.subcontracting_cost_entry.pack(fill=tk.X)

        ttk.Label(self.right_frame, text="Notes :").pack(anchor=tk.W)
        self.notes_entry = ttk.Entry(self.right_frame)
        self.notes_entry.pack(fill=tk.X)

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
        """Créer les labels pour afficher les totaux et la Marge Brute et le Ratio de Marge."""
        total_frame = ttk.Frame(self.left_frame)
        total_frame.pack(fill=tk.X, padx=10, pady=10)

        self.total_material_label = ttk.Label(total_frame, text="Total Achats: 0.00")
        self.total_material_label.pack(side=tk.LEFT, padx=5)

        self.total_subcontracting_label = ttk.Label(total_frame, text="Total Vente: 0.00")
        self.total_subcontracting_label.pack(side=tk.LEFT, padx=5)

        self.total_margin_label = ttk.Label(total_frame, text="Marge Brute: 0.00")
        self.total_margin_label.pack(side=tk.LEFT, padx=5)

        self.ratio_margin_label = ttk.Label(total_frame, text="Ratio Marge: 0.00%")
        self.ratio_margin_label.pack(side=tk.LEFT, padx=5)

        self.total_count_label = ttk.Label(total_frame, text="Total Commandes: 0")
        self.total_count_label.pack(side=tk.LEFT, padx=5)

    def load_commandes(self):
        """Charger les commandes depuis la base de données."""
        self.commandes_list.delete(*self.commandes_list.get_children())
        total_material = 0.0
        total_subcontracting = 0.0

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM commandes ORDER BY ref_devis ASC")
        commandes = cursor.fetchall()

        for commande in commandes:
            self.commandes_list.insert("", "end", values=commande)  # Inclut l'ID
            if commande[3] == 1:  # Vérifier si Devis accepté est coché (1 = vrai)
                total_material += commande[7]  # Achats
                total_subcontracting += commande[8]  # Vente

        conn.close()

        # Calculer et afficher la marge brute et le ratio
        total_margin = total_subcontracting - total_material
        ratio_margin = (total_margin / total_subcontracting * 100) if total_subcontracting > 0 else 0.0
        self.update_totals(total_material, total_subcontracting, total_margin, ratio_margin, len(commandes))

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
            self.year_entry.insert(0, commande[1])  # Ref. devis
            self.account_entry.delete(0, tk.END)
            self.account_entry.insert(0, commande[2])  # Compte
            
            # Assigner les valeurs des cases à cocher
            self.devis_accepte_var.set(commande[3])  # Devis accepté
            self.commanded_var.set(commande[4])  # Commandée
            self.delivered_var.set(commande[5])  # Livraison
            self.received_var.set(commande[6])  # Réception
            
            self.material_cost_entry.delete(0, tk.END)
            self.material_cost_entry.insert(0, commande[7])  # Achats
            self.subcontracting_cost_entry.delete(0, tk.END)
            self.subcontracting_cost_entry.insert(0, commande[8])  # Vente
            self.notes_entry.delete(0, tk.END)
            self.notes_entry.insert(0, commande[9])  # Notes

            # Charger les documents
            self.documents_listbox.delete(0, tk.END)  # Vider la liste
            for doc in commande[10].split(','):
                if doc.strip():
                    self.documents_listbox.insert(tk.END, doc.strip())  # Ajouter les documents

    def search_commandes(self):
        """Rechercher des commandes basées sur l'année, le compte et les notes."""
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
            query += " AND ref_devis LIKE ?"
            params.append('%' + self.search_annee_var.get() + '%')

        if self.search_notes_var.get():
            query += " AND notes LIKE ?"
            params.append('%' + self.search_notes_var.get() + '%')

        cursor.execute(query, params)
        commandes = cursor.fetchall()

        for commande in commandes:
            if commande[3] == 1:  # Vérifier si Devis accepté est coché (1 = vrai)
                self.commandes_list.insert("", "end", values=commande)  # Inclut l'ID
                total_material += commande[7]  # Achats
                total_subcontracting += commande[8]  # Vente

        conn.close()

        # Calculer et afficher la marge brute et le ratio
        total_margin = total_subcontracting - total_material
        ratio_margin = (total_margin / total_subcontracting * 100) if total_subcontracting > 0 else 0.0
        self.update_totals(total_material, total_subcontracting, total_margin, ratio_margin, len(commandes))

    def update_totals(self, total_material, total_subcontracting, total_margin, ratio_margin, count):
        """Mettre à jour les labels pour afficher les totaux et le nombre de commandes."""
        self.total_material_label.config(text=f"Total Achats: {total_material:.2f}")
        self.total_subcontracting_label.config(text=f"Total Vente: {total_subcontracting:.2f}")
        self.total_margin_label.config(text=f"Marge Brute: {total_margin:.2f}")  # Mettre à jour la marge brute
        self.ratio_margin_label.config(text=f"Ratio Marge: {ratio_margin:.2f}%")  # Mettre à jour le ratio de marge
        self.total_count_label.config(text=f"Total Commandes: {count}")

    def export_to_text(self):
        """Exporter le contenu de la Treeview dans un fichier texte."""
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if not file_path:
            return  # Si l'utilisateur annule

        with open(file_path, 'w') as file:
            # Écrire les totaux en haut du fichier
            file.write("----\n")
            file.write("Total Achats: " + self.total_material_label.cget("text").split(": ")[1] + "\n")
            file.write("Total Vente: " + self.total_subcontracting_label.cget("text").split(": ")[1] + "\n")
            file.write("Marge Brute: " + self.total_margin_label.cget("text").split(": ")[1] + "\n")
            file.write("Ratio Marge: " + self.ratio_margin_label.cget("text").split(": ")[1] + "\n")
            file.write("Total Commandes: " + self.total_count_label.cget("text").split(": ")[1] + "\n")
            file.write("----\n\n")

            # Écrire les données de la Treeview
            for child in self.commandes_list.get_children():
                values = self.commandes_list.item(child)["values"]
                file.write(f"Ref. devis : {values[1]}\n")
                file.write(f"Compte : {values[2]}\n")
                file.write(f"Devis accepté : {values[3]}\n")  # Ajout de l'état de "Devis accepté"
                file.write(f"Commande : {values[4]}\n")
                file.write(f"Livraison : {values[5]}\n")
                file.write(f"Réception : {values[6]}\n")
                file.write(f"Achats : {values[7]}\n")
                file.write(f"Vente : {values[8]}\n")
                file.write(f"Notes : {values[9]}\n")
                file.write(f"Documents : {values[10]}\n")
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

        # Vérifier que les champs obligatoires sont remplis
        if not self.year_entry.get() or not self.account_entry.get():
            messagebox.showwarning("Avertissement", "Veuillez remplir tous les champs obligatoires.")
            return

        # Calculer les Achats et Vente
        try:
            achats = float(self.material_cost_entry.get() or 0)
            vente = float(self.subcontracting_cost_entry.get() or 0)

            data = (
                self.year_entry.get(),
                self.account_entry.get(),
                self.devis_accepte_var.get(),  # Devis accepté
                self.commanded_var.get(),  # Commandée
                self.delivered_var.get(),  # Livraison
                self.received_var.get(),  # Réception
                achats,
                vente,
                self.notes_entry.get(),
                ""  # Documents laissés vides
            )

            # Afficher les données à insérer pour le débogage
            print("Données à insérer:", data)  # Debugging line

            cursor.execute("""
                INSERT INTO commandes (ref_devis, compte, devis_accepte, commande, livraison, reception, 
                                       achats, vente, notes, documents)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", data)
            conn.commit()

            print("Commande insérée avec succès.")  # Debugging line
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'insertion des données: {e}")

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

        # Vérifier que les champs obligatoires sont remplis
        if not self.year_entry.get() or not self.account_entry.get():
            messagebox.showwarning("Avertissement", "Veuillez remplir tous les champs obligatoires.")
            return

        # Calculer les Achats et Vente
        try:
            achats = float(self.material_cost_entry.get() or 0)
            vente = float(self.subcontracting_cost_entry.get() or 0)

            documents = ",".join(self.documents_listbox.get(0, tk.END))  # Obtenir les chemins des documents

            data = (
                self.year_entry.get(),
                self.account_entry.get(),
                self.devis_accepte_var.get(),  # Devis accepté
                self.commanded_var.get(),  # Commandée
                self.delivered_var.get(),  # Livraison
                self.received_var.get(),  # Réception
                achats,
                vente,
                self.notes_entry.get(),
                documents,  # Mettre à jour la liste des documents
                commande_id  # ID de l'enregistrement à modifier
            )

            cursor.execute("""
                UPDATE commandes 
                SET ref_devis=?, compte=?, devis_accepte=?, commande=?, livraison=?, 
                    reception=?, achats=?, vente=?, notes=?, documents=? 
                WHERE id=?""", data)
            conn.commit()

            print("Commande mise à jour avec succès.")  # Debugging line
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la mise à jour des données: {e}")

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
            self.year_entry.insert(0, commande[1])  # Ref. devis
            self.account_entry.insert(0, commande[2])  # Compte
            self.devis_accepte_var.set(commande[3])  # Devis accepté
            self.commanded_var.set(commande[4])  # Commandée
            self.delivered_var.set(commande[5])  # Livraison
            self.received_var.set(commande[6])  # Réception
            self.material_cost_entry.insert(0, commande[7])  # Achats
            self.subcontracting_cost_entry.insert(0, commande[8])  # Vente
            self.notes_entry.insert(0, commande[9])  # Notes

            # Copier les documents
            self.documents_listbox.delete(0, tk.END)  # Vider la liste
            for doc in commande[10].split(','):
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
        self.year_entry.delete(0, tk.END)  # Ref. devis
        self.account_entry.delete(0, tk.END)  # Compte
        self.devis_accepte_var.set(0)  # Devis accepté
        self.commanded_var.set(0)  # Commandée
        self.delivered_var.set(0)  # Livraison
        self.received_var.set(0)  # Réception
        self.material_cost_entry.delete(0, tk.END)  # Achats
        self.subcontracting_cost_entry.delete(0, tk.END)  # Vente
        self.notes_entry.delete(0, tk.END)  # Notes
        self.documents_listbox.delete(0, tk.END)  # Vider la liste des documents

if __name__ == "__main__":
    app = CommandeApp()
    app.mainloop()
