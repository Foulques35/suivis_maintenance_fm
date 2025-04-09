import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
from datetime import datetime

class DBManager:
    def __init__(self, parent, conn, db_path):
        self.parent = parent
        self.conn = conn
        self.db_path = db_path  # Chemin de la base de données principale (meters.db)
        self.backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backup_db")

        # Frame principale
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Bouton de sauvegarde manuelle
        self.backup_button = ttk.Button(self.main_frame, text="Sauvegarder la base de données", command=self.manual_backup)
        self.backup_button.pack(pady=10)

        # Bouton pour afficher les sauvegardes
        self.show_backups_button = ttk.Button(self.main_frame, text="Afficher les sauvegardes", command=self.show_backups_window)
        self.show_backups_button.pack(pady=10)

        # Label pour la dernière sauvegarde
        self.last_backup_label = ttk.Label(self.main_frame, text=self.get_last_backup_info())
        self.last_backup_label.pack(pady=10)

    def manual_backup(self):
        """Permet de sauvegarder manuellement la base de données à l'emplacement choisi."""
        backup_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Fichiers SQLite", "*.db"), ("Tous les fichiers", "*.*")],
            title="Sauvegarder la base de données",
            initialfile=f"{datetime.now().strftime('%Y-%m')}-meters.db"
        )
        if not backup_path:
            return

        try:
            shutil.copy2(self.db_path, backup_path)
            messagebox.showinfo("Succès", f"La base de données a été sauvegardée avec succès à :\n{backup_path}")
            self.last_backup_label.config(text=self.get_last_backup_info())  # Met à jour le label
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la sauvegarde : {str(e)}")

    def get_last_backup_info(self):
        """Récupère la date et l'heure de la dernière sauvegarde dans backup_db."""
        if not os.path.exists(self.backup_dir):
            return "Aucune sauvegarde trouvée."
        
        backups = [f for f in os.listdir(self.backup_dir) if f.endswith("-meters.db")]
        if not backups:
            return "Aucune sauvegarde trouvée."
        
        latest_backup = max(backups, key=lambda f: os.path.getmtime(os.path.join(self.backup_dir, f)))
        mod_time = datetime.fromtimestamp(os.path.getmtime(os.path.join(self.backup_dir, latest_backup)))
        return f"Dernière sauvegarde : {latest_backup} ({mod_time.strftime('%Y-%m-%d %H:%M:%S')})"

    def show_backups_window(self):
        """Ouvre une fenêtre listant les sauvegardes avec une option pour les importer."""
        window = tk.Toplevel(self.parent)
        window.title("Gestion des sauvegardes")
        window.geometry("500x400")
        window.resizable(True, True)
        window.transient(self.parent)
        window.grab_set()

        # Frame pour la liste des sauvegardes
        list_frame = ttk.Frame(window)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview pour afficher les sauvegardes
        self.backup_tree = ttk.Treeview(list_frame, columns=("Nom", "Date"), show="headings")
        self.backup_tree.heading("Nom", text="Nom du fichier")
        self.backup_tree.heading("Date", text="Date de modification")
        self.backup_tree.column("Nom", width=200)
        self.backup_tree.column("Date", width=250)
        self.backup_tree.pack(fill="both", expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.backup_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.backup_tree.configure(yscrollcommand=scrollbar.set)

        # Charger les sauvegardes
        self.load_backups()

        # Bouton pour importer
        import_button = ttk.Button(window, text="Importer la sauvegarde sélectionnée", command=self.import_backup)
        import_button.pack(pady=10)

        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def load_backups(self):
        """Charge la liste des sauvegardes dans le Treeview."""
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)

        if not os.path.exists(self.backup_dir):
            return

        backups = [f for f in os.listdir(self.backup_dir) if f.endswith("-meters.db")]
        for backup in sorted(backups):
            backup_path = os.path.join(self.backup_dir, backup)
            mod_time = datetime.fromtimestamp(os.path.getmtime(backup_path)).strftime('%Y-%m-%d %H:%M:%S')
            self.backup_tree.insert("", "end", values=(backup, mod_time), tags=(backup_path,))

    def import_backup(self):
        """Importe la sauvegarde sélectionnée en remplaçant la base de données actuelle."""
        selected = self.backup_tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Veuillez sélectionner une sauvegarde à importer.")
            return

        backup_file = self.backup_tree.item(selected[0])["values"][0]
        backup_path = os.path.join(self.backup_dir, backup_file)

        if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment importer '{backup_file}' ?\nCela remplacera la base de données actuelle ({os.path.basename(self.db_path)})."):
            try:
                # Ferme temporairement la connexion pour éviter les conflits
                self.conn.close()
                # Remplace la base de données actuelle par la sauvegarde
                shutil.copy2(backup_path, self.db_path)
                # Réouvre la connexion
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self.conn.isolation_level = None
                messagebox.showinfo("Succès", f"La sauvegarde '{backup_file}' a été importée avec succès.")
                self.last_backup_label.config(text=self.get_last_backup_info())
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec de l'importation : {str(e)}")
                # Tente de réouvrir la connexion en cas d'erreur
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self.conn.isolation_level = None