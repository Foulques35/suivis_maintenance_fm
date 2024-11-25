import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from email import policy
from email.parser import BytesParser
import extract_msg
import json
import webbrowser
import tempfile
import gc
from email.utils import parsedate_to_datetime

class EmailViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lecteur de fichiers .eml et .msg")
        self.root.geometry("1000x600")

        # Chargement des paramètres (adresse email) depuis un fichier de configuration
        self.config_file = "config.json"
        self.user_email = self.load_config()

        # Interface principale
        self.search_frame = ttk.Frame(self.root)
        self.search_frame.pack(fill="x", padx=10, pady=5)

        self.tree_frame = ttk.Frame(self.root)
        self.tree_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        self.detail_frame = ttk.Frame(self.root)
        self.detail_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Barre de recherche
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var, width=50)
        self.search_entry.pack(side="left", padx=10)
        self.search_button = ttk.Button(self.search_frame, text="Rechercher", command=self.search_emails)
        self.search_button.pack(side="left")

        # Bouton pour accéder aux options
        self.options_button = ttk.Button(self.search_frame, text="Options", command=self.open_options_window)
        self.options_button.pack(side="left", padx=10)

        # Boutons pour ajouter et supprimer des emails
        self.add_button = ttk.Button(self.search_frame, text="Ajouter fichier .eml ou .msg", command=self.add_email_file)
        self.add_button.pack(side="left", pady=5)

        self.delete_button = ttk.Button(self.search_frame, text="Supprimer", command=self.delete_selected_email)
        self.delete_button.pack(side="left", padx=10)

        # Arborescence pour afficher les emails
        self.tree = ttk.Treeview(self.tree_frame, columns=("Fichier", "Type", "Date"), show="headings")
        self.tree.heading("Fichier", text="Fichiers .eml et .msg", command=lambda: self.sort_treeview("Fichier", False))
        self.tree.heading("Type", text="Reçu/Envoyé/Copie", command=lambda: self.sort_treeview("Type", False))
        self.tree.heading("Date", text="Date (AAAA-MM)", command=lambda: self.sort_treeview("Date", False))
        self.tree.bind("<<TreeviewSelect>>", self.on_email_select)
        self.tree.pack(fill="both", expand=True)

        # Champs d'affichage des détails de l'email
        self.email_subject = tk.StringVar()
        self.email_from = tk.StringVar()
        self.email_to = tk.StringVar()

        self.subject_label = ttk.Label(self.detail_frame, text="Sujet:")
        self.subject_label.pack(anchor="w")
        self.subject_value = ttk.Label(self.detail_frame, textvariable=self.email_subject)
        self.subject_value.pack(anchor="w")

        self.from_label = ttk.Label(self.detail_frame, text="De:")
        self.from_label.pack(anchor="w")
        self.from_value = ttk.Label(self.detail_frame, textvariable=self.email_from)
        self.from_value.pack(anchor="w")

        self.to_label = ttk.Label(self.detail_frame, text="À:")
        self.to_label.pack(anchor="w")
        self.to_value = ttk.Label(self.detail_frame, textvariable=self.email_to)
        self.to_value.pack(anchor="w")

        self.body_text = tk.Text(self.detail_frame, wrap="word")
        self.body_text.pack(fill="both", expand=True)

        # Pièces jointes
        self.attachments_label = ttk.Label(self.detail_frame, text="Pièces jointes:")
        self.attachments_label.pack(anchor="w")
        self.attachments_list = tk.Listbox(self.detail_frame)
        self.attachments_list.pack(fill="x")
        self.attachments_list.bind("<Double-Button-1>", self.open_attachment)

        # Stockage des emails
        self.email_folder = "emails_stockes"
        os.makedirs(self.email_folder, exist_ok=True)

        # Variable pour stocker l'ordre de tri (ascendant ou descendant)
        self.sort_order = {
            "Fichier": False,
            "Type": False,
            "Date": False
        }

        # Charger les emails existants
        self.load_emails()

    def load_config(self):
        """Charge l'adresse email de l'utilisateur depuis un fichier de configuration JSON."""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                config = json.load(file)
                return config.get("user_email", "monemail@example.com")
        else:
            return "monemail@example.com"

    def save_config(self):
        """Sauvegarde l'adresse email de l'utilisateur dans un fichier de configuration JSON."""
        config = {"user_email": self.user_email}
        with open(self.config_file, 'w') as file:
            json.dump(config, file)

    def open_options_window(self):
        """Ouvre une fenêtre pour renseigner l'adresse email."""
        options_window = tk.Toplevel(self.root)
        options_window.title("Options")
        options_window.geometry("300x150")

        email_label = ttk.Label(options_window, text="Adresse email :")
        email_label.pack(pady=10)

        email_var = tk.StringVar(value=self.user_email)
        email_entry = ttk.Entry(options_window, textvariable=email_var, width=40)
        email_entry.pack(pady=10)

        save_button = ttk.Button(options_window, text="Sauvegarder", command=lambda: self.save_email(email_var.get(), options_window))
        save_button.pack(pady=10)

    def save_email(self, email, window):
        """Sauvegarde l'adresse email et ferme la fenêtre des options."""
        self.user_email = email
        self.save_config()
        window.destroy()
        self.update_email_list()

    def update_email_list(self):
        """Met à jour la liste des emails après une modification des paramètres."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.load_emails()

    def add_email_file(self):
        """Ajoute un fichier .eml ou .msg depuis l'explorateur de fichiers et le stocke."""
        filepath = filedialog.askopenfilename(filetypes=[("Fichiers EML ou MSG", "*.eml *.msg")])
        if filepath:
            try:
                file_name = os.path.basename(filepath)
                destination = os.path.join(self.email_folder, file_name)
                if not os.path.exists(destination):
                    with open(filepath, 'rb') as src_file, open(destination, 'wb') as dest_file:
                        dest_file.write(src_file.read())
                    self.tree.insert("", "end", values=(file_name, self.get_email_type(filepath), self.get_email_date(filepath)))
                else:
                    messagebox.showwarning("Doublon", "Le fichier existe déjà.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Une erreur s'est produite : {e}")

    def load_emails(self):
        """Charge les fichiers .eml et .msg du dossier et les affiche dans le Treeview."""
        for file_name in os.listdir(self.email_folder):
            if file_name.endswith(".eml") or file_name.endswith(".msg"):
                filepath = os.path.join(self.email_folder, file_name)
                self.tree.insert("", "end", values=(file_name, self.get_email_type(filepath), self.get_email_date(filepath)))

    def delete_selected_email(self):
        """Supprime l'email sélectionné."""
        selected_item = self.tree.selection()
        if selected_item:
            file_name = self.tree.item(selected_item[0])["values"][0]
            filepath = os.path.join(self.email_folder, file_name)
            confirm = messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer {file_name} ?")
            if confirm:
                try:
                    if filepath.endswith(".msg"):
                        msg = extract_msg.Message(filepath)
                        msg.close()
                        del msg
                        gc.collect()
                    elif filepath.endswith(".eml"):
                        with open(filepath, 'rb') as f:
                            pass
                    os.remove(filepath)
                    self.tree.delete(selected_item)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de supprimer le fichier : {e}")

    def get_email_type(self, filepath):
        """Détermine si l'email est Reçu, Envoyé ou Copie."""
        if filepath.endswith(".eml"):
            with open(filepath, 'rb') as file:
                msg = BytesParser(policy=policy.default).parse(file)
                if self.user_email in (msg['from'] or ""):
                    return "Envoyé"
                elif self.user_email in (msg['to'] or ""):
                    return "Reçu"
                elif self.user_email in (msg['cc'] or ""):
                    return "Copie"
        elif filepath.endswith(".msg"):
            msg = extract_msg.Message(filepath)
            if self.user_email in msg.sender:
                return "Envoyé"
            elif self.user_email in msg.to:
                return "Reçu"
            elif self.user_email in msg.cc:
                return "Copie"
        return "Inconnu"

    def get_email_date(self, filepath):
        """Récupère la date de l'email en format 'YYYY-MM'."""
        date_str = None
        if filepath.endswith(".eml"):
            with open(filepath, 'rb') as file:
                msg = BytesParser(policy=policy.default).parse(file)
                date_str = msg['date']
        elif filepath.endswith(".msg"):
            msg = extract_msg.Message(filepath)
            date_str = msg.date

        # Afficher la date brute si nous ne pouvons pas la parser
        if date_str:
            try:
                parsed_date = parsedate_to_datetime(date_str)
                return parsed_date.strftime("%Y-%m")
            except Exception as e:
                print(f"Erreur lors de la conversion de la date '{date_str}' : {e}")
                return f"Date brute : {date_str}"  # Afficher la date brute si elle ne peut pas être convertie
        return "Inconnue"

    def on_email_select(self, event):
        """Affiche le contenu de l'email sélectionné et liste les pièces jointes."""
        selected_item = self.tree.selection()
        if selected_item:
            file_name = self.tree.item(selected_item[0])["values"][0]
            self.display_email_content(file_name)

    def display_email_content(self, file_name):
        """Lit et affiche le contenu d'un fichier .eml ou .msg."""
        filepath = os.path.join(self.email_folder, file_name)
        if file_name.endswith(".eml"):
            self.display_eml_content(filepath)
        elif file_name.endswith(".msg"):
            self.display_msg_content(filepath)

    def display_eml_content(self, filepath):
        """Affiche le contenu d'un fichier .eml et liste les pièces jointes."""
        try:
            with open(filepath, 'rb') as file:
                msg = BytesParser(policy=policy.default).parse(file)
                self.email_subject.set(msg['subject'] if msg['subject'] else "Sans sujet")
                self.email_from.set(msg['from'] if msg['from'] else "Inconnu")
                self.email_to.set(msg['to'] if msg['to'] else "Inconnu")

                body = msg.get_body(preferencelist=('plain'))
                if body:
                    self.body_text.delete(1.0, tk.END)
                    self.body_text.insert(tk.END, body.get_content())
                else:
                    self.body_text.delete(1.0, tk.END)
                    self.body_text.insert(tk.END, "[Aucun contenu disponible]")

                self.attachments_list.delete(0, tk.END)
                for part in msg.iter_attachments():
                    filename = part.get_filename()
                    if filename:
                        self.attachments_list.insert(tk.END, filename)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire le fichier : {e}")

    def display_msg_content(self, filepath):
        """Affiche le contenu d'un fichier .msg et liste les pièces jointes."""
        try:
            msg = extract_msg.Message(filepath)
            self.email_subject.set(msg.subject if msg.subject else "Sans sujet")
            self.email_from.set(msg.sender if msg.sender else "Inconnu")
            self.email_to.set(msg.to if msg.to else "Inconnu")

            body = msg.body
            if body:
                self.body_text.delete(1.0, tk.END)
                self.body_text.insert(tk.END, body)
            else:
                self.body_text.delete(1.0, tk.END)
                self.body_text.insert(tk.END, "[Aucun contenu disponible]")

            self.attachments_list.delete(0, tk.END)
            for attachment in msg.attachments:
                self.attachments_list.insert(tk.END, attachment.longFilename)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire le fichier : {e}")

    def open_attachment(self, event):
        """Ouvre la pièce jointe sélectionnée avec l'application par défaut du système."""
        selected_attachment = self.attachments_list.curselection()
        if selected_attachment:
            filename = self.attachments_list.get(selected_attachment[0])

            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, filename)

            selected_item = self.tree.selection()
            if selected_item:
                file_name = self.tree.item(selected_item[0])["values"][0]
                filepath = os.path.join(self.email_folder, file_name)

                if file_name.endswith(".eml"):
                    with open(filepath, 'rb') as file:
                        msg = BytesParser(policy=policy.default).parse(file)
                        for part in msg.iter_attachments():
                            if part.get_filename() == filename:
                                with open(temp_file_path, 'wb') as temp_file:
                                    temp_file.write(part.get_payload(decode=True))
                                webbrowser.open(temp_file_path)

                elif file_name.endswith(".msg"):
                    msg = extract_msg.Message(filepath)
                    for attachment in msg.attachments:
                        if attachment.longFilename == filename:
                            with open(temp_file_path, 'wb') as temp_file:
                                temp_file.write(attachment.data)
                            webbrowser.open(temp_file_path)

    def sort_treeview(self, col, reverse):
        """Trie les données du Treeview en fonction de la colonne cliquée."""
        data = [(self.tree.set(item, col), item) for item in self.tree.get_children("")]
        # Si la colonne est Date, on trie comme des dates, sinon comme des chaînes de caractères
        if col == "Date":
            data.sort(key=lambda t: (t[0] != "Inconnue", t[0]), reverse=reverse)
        else:
            data.sort(reverse=reverse)

        for index, (_, item) in enumerate(data):
            self.tree.move(item, '', index)

        # Inverser l'ordre de tri pour la prochaine fois que la colonne est cliquée
        self.sort_order[col] = not reverse
        self.tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))

    def search_emails(self):
        """Filtre les emails dans le Treeview selon la recherche."""
        search_term = self.search_var.get().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)

        for file_name in os.listdir(self.email_folder):
            if file_name.endswith(".eml") or file_name.endswith(".msg"):
                filepath = os.path.join(self.email_folder, file_name)
                email_type = self.get_email_type(filepath)
                email_date = self.get_email_date(filepath)

                if file_name.endswith(".eml"):
                    with open(filepath, 'rb') as file:
                        msg = BytesParser(policy=policy.default).parse(file)
                        subject = msg['subject'] or ""
                        from_email = msg['from'] or ""
                        to_email = msg['to'] or ""
                elif file_name.endswith(".msg"):
                    msg = extract_msg.Message(filepath)
                    subject = msg.subject or ""
                    from_email = msg.sender or ""
                    to_email = msg.to or ""

                if (search_term in file_name.lower() or
                    search_term in subject.lower() or
                    search_term in from_email.lower() or
                    search_term in to_email.lower() or
                    search_term in email_type.lower() or
                    search_term in email_date.lower()):
                    self.tree.insert("", "end", values=(file_name, email_type, email_date))

# Lancement de l'application
if __name__ == "__main__":
    root = tk.Tk()
    app = EmailViewerApp(root)
    root.mainloop()
