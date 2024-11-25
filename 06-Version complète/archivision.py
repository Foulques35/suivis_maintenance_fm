import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import os
import json
import shutil
from datetime import datetime

# Chemin du dossier où seront enregistrés les fichiers de l'application
APP_FOLDER = "app_data"
IMAGES_FOLDER = os.path.join(APP_FOLDER, "images")
LOGO_PATH = "logo.jpg"  # Chemin du logo

if not os.path.exists(APP_FOLDER):
    os.makedirs(APP_FOLDER)
if not os.path.exists(IMAGES_FOLDER):
    os.makedirs(IMAGES_FOLDER)

class Volet2(tk.Toplevel):
    def __init__(self, parent, repere_data=None, history=None, root=False):
        super().__init__(parent)
        self.title("Gestion des Images et Repères")
        self.geometry("500x600")

        self.history = history if history is not None else []
        self.root_data = repere_data if repere_data else {"Numero": 1, "Objet": "Racine", "Position": [50, 50], "Sous_reperes": [], "Image": None}
        self.current_reperes = self.root_data
        self.repere_list = self.current_reperes["Sous_reperes"]
        self.image_path = self.root_data.get("Image")  # Initialisation correcte de l'image

        # Canvas pour afficher l'image
        self.canvas = tk.Canvas(self, width=300, height=300, bg="gray")
        self.canvas.pack(pady=10)

        # Frame pour les boutons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=5)

        # Bouton pour charger une image
        load_image_button = tk.Button(button_frame, text="Charger une image", command=self.load_image)
        load_image_button.pack(side=tk.LEFT, padx=5)

        # Bouton pour sauvegarder le fichier
        save_button = tk.Button(button_frame, text="Enregistrer", command=self.save_data)
        save_button.pack(side=tk.LEFT, padx=5)

        # Bouton pour charger les données à l'ouverture
        load_button = tk.Button(button_frame, text="Charger", command=self.load_data)
        load_button.pack(side=tk.LEFT, padx=5)

        # Bouton pour exporter en PDF
        export_button = tk.Button(button_frame, text="Exporter PDF", command=self.export_pdf)
        export_button.pack(side=tk.LEFT, padx=5)

        # Navigation boutons pour sous-catégories
        back_button = tk.Button(button_frame, text="Retour", command=self.navigate_back)
        back_button.pack(side=tk.LEFT, padx=5)

        home_button = tk.Button(button_frame, text="Retour à la racine", command=self.navigate_home)
        home_button.pack(side=tk.LEFT, padx=5)

        # Initialiser le mode
        self.mode = tk.StringVar(value="Visualisation")

        # RadioButtons pour changer de mode
        mode_frame = tk.Frame(self)
        mode_frame.pack(pady=10)

        tk.Radiobutton(mode_frame, text="Visualisation", variable=self.mode, value="Visualisation").pack(side=tk.LEFT)
        tk.Radiobutton(mode_frame, text="Ajout", variable=self.mode, value="Ajout").pack(side=tk.LEFT)
        tk.Radiobutton(mode_frame, text="Édition", variable=self.mode, value="Édition").pack(side=tk.LEFT)

        # Treeview pour lister les repères
        self.repere_frame = tk.Frame(self)
        self.repere_frame.pack(fill='both', expand=True, pady=10)

        self.repere_tree = ttk.Treeview(self.repere_frame, columns=("Numéro", "Objet"), show="headings")
        self.repere_tree.heading("Numéro", text="Numéro")
        self.repere_tree.heading("Objet", text="Objet")
        self.repere_tree.pack(fill="both", expand=True)

        self.selected_repere_for_move = None
        self.repere_counter = self.get_next_repere_counter() if not root else 1

        # Lier les actions sur le treeview
        self.repere_tree.bind('<Double-1>', self.open_sub_category)

        # Afficher l'image si elle est définie
        if self.image_path:
            self.display_image()

        # Afficher les repères actuels
        self.redraw_reperes()

        # Gérer les clics sur le canvas
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def get_next_repere_counter(self):
        """Retourne le prochain numéro de repère à utiliser en fonction des repères déjà existants."""
        max_num = 0
        def find_max_num(reperes):
            nonlocal max_num
            for repere in reperes:
                max_num = max(max_num, repere["Numero"])
                find_max_num(repere["Sous_reperes"])

        find_max_num(self.root_data["Sous_reperes"])
        return max_num + 1

    def load_image(self):
        """Charger une image et l'afficher dans le canvas."""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            # Copier l'image dans le dossier app_data/images
            image_name = os.path.basename(file_path)
            dest_path = os.path.join(IMAGES_FOLDER, image_name)
            shutil.copy(file_path, dest_path)
            
            # Sauvegarder le chemin de l'image
            self.image_path = dest_path
            self.current_reperes["Image"] = dest_path
            self.display_image()

    def display_image(self):
        """Affiche l'image chargée dans le canvas."""
        img = Image.open(self.image_path)
        img = img.resize((300, 300))  # Taille du canvas de l'application
        self.img_tk = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)

    def save_data(self):
        """Enregistrer les repères dans un fichier JSON."""
        file_path = filedialog.asksaveasfilename(defaultextension=".json", initialdir=APP_FOLDER, filetypes=[("JSON Files", "*.json")])
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(self.root_data, f, indent=4)
            messagebox.showinfo("Enregistrement", "Données sauvegardées avec succès.")

    def load_data(self):
        """Charger les repères depuis un fichier JSON."""
        file_path = filedialog.askopenfilename(initialdir=APP_FOLDER, filetypes=[("JSON Files", "*.json")])
        if file_path:
            with open(file_path, 'r') as f:
                self.root_data = json.load(f)
            self.repere_list = self.root_data["Sous_reperes"]
            self.image_path = self.root_data.get("Image")
            self.history = []
            self.current_reperes = self.root_data
            self.repere_counter = self.get_next_repere_counter()
            if self.image_path:
                self.display_image()
            self.redraw_reperes()

    def redraw_reperes(self):
        """Effacer et redessiner tous les repères."""
        self.canvas.delete("all")
        if self.image_path:
            self.display_image()
        self.repere_tree.delete(*self.repere_tree.get_children())
        for repere in self.repere_list:
            self.repere_tree.insert("", "end", values=(repere["Numero"], repere["Objet"]))
            x, y = repere["Position"]
            color = "blue" if repere["Image"] else "red"
            self.canvas.create_oval(x-5, y-5, x+5, y+5, fill=color)
            self.canvas.create_text(x+10, y, text=str(repere["Numero"]), font=("Arial", 10, "bold"), fill=color, anchor=tk.W)

    def navigate_back(self):
        """Retourner à la catégorie précédente."""
        if self.history:
            self.current_reperes = self.history.pop()
            self.repere_list = self.current_reperes["Sous_reperes"]
            self.image_path = self.current_reperes["Image"]
            self.redraw_reperes()
        else:
            messagebox.showinfo("Retour", "Vous êtes déjà à la racine.")

    def navigate_home(self):
        """Retourner à la racine."""
        self.current_reperes = self.root_data
        self.repere_list = self.root_data["Sous_reperes"]
        self.history = []
        self.image_path = self.root_data["Image"]
        self.redraw_reperes()

    def open_sub_category(self, event):
        """Ouvrir la sous-catégorie associée à un repère."""
        selected_item = self.repere_tree.selection()
        if selected_item:
            item_values = self.repere_tree.item(selected_item, "values")
            for repere in self.repere_list:
                if repere["Numero"] == int(item_values[0]):
                    if repere["Image"]:
                        self.history.append(self.current_reperes)
                        self.current_reperes = repere
                        self.repere_list = repere["Sous_reperes"]
                        self.image_path = repere["Image"]
                        self.redraw_reperes()
                    else:
                        messagebox.showinfo("Sous-catégorie", "Ce repère ne contient pas de sous-catégorie.")
                    break

    def on_canvas_click(self, event):
        """Gérer les clics sur le canvas en fonction du mode."""
        if self.mode.get() == "Ajout":
            self.add_repere_to_canvas(event.x, event.y)
        elif self.mode.get() == "Édition":
            if self.selected_repere_for_move:
                self.move_repere(event.x, event.y)
            else:
                self.select_repere(event.x, event.y)

    def add_repere_to_canvas(self, x, y):
        """Ajouter un repère à l'endroit cliqué."""
        self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="red")
        self.canvas.create_text(x+10, y, text=str(self.repere_counter), font=("Arial", 10, "bold"), fill="red", anchor=tk.W)
        self.add_repere_to_list(x, y)

    def add_repere_to_list(self, x, y):
        """Ajouter un repère à la liste et dans le Treeview."""
        objet = simpledialog.askstring("Objet du Repère", "Entrez l'objet du repère :")
        self.repere_tree.insert("", "end", values=(self.repere_counter, objet if objet else "Sous-image"))
        new_repere = {"Numero": self.repere_counter, "Objet": objet, "Position": (x, y), "Sous_reperes": [], "Image": None}
        self.repere_list.append(new_repere)
        self.repere_counter += 1

    def select_repere(self, x, y):
        """Sélectionner un repère pour le déplacer ou modifier."""
        for repere in self.repere_list:
            repere_x, repere_y = repere["Position"]
            if abs(repere_x - x) < 10 and abs(repere_y - y) < 10:
                self.open_repere_editor(repere)
                break

    def open_repere_editor(self, repere):
        """Ouvrir une fenêtre pour éditer un repère."""
        edit_window = tk.Toplevel(self)
        edit_window.title(f"Éditer Repère {repere['Numero']}")
        edit_window.geometry("300x250")

        # Bouton pour déplacer le repère
        move_button = tk.Button(edit_window, text="Déplacer", command=lambda: self.start_move_repere(repere, edit_window))
        move_button.pack(pady=5)

        # Bouton pour modifier le texte de l'objet
        modify_button = tk.Button(edit_window, text="Modifier l'objet", command=lambda: self.modify_repere_text(repere, edit_window))
        modify_button.pack(pady=5)

        # Bouton pour charger une sous-image
        add_image_button = tk.Button(edit_window, text="Charger une sous-image", command=lambda: self.load_image_for_repere(repere, edit_window))
        add_image_button.pack(pady=5)

        # Bouton pour supprimer le repère
        delete_button = tk.Button(edit_window, text="Supprimer", command=lambda: self.delete_repere(repere, edit_window))
        delete_button.pack(pady=5)

    def start_move_repere(self, repere, edit_window):
        """Commencer le processus de déplacement du repère."""
        self.selected_repere_for_move = repere
        messagebox.showinfo("Déplacement", "Cliquez à l'endroit où vous souhaitez déplacer le repère.")
        edit_window.destroy()

    def move_repere(self, x, y):
        """Déplacer le repère à une nouvelle position."""
        self.selected_repere_for_move["Position"] = (x, y)
        self.selected_repere_for_move = None
        self.redraw_reperes()

    def modify_repere_text(self, repere, edit_window):
        """Modifier l'objet du repère."""
        new_objet = simpledialog.askstring("Modifier Objet", "Entrez le nouvel objet :")
        if new_objet:
            repere["Objet"] = new_objet
            self.redraw_reperes()
        edit_window.destroy()

    def load_image_for_repere(self, repere, edit_window):
        """Charger une sous-image spécifique pour un repère."""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            image_name = os.path.basename(file_path)
            dest_path = os.path.join(IMAGES_FOLDER, image_name)
            shutil.copy(file_path, dest_path)
            repere["Image"] = dest_path
        edit_window.destroy()

    def delete_repere(self, repere, edit_window):
        """Supprimer le repère sélectionné."""
        self.repere_list.remove(repere)
        self.redraw_reperes()
        edit_window.destroy()

    def export_pdf(self):
        """Exporter les repères et les images dans un fichier PDF."""
        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if output_path:
            # Demander le titre et le nom de l'utilisateur
            titre = simpledialog.askstring("Titre du PDF", "Entrez le titre du document :")
            auteur = simpledialog.askstring("Nom de l'utilisateur", "Entrez votre nom :")
            
            self.create_pdf_with_reperes(output_path, self.root_data, titre, auteur)

    def create_pdf_with_reperes(self, output_path, repere_data, titre, auteur):
        """Créer un PDF avec les images, repères, et autres informations."""
        pdf = canvas.Canvas(output_path, pagesize=A4)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")  # Date et heure actuelles

        # Dimensions de la page et de l'image
        width, height = A4
        image_width_pdf = 300  # Forcer l'image à être de 300 pixels
        image_height_pdf = 300
        image_x = (width - image_width_pdf) / 2
        image_y = height - image_height_pdf - (5 * cm)

        def draw_image_with_reperes(pdf, image_path, repere_list):
            """Fonction pour dessiner une image et les repères dessus."""
            pdf.drawImage(image_path, image_x, image_y, image_width_pdf, image_height_pdf)

            # Dessiner les repères avec la même échelle
            for repere in repere_list:
                x, y = repere["Position"]
                x_pdf = image_x + x  # On garde la même échelle
                y_pdf = image_y + (300 - y)  # Inverser l'axe Y
                color = "blue" if repere["Image"] else "red"
                pdf.setFillColor(color)
                pdf.circle(x_pdf, y_pdf, 5, fill=1)
                pdf.setFillColor("black")
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawString(x_pdf + 10, y_pdf, f"{repere['Numero']}")

            # Ajouter les informations des objets liés aux repères sous l'image
            pdf.setFont("Helvetica", 10)
            pdf.setFillColor("black")
            pdf.drawString(100, image_y - 20, "Informations des repères:")
            y_offset = image_y - 40
            for repere in repere_list:
                pdf.drawString(100, y_offset, f"Repère {repere['Numero']} : {repere['Objet']}")
                y_offset -= 15

        # Ajouter le logo, le titre, et les informations en haut de la page
        if os.path.exists(LOGO_PATH):
            pdf.drawImage(LOGO_PATH, 40, height - 80, width=100, height=50)  # Positionner le logo
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(150, height - 50, titre if titre else "Titre non défini")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(150, height - 70, f"Créé par : {auteur if auteur else 'Anonyme'}")
        pdf.drawString(150, height - 85, f"Date de création : {now}")

        # Dessiner l'image principale avec les repères sur la première page
        if self.image_path:
            draw_image_with_reperes(pdf, self.image_path, repere_data["Sous_reperes"])

        # Ajouter une nouvelle page pour chaque sous-repère (si une sous-image existe)
        for repere in repere_data["Sous_reperes"]:
            if repere["Image"]:
                pdf.showPage()  # Crée une nouvelle page
                draw_image_with_reperes(pdf, repere["Image"], repere["Sous_reperes"])

        pdf.save()

# Lancer l'application
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = Volet2(root)
    app.mainloop()
