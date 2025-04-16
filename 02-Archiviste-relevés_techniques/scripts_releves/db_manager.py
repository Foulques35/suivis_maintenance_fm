import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
from datetime import datetime
import sqlite3
import json

class DBManager:
    def __init__(self, parent, conn_audit, db_path_audit, conn_compteurs, db_path_compteurs, update_callback=None):
        self.parent = parent
        self.conn_audit = conn_audit
        self.db_path_audit = db_path_audit
        self.conn_compteurs = conn_compteurs
        self.db_path_compteurs = db_path_compteurs
        self.update_callback = update_callback

        self.backup_dir_audit = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backup_db_audit")
        self.backup_dir_compteurs = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backup_db_compteurs")
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

        # Frame principale
        self.main_frame = ttk.LabelFrame(self.parent, text="Gestion des Bases de Données")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Section pour Audit
        ttk.Label(self.main_frame, text="Base de données Audit", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        self.current_path_label_audit = ttk.Label(self.main_frame, text=f"Emplacement actuel : {os.path.dirname(self.db_path_audit)}")
        self.current_path_label_audit.pack(anchor="w", pady=2)
        ttk.Button(self.main_frame, text="Changer l'emplacement (Audit)", command=lambda: self.change_db_location("audit")).pack(pady=5)
        ttk.Button(self.main_frame, text="Sauvegarder la base Audit", command=lambda: self.manual_backup("audit")).pack(pady=5)
        ttk.Button(self.main_frame, text="Afficher les sauvegardes Audit", command=lambda: self.show_backups_window("audit")).pack(pady=5)
        self.last_backup_label_audit = ttk.Label(self.main_frame, text=self.get_last_backup_info("audit"))
        self.last_backup_label_audit.pack(pady=5)

        ttk.Separator(self.main_frame, orient="horizontal").pack(fill="x", pady=10)

        # Section pour Compteurs
        ttk.Label(self.main_frame, text="Base de données Compteurs", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        self.current_path_label_compteurs = ttk.Label(self.main_frame, text=f"Emplacement actuel : {os.path.dirname(self.db_path_compteurs)}")
        self.current_path_label_compteurs.pack(anchor="w", pady=2)
        ttk.Button(self.main_frame, text="Changer l'emplacement (Compteurs)", command=lambda: self.change_db_location("compteurs")).pack(pady=5)
        ttk.Button(self.main_frame, text="Sauvegarder la base Compteurs", command=lambda: self.manual_backup("compteurs")).pack(pady=5)
        ttk.Button(self.main_frame, text="Afficher les sauvegardes Compteurs", command=lambda: self.show_backups_window("compteurs")).pack(pady=5)
        self.last_backup_label_compteurs = ttk.Label(self.main_frame, text=self.get_last_backup_info("compteurs"))
        self.last_backup_label_compteurs.pack(pady=5)

    def change_db_location(self, section):
        """Permet à l'utilisateur de changer l'emplacement du dossier de la base de données."""
        current_dir = os.path.dirname(self.db_path_audit if section == "audit" else self.db_path_compteurs)
        new_dir = filedialog.askdirectory(
            title=f"Sélectionner un nouvel emplacement pour la base de données ({section})",
            initialdir=current_dir
        )
        if not new_dir:
            return

        # Sauvegarder le nouvel emplacement dans config.json
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
            else:
                config = {}
            config[f"db_dir_{section}"] = new_dir
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder le nouvel emplacement ({section}) : {str(e)}")
            return

        # Déterminer le chemin de la base actuelle et le nouveau chemin
        db_filename = "audit.db" if section == "audit" else "meters.db"
        new_db_path = os.path.join(new_dir, db_filename)

        # Vérifier si une base existe déjà dans le nouvel emplacement
        if os.path.exists(new_db_path):
            if not messagebox.askyesno(
                "Base de données existante",
                f"Une base de données ({db_filename}) existe déjà dans le dossier {new_dir}.\nVoulez-vous l'utiliser ? (Sinon, elle sera remplacée par la base actuelle.)"
            ):
                # Copier la base actuelle vers le nouvel emplacement
                try:
                    shutil.copy2(self.db_path_audit if section == "audit" else self.db_path_compteurs, new_db_path)
                    messagebox.showinfo("Succès", f"La base de données ({section}) a été copiée vers le nouvel emplacement.")
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de copier la base de données vers le nouvel emplacement ({section}) : {str(e)}")
                    return
        else:
            # Copier la base actuelle vers le nouvel emplacement
            try:
                shutil.copy2(self.db_path_audit if section == "audit" else self.db_path_compteurs, new_db_path)
                messagebox.showinfo("Succès", f"La base de données ({section}) a été copiée vers le nouvel emplacement.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de copier la base de données vers le nouvel emplacement ({section}) : {str(e)}")
                return

        # Mettre à jour le chemin et la connexion
        if section == "audit":
            self.conn_audit.close()
            self.db_path_audit = new_db_path
            self.conn_audit = sqlite3.connect(self.db_path_audit, check_same_thread=False)
            self.conn_audit.isolation_level = None
            self.current_path_label_audit.config(text=f"Emplacement actuel : {new_dir}")
        else:
            self.conn_compteurs.close()
            self.db_path_compteurs = new_db_path
            self.conn_compteurs = sqlite3.connect(self.db_path_compteurs, check_same_thread=False)
            self.conn_compteurs.isolation_level = None
            self.current_path_label_compteurs.config(text=f"Emplacement actuel : {new_dir}")

        # Appeler le callback pour mettre à jour les connexions dans les modules
        if self.update_callback:
            self.update_callback(self.conn_audit, self.conn_compteurs)

    def manual_backup(self, section):
        """Permet de sauvegarder manuellement la base de données à l'emplacement choisi."""
        db_path = self.db_path_audit if section == "audit" else self.db_path_compteurs
        backup_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Fichiers SQLite", "*.db"), ("Tous les fichiers", "*.*")],
            title=f"Sauvegarder la base de données ({section})",
            initialfile=f"{datetime.now().strftime('%Y-%m')}-{os.path.basename(db_path)}"
        )
        if not backup_path:
            return

        try:
            shutil.copy2(db_path, backup_path)
            messagebox.showinfo("Succès", f"La base de données ({section}) a été sauvegardée avec succès à :\n{backup_path}")
            if section == "audit":
                self.last_backup_label_audit.config(text=self.get_last_backup_info("audit"))
            else:
                self.last_backup_label_compteurs.config(text=self.get_last_backup_info("compteurs"))
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la sauvegarde ({section}) : {str(e)}")

    def get_last_backup_info(self, section):
        """Récupère la date et l'heure de la dernière sauvegarde."""
        backup_dir = self.backup_dir_audit if section == "audit" else self.backup_dir_compteurs
        db_name = "audit.db" if section == "audit" else "meters.db"
        if not os.path.exists(backup_dir):
            return f"Aucune sauvegarde trouvée pour {section}."
        
        backups = [f for f in os.listdir(backup_dir) if f.endswith(f"-{db_name}")]
        if not backups:
            return f"Aucune sauvegarde trouvée pour {section}."
        
        latest_backup = max(backups, key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)))
        mod_time = datetime.fromtimestamp(os.path.getmtime(os.path.join(backup_dir, latest_backup)))
        return f"Dernière sauvegarde ({section}) : {latest_backup} ({mod_time.strftime('%Y-%m-%d %H:%M:%S')})"

    def show_backups_window(self, section):
        """Ouvre une fenêtre listant les sauvegardes avec une option pour les importer."""
        window = tk.Toplevel(self.parent)
        window.title(f"Gestion des sauvegardes ({section})")
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
        self.load_backups(section)

        # Bouton pour importer
        import_button = ttk.Button(window, text="Importer la sauvegarde sélectionnée", command=lambda: self.import_backup(section))
        import_button.pack(pady=10)

        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def load_backups(self, section):
        """Charge la liste des sauvegardes dans le Treeview."""
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)

        backup_dir = self.backup_dir_audit if section == "audit" else self.backup_dir_compteurs
        db_name = "audit.db" if section == "audit" else "meters.db"
        if not os.path.exists(backup_dir):
            return

        backups = [f for f in os.listdir(backup_dir) if f.endswith(f"-{db_name}")]
        for backup in sorted(backups):
            backup_path = os.path.join(backup_dir, backup)
            mod_time = datetime.fromtimestamp(os.path.getmtime(backup_path)).strftime('%Y-%m-%d %H:%M:%S')
            self.backup_tree.insert("", "end", values=(backup, mod_time), tags=(backup_path,))

    def import_backup(self, section):
        """Importe la sauvegarde sélectionnée en remplaçant la base de données actuelle."""
        selected = self.backup_tree.selection()
        if not selected:
            messagebox.showwarning("Attention", f"Veuillez sélectionner une sauvegarde à importer pour {section}.")
            return

        backup_file = self.backup_tree.item(selected[0])["values"][0]
        backup_dir = self.backup_dir_audit if section == "audit" else self.backup_dir_compteurs
        backup_path = os.path.join(backup_dir, backup_file)
        db_path = self.db_path_audit if section == "audit" else self.db_path_compteurs
        conn = self.conn_audit if section == "audit" else self.conn_compteurs

        if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment importer '{backup_file}' pour {section} ?\nCela remplacera la base de données actuelle ({os.path.basename(db_path)})."):
            try:
                # Ferme temporairement la connexion pour éviter les conflits
                conn.close()
                # Remplace la base de données actuelle par la sauvegarde
                shutil.copy2(backup_path, db_path)
                # Réouvre la connexion
                conn = sqlite3.connect(db_path, check_same_thread=False)
                conn.isolation_level = None
                if section == "audit":
                    self.conn_audit = conn
                else:
                    self.conn_compteurs = conn
                messagebox.showinfo("Succès", f"La sauvegarde '{backup_file}' a été importée avec succès pour {section}.")
                if section == "audit":
                    self.last_backup_label_audit.config(text=self.get_last_backup_info("audit"))
                else:
                    self.last_backup_label_compteurs.config(text=self.get_last_backup_info("compteurs"))
                # Appeler le callback pour mettre à jour les connexions
                if self.update_callback:
                    self.update_callback(self.conn_audit, self.conn_compteurs)
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec de l'importation ({section}) : {str(e)}")
                # Tente de réouvrir la connexion en cas d'erreur
                conn = sqlite3.connect(db_path, check_same_thread=False)
                conn.isolation_level = None
                if section == "audit":
                    self.conn_audit = conn
                else:
                    self.conn_compteurs = conn