import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class MeterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion Visuelle des Compteurs")
        
        # Appliquer le thème Clam
        style = ttk.Style()
        style.theme_use("clam")

        # Personnaliser le thème Clam
        style.configure("TLabel", background="#e1e1e1", foreground="#333333")  # Couleur de fond et de texte pour les labels
        style.configure("TButton", background="#4CAF50", foreground="white")  # Couleur des boutons
        style.configure("TEntry", fieldbackground="#ffffff")  # Couleur de fond des champs de saisie
        style.configure("TCombobox", fieldbackground="#ffffff")  # Couleur de fond des combobox
        style.configure("Horizontal.TPanedwindow", sashwidth=10, background="gray50")  # Barre de séparation visible

        self.conn = sqlite3.connect("meters.db")
        self.cursor = self.conn.cursor()
        self.create_initial_tables()

        # Facteur de zoom initial (1.0 = 100%)
        self.zoom_factor = 1.0

        # Frame principale avec deux volets
        self.main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill="both", expand=True)

        # Volet gauche : Canvas avec scrollbars
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.canvas_frame, weight=7)  # Poids pour 70% de l'espace

        self.canvas = tk.Canvas(self.canvas_frame, bg="white", scrollregion=(0, 0, 1000, 1000))
        h_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.config(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        # Ajout des boutons de zoom et de l'étiquette de zoom en bas du canvas
        self.zoom_frame = ttk.Frame(self.canvas_frame)
        self.zoom_frame.grid(row=2, column=0, pady=5)

        self.zoom_label = tk.Label(self.zoom_frame, text="Zoom : 100%")
        self.zoom_label.pack(side="left", padx=5)

        self.zoom_in_button = tk.Button(self.zoom_frame, text="Zoom +", command=lambda: self.zoom(1.1))
        self.zoom_in_button.pack(side="left", padx=5)

        self.zoom_out_button = tk.Button(self.zoom_frame, text="Zoom -", command=lambda: self.zoom(0.9))
        self.zoom_out_button.pack(side="left", padx=5)

        self.reset_zoom_button = tk.Button(self.zoom_frame, text="100%", command=self.reset_zoom)
        self.reset_zoom_button.pack(side="left", padx=5)

        # Volet droit : Configuration
        self.config_frame = ttk.Frame(self.main_frame, width=300)
        self.main_frame.add(self.config_frame, weight=3)  # Poids pour 30% de l'espace

        # Formulaire pour les compteurs
        meter_frame = ttk.Frame(self.config_frame)
        meter_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(meter_frame, text="Créer un Compteur", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        tk.Label(meter_frame, text="Nom du compteur:").pack(anchor="w")
        self.meter_name = tk.Entry(meter_frame)
        self.meter_name.pack(fill="x", pady=5)

        tk.Label(meter_frame, text="Catégorie:").pack(anchor="w")
        self.meter_category = ttk.Combobox(meter_frame, state="readonly")
        self.meter_category.pack(fill="x", pady=5)

        tk.Label(meter_frame, text="Note (description):").pack(anchor="w")
        self.meter_note = tk.Text(meter_frame, height=4)
        self.meter_note.pack(fill="x", pady=5)

        # Frame pour aligner les boutons
        meter_buttons_frame = ttk.Frame(meter_frame)
        meter_buttons_frame.pack(fill="x", pady=5)
        self.create_meter_button = tk.Button(meter_buttons_frame, text="Créer Compteur", command=self.add_meter)
        self.create_meter_button.pack(side="left", padx=5)
        self.edit_meter_button = tk.Button(meter_buttons_frame, text="Modifier Compteur", command=self.edit_meter, state="disabled")
        self.edit_meter_button.pack(side="left", padx=5)
        self.delete_meter_button = tk.Button(meter_buttons_frame, text="Supprimer Compteur", command=self.delete_meter, state="disabled")
        self.delete_meter_button.pack(side="left", padx=5)

        # Barre de séparation entre les sections
        ttk.Separator(self.config_frame, orient="horizontal").pack(fill="x", pady=10)

        # Formulaire pour les catégories
        cat_frame = ttk.Frame(self.config_frame)
        cat_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(cat_frame, text="Créer une Catégorie", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        tk.Label(cat_frame, text="Nom de la catégorie:").pack(anchor="w")
        self.cat_name_entry = tk.Entry(cat_frame)
        self.cat_name_entry.pack(fill="x", pady=5)

        tk.Label(cat_frame, text="Catégorie parente:").pack(anchor="w")
        self.cat_parent = ttk.Combobox(cat_frame, state="readonly")
        self.cat_parent.pack(fill="x", pady=5)

        # Frame pour aligner les boutons
        cat_buttons_frame = ttk.Frame(cat_frame)
        cat_buttons_frame.pack(fill="x", pady=5)
        self.create_cat_button = tk.Button(cat_buttons_frame, text="Créer Catégorie", command=self.add_category)
        self.create_cat_button.pack(side="left", padx=5)
        self.edit_cat_button = tk.Button(cat_buttons_frame, text="Modifier Catégorie", command=self.edit_category, state="disabled")
        self.edit_cat_button.pack(side="left", padx=5)
        self.delete_cat_button = tk.Button(cat_buttons_frame, text="Supprimer Catégorie", command=self.delete_category, state="disabled")
        self.delete_cat_button.pack(side="left", padx=5)

        # Barre de séparation entre les sections
        ttk.Separator(self.config_frame, orient="horizontal").pack(fill="x", pady=10)

        # Barre de recherche pour le Treeview
        search_frame = ttk.Frame(self.config_frame)
        search_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(search_frame, text="Rechercher (Nom/Note):").pack(side="left")
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_treeview)

        # Treeview pour lister les compteurs et catégories
        self.tree = ttk.Treeview(self.config_frame, columns=("ID", "Name", "Note"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Nom")
        self.tree.heading("Note", text="Note")
        self.tree.column("ID", width=30)
        self.tree.column("Name", width=100)
        self.tree.column("Note", width=150)
        self.tree.pack(fill="both", expand=True, pady=5)

        # Binding pour sélectionner dans le Treeview
        self.tree.bind("<<TreeviewSelect>>", self.on_treeview_select)

        # Binding pour le défilement avec la molette de la souris
        self.canvas.bind("<MouseWheel>", self.scroll_canvas)  # Windows
        self.canvas.bind("<Button-4>", self.scroll_canvas)  # Linux/macOS (défilement vers le haut)
        self.canvas.bind("<Button-5>", self.scroll_canvas)  # Linux/macOS (défilement vers le bas)

        self.update_ui()

        # Binding pour sélectionner dans le canvas
        self.canvas.bind("<ButtonPress-1>", self.select_item)

    def scroll_canvas(self, event):
        """Gère le défilement vertical avec la molette de la souris."""
        if event.num == 4:  # Défilement vers le haut (Linux/macOS)
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Défilement vers le bas (Linux/macOS)
            self.canvas.yview_scroll(1, "units")
        else:  # Windows
            # event.delta est positif pour un défilement vers le haut, négatif pour un défilement vers le bas
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def zoom(self, factor):
        """Applique un zoom ou dézoom sur le canvas."""
        # Mettre à jour le facteur de zoom
        self.zoom_factor *= factor
        # Limiter le zoom entre 10% et 500% pour éviter des valeurs extrêmes
        self.zoom_factor = max(0.1, min(self.zoom_factor, 5.0))

        # Appliquer le zoom à tous les éléments du canvas
        self.canvas.scale("all", 0, 0, factor, factor)

        # Ajuster la région de défilement après le zoom
        bbox = self.canvas.bbox("all")
        if bbox:
            x1, y1, x2, y2 = bbox
            self.canvas.configure(scrollregion=(x1, y1, x2, y2))
        else:
            self.canvas.configure(scrollregion=(0, 0, 1000 * self.zoom_factor, 1000 * self.zoom_factor))

        # Mettre à jour l'affichage du niveau de zoom
        self.zoom_label.config(text=f"Zoom : {int(self.zoom_factor * 100)}%")

    def reset_zoom(self):
        """Réinitialise le zoom à 100%."""
        # Calculer le facteur pour revenir à 100% (zoom_factor = 1.0)
        if self.zoom_factor != 1.0:
            factor = 1.0 / self.zoom_factor
            self.zoom(factor)

    def create_initial_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS meters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            note TEXT,
            category_id INTEGER,
            x_pos REAL DEFAULT 20,
            y_pos REAL DEFAULT 60,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            x_pos REAL DEFAULT 20,
            y_pos REAL DEFAULT 20,
            width REAL DEFAULT 150,
            height REAL DEFAULT 50,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )''')
        self.conn.commit()

    def get_category_hierarchy(self, cat_id, level=0):
        """Récupère la hiérarchie des catégories avec leur niveau d'imbrication."""
        if level > 5:  # Limite à 5 niveaux de sous-catégories
            return []
        categories = []
        self.cursor.execute("SELECT id, name, parent_id FROM categories WHERE id=?", (cat_id,))
        cat = self.cursor.fetchone()
        if cat:
            categories.append((cat[0], cat[1], level))
            self.cursor.execute("SELECT id FROM categories WHERE parent_id=?", (cat[0],))
            for subcat_id in self.cursor.fetchall():
                categories.extend(self.get_category_hierarchy(subcat_id[0], level + 1))
        return categories

    def update_category_combobox(self):
        """Met à jour les combobox avec la liste des catégories."""
        self.cursor.execute("SELECT id, name FROM categories")
        categories = self.cursor.fetchall()
        cat_names = ["Aucune"]
        self.cat_hierarchy = {"Aucune": None}
        for cat_id, name in categories:
            hierarchy = self.get_category_hierarchy(cat_id)
            for c_id, c_name, level in hierarchy:
                display_name = "  " * level + c_name
                cat_names.append(display_name)
                self.cat_hierarchy[display_name] = c_id
        self.meter_category["values"] = cat_names
        self.cat_parent["values"] = cat_names
        self.meter_category.set("Aucune")
        self.cat_parent.set("Aucune")

    def add_meter(self):
        name = self.meter_name.get()
        note = self.meter_note.get("1.0", tk.END).strip()
        category = self.meter_category.get()
        category_id = self.cat_hierarchy.get(category)
        if name:
            self.cursor.execute("INSERT INTO meters (name, note, category_id) VALUES (?, ?, ?)", (name, note, category_id))
            self.conn.commit()
            self.meter_name.delete(0, tk.END)
            self.meter_note.delete("1.0", tk.END)
            self.meter_category.set("Aucune")
            self.create_meter_button.config(text="Créer Compteur", command=self.add_meter)  # Réinitialiser le bouton
            self.update_ui()

    def edit_meter(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez un compteur à modifier.")
            return
        item = self.tree.item(selected[0])["values"]
        if str(item[0]).startswith("cat_"):
            messagebox.showwarning("Attention", "Sélectionnez un compteur à modifier.")
            return
        meter_id = item[0]
        self.meter_name.delete(0, tk.END)
        self.meter_name.insert(0, item[1])
        self.meter_note.delete("1.0", tk.END)
        self.meter_note.insert("1.0", item[2])
        category_name = "Aucune"
        self.cursor.execute("SELECT category_id FROM meters WHERE id=?", (meter_id,))
        category_id = self.cursor.fetchone()[0]
        if category_id:
            for display_name, c_id in self.cat_hierarchy.items():
                if c_id == category_id:
                    category_name = display_name
                    break
        self.meter_category.set(category_name)

        def save_edit():
            new_name = self.meter_name.get()
            new_note = self.meter_note.get("1.0", tk.END).strip()
            new_category = self.meter_category.get()
            new_category_id = self.cat_hierarchy.get(new_category)
            if new_name:
                self.cursor.execute("UPDATE meters SET name=?, note=?, category_id=? WHERE id=?", 
                                    (new_name, new_note, new_category_id, meter_id))
                self.conn.commit()
                self.meter_name.delete(0, tk.END)
                self.meter_note.delete("1.0", tk.END)
                self.meter_category.set("Aucune")
                self.create_meter_button.config(text="Créer Compteur", command=self.add_meter)  # Réinitialiser le bouton
                self.update_ui()

        self.create_meter_button.config(text="Sauvegarder", command=save_edit)

    def delete_meter(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez un compteur à supprimer.")
            return
        item = self.tree.item(selected[0])["values"]
        if str(item[0]).startswith("cat_"):
            messagebox.showwarning("Attention", "Sélectionnez un compteur à supprimer.")
            return
        meter_id = item[0]
        if messagebox.askyesno("Confirmation", "Supprimer ce compteur ?"):
            self.cursor.execute("DELETE FROM meters WHERE id=?", (meter_id,))
            self.conn.commit()
            self.update_ui()

    def add_category(self):
        name = self.cat_name_entry.get()
        parent = self.cat_parent.get()
        parent_id = self.cat_hierarchy.get(parent)
        if name:
            # Vérifier si une catégorie avec ce nom existe déjà
            self.cursor.execute("SELECT id FROM categories WHERE name=?", (name,))
            if self.cursor.fetchone():
                messagebox.showwarning("Attention", "Une catégorie avec ce nom existe déjà.")
                return
            # Vérifier le niveau d'imbrication
            level = 0
            current_parent = parent_id
            while current_parent:
                self.cursor.execute("SELECT parent_id FROM categories WHERE id=?", (current_parent,))
                current_parent = self.cursor.fetchone()[0]
                level += 1
            if level >= 5:
                messagebox.showwarning("Attention", "Limite de 5 niveaux de sous-catégories atteinte.")
                return
            self.cursor.execute("INSERT INTO categories (name, parent_id) VALUES (?, ?)", (name, parent_id))
            self.conn.commit()
            self.cat_name_entry.delete(0, tk.END)
            self.cat_parent.set("Aucune")
            self.create_cat_button.config(text="Créer Catégorie", command=self.add_category)  # Réinitialiser le bouton
            self.update_ui()

    def edit_category(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez une catégorie à modifier.")
            return
        item = self.tree.item(selected[0])["values"]
        if not str(item[0]).startswith("cat_"):
            messagebox.showwarning("Attention", "Sélectionnez une catégorie à modifier.")
            return
        cat_id = int(item[0].split("_")[1])
        self.cursor.execute("SELECT name, parent_id FROM categories WHERE id=?", (cat_id,))
        cat_name, parent_id = self.cursor.fetchone()
        self.cat_name_entry.delete(0, tk.END)
        self.cat_name_entry.insert(0, cat_name)
        parent_name = "Aucune"
        if parent_id:
            for display_name, c_id in self.cat_hierarchy.items():
                if c_id == parent_id:
                    parent_name = display_name
                    break
        self.cat_parent.set(parent_name)

        def save_edit():
            new_name = self.cat_name_entry.get()
            new_parent = self.cat_parent.get()
            new_parent_id = self.cat_hierarchy.get(new_parent)
            if new_name:
                # Vérifier si une autre catégorie avec ce nom existe déjà
                self.cursor.execute("SELECT id FROM categories WHERE name=? AND id!=?", (new_name, cat_id))
                if self.cursor.fetchone():
                    messagebox.showwarning("Attention", "Une catégorie avec ce nom existe déjà.")
                    return
                # Vérifier le niveau d'imbrication
                level = 0
                current_parent = new_parent_id
                while current_parent:
                    self.cursor.execute("SELECT parent_id FROM categories WHERE id=?", (current_parent,))
                    current_parent = self.cursor.fetchone()[0]
                    level += 1
                if level >= 5:
                    messagebox.showwarning("Attention", "Limite de 5 niveaux de sous-catégories atteinte.")
                    return
                self.cursor.execute("UPDATE categories SET name=?, parent_id=? WHERE id=?", 
                                    (new_name, new_parent_id, cat_id))
                self.conn.commit()
                self.cat_name_entry.delete(0, tk.END)
                self.cat_parent.set("Aucune")
                self.create_cat_button.config(text="Créer Catégorie", command=self.add_category)  # Réinitialiser le bouton
                self.update_ui()

        self.create_cat_button.config(text="Sauvegarder", command=save_edit)

    def delete_category(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez une catégorie à supprimer.")
            return
        item = self.tree.item(selected[0])["values"]
        if not str(item[0]).startswith("cat_"):
            messagebox.showwarning("Attention", "Sélectionnez une catégorie à supprimer.")
            return
        cat_id = int(item[0].split("_")[1])
        if messagebox.askyesno("Confirmation", "Supprimer cette catégorie et ses compteurs associés ?"):
            # Supprimer les compteurs associés
            self.cursor.execute("DELETE FROM meters WHERE category_id=?", (cat_id,))
            # Supprimer les sous-catégories récursivement
            self.delete_subcategories(cat_id)
            # Supprimer la catégorie
            self.cursor.execute("DELETE FROM categories WHERE id=?", (cat_id,))
            self.conn.commit()
            self.update_ui()

    def delete_subcategories(self, cat_id):
        """Supprime récursivement les sous-catégories et leurs compteurs."""
        self.cursor.execute("SELECT id FROM categories WHERE parent_id=?", (cat_id,))
        subcats = self.cursor.fetchall()
        for subcat_id in subcats:
            self.delete_subcategories(subcat_id[0])
            self.cursor.execute("DELETE FROM meters WHERE category_id=?", (subcat_id[0],))
            self.cursor.execute("DELETE FROM categories WHERE id=?", (subcat_id[0],))

    def update_ui(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.cursor.execute("SELECT id, name, note FROM meters")
        meters = self.cursor.fetchall()
        print(f"Meters loaded: {meters}")  # Débogage
        for meter in meters:
            self.tree.insert("", tk.END, values=meter)
        self.cursor.execute("SELECT id, name FROM categories")
        categories = self.cursor.fetchall()
        print(f"Categories loaded: {categories}")  # Débogage
        for cat in categories:
            self.tree.insert("", tk.END, values=(f"cat_{cat[0]}", cat[1], ""))

        self.update_category_combobox()

        self.canvas.delete("all")
        self.cat_positions = {}
        self.meter_rects = {}

        # Positionner les catégories principales côte à côte
        x_pos = 20
        y_pos = 20
        self.cursor.execute("SELECT id, name, width, height FROM categories WHERE parent_id IS NULL")
        top_categories = self.cursor.fetchall()
        top_cat_ids = [cat[0] for cat in top_categories]
        for cat_id, name, width, height in top_categories:
            self.cat_positions[cat_id] = (x_pos, y_pos, x_pos + width, y_pos + height, width, height)
            self.cursor.execute("UPDATE categories SET x_pos=?, y_pos=? WHERE id=?", (x_pos, y_pos, cat_id))
            x_pos += width + 70  # Espace entre les catégories principales

        # Calculer la hauteur totale de chaque catégorie principale
        for cat_id in top_cat_ids:
            self.calculate_category_height(cat_id)

        # Dessiner les éléments avec des couleurs différentes
        self.cursor.execute("SELECT id, name, x_pos, y_pos, width, height, parent_id FROM categories")
        categories = self.cursor.fetchall()
        for cat_id, name, x_pos, y_pos, width, height, parent_id in categories:
            # Déterminer le niveau d'imbrication pour choisir la couleur
            level = 0
            current_parent = parent_id
            while current_parent:
                self.cursor.execute("SELECT parent_id FROM categories WHERE id=?", (current_parent,))
                current_parent = self.cursor.fetchone()[0]
                level += 1
            # Couleur différente selon le niveau d'imbrication
            if parent_id is None:
                fill_color = "#D3D3D3"  # Gris clair pour les catégories principales
            else:
                colors = {
                    1: "#ADD8E6",  # Bleu clair (niveau 1)
                    2: "#FFB6C1",  # Rose clair (niveau 2)
                    3: "#98FB98",  # Vert pâle (niveau 3)
                    4: "#FFDAB9",  # Pêche clair (niveau 4)
                    5: "#E6E6FA"   # Lavande clair (niveau 5)
                }
                fill_color = colors.get(level, "#ADD8E6")  # Par défaut, bleu clair si niveau > 5
            rect = self.canvas.create_rectangle(x_pos, y_pos, x_pos + width, y_pos + height, fill=fill_color, tags=f"cat_{cat_id}")
            text = self.canvas.create_text(x_pos + width/2, y_pos + 15, text=name, font=("Arial", 10, "bold"), tags=f"cat_{cat_id}_text")

        self.cursor.execute("SELECT id, name, category_id, x_pos, y_pos FROM meters")
        meters = self.cursor.fetchall()
        for meter_id, name, category_id, x_pos, y_pos in meters:
            # Si x_pos ou y_pos est None, utiliser des valeurs par défaut
            x_pos = x_pos if x_pos is not None else 20
            y_pos = y_pos if y_pos is not None else 60
            rect = self.canvas.create_rectangle(x_pos, y_pos, x_pos + 130, y_pos + 30, fill="#FFC107", tags=f"meter_{meter_id}")  # Jaune foncé pour les compteurs
            text = self.canvas.create_text(x_pos + 65, y_pos + 15, text=name, tags=f"meter_{meter_id}_text")

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def calculate_category_height(self, cat_id):
        """Calcule la hauteur totale d'une catégorie, y compris ses sous-catégories et compteurs."""
        if cat_id not in self.cat_positions:
            return 50  # Hauteur par défaut si la catégorie n'est pas encore positionnée
        x1, y1, x2, y2, width, height = self.cat_positions[cat_id]
        y_offset = y1 + 50  # Espace pour le titre de la catégorie

        # Calculer la hauteur des sous-catégories
        self.cursor.execute("SELECT id, width, height FROM categories WHERE parent_id=?", (cat_id,))
        subcats = self.cursor.fetchall()
        for subcat_id, sub_width, sub_height in subcats:
            self.cat_positions[subcat_id] = (x1 + 10, y_offset, x1 + 10 + sub_width, y_offset + sub_height, sub_width, sub_height)
            self.cursor.execute("UPDATE categories SET x_pos=?, y_pos=? WHERE id=?", (x1 + 10, y_offset, subcat_id))
            sub_height = self.calculate_category_height(subcat_id)
            self.cat_positions[subcat_id] = (x1 + 10, y_offset, x1 + 10 + sub_width, y_offset + sub_height, sub_width, sub_height)
            self.cursor.execute("UPDATE categories SET x_pos=?, y_pos=?, height=? WHERE id=?", (x1 + 10, y_offset, sub_height, subcat_id))
            y_offset += sub_height + 10

        # Calculer la hauteur des compteurs
        self.cursor.execute("SELECT id FROM meters WHERE category_id=?", (cat_id,))
        meters = self.cursor.fetchall()
        for meter_id in meters:
            meter_id = meter_id[0]
            self.cursor.execute("UPDATE meters SET x_pos=?, y_pos=? WHERE id=?", (x1 + 10, y_offset, meter_id))
            y_offset += 40  # Hauteur d'un compteur + marge

        # Ajuster la hauteur de la catégorie
        new_height = max(50, y_offset - y1 + 10)
        self.cat_positions[cat_id] = (x1, y1, x2, y1 + new_height, width, new_height)
        self.cursor.execute("UPDATE categories SET height=? WHERE id=?", (new_height, cat_id))
        return new_height

    def adjust_subcategory_positions(self, cat_id, parent_y):
        """Ajuste les positions des sous-catégories et compteurs."""
        if cat_id not in self.cat_positions:
            return
        x1, y1, x2, y2, width, height = self.cat_positions[cat_id]
        y_offset = parent_y + 50

        # Ajuster les sous-catégories
        self.cursor.execute("SELECT id, width, height FROM categories WHERE parent_id=?", (cat_id,))
        subcats = self.cursor.fetchall()
        for subcat_id, sub_width, sub_height in subcats:
            self.cat_positions[subcat_id] = (x1 + 10, y_offset, x1 + 10 + sub_width, y_offset + sub_height, sub_width, sub_height)
            self.cursor.execute("UPDATE categories SET x_pos=?, y_pos=? WHERE id=?", (x1 + 10, y_offset, subcat_id))
            self.adjust_subcategory_positions(subcat_id, y_offset)
            # Mettre à jour la position après ajustement des sous-sous-catégories
            _, _, _, sub_y2, _, sub_height = self.cat_positions[subcat_id]
            y_offset = sub_y2 + 10

        # Ajuster les compteurs
        self.cursor.execute("SELECT id FROM meters WHERE category_id=?", (cat_id,))
        meters = self.cursor.fetchall()
        for meter_id in meters:
            meter_id = meter_id[0]
            self.cursor.execute("UPDATE meters SET x_pos=?, y_pos=? WHERE id=?", (x1 + 10, y_offset, meter_id))
            y_offset += 40

        # Ajuster la hauteur de la catégorie
        new_height = max(50, y_offset - parent_y + 10)
        self.cat_positions[cat_id] = (x1, parent_y, x2, parent_y + new_height, width, new_height)
        self.cursor.execute("UPDATE categories SET height=? WHERE id=?", (new_height, cat_id))

    def select_item(self, event):
        """Sélectionne un élément dans le canvas et met à jour la sélection dans le Treeview."""
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        items = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)
        for item in items:
            tags = self.canvas.gettags(item)
            if "text" in tags[0]:  # Sélectionner uniquement via le texte
                if "meter" in tags[0]:
                    meter_id = tags[0].split("_")[1]
                    self.cursor.execute("SELECT id FROM meters WHERE id=?", (meter_id,))
                    meter = self.cursor.fetchone()
                    print(f"Canvas selected meter ID: {meter_id}, Data: {meter}")  # Débogage
                    if meter:
                        for tree_item in self.tree.get_children():
                            values = self.tree.item(tree_item)["values"]
                            if values and str(values[0]) == str(meter[0]):
                                print(f"Found meter in Treeview: {values}")  # Débogage
                                self.tree.selection_set(tree_item)
                                break
                elif "cat" in tags[0]:
                    cat_id = tags[0].split("_")[1]
                    self.cursor.execute("SELECT id FROM categories WHERE id=?", (cat_id,))
                    cat = self.cursor.fetchone()
                    print(f"Canvas selected category ID: {cat_id}, Data: {cat}")  # Débogage
                    if cat:
                        for tree_item in self.tree.get_children():
                            values = self.tree.item(tree_item)["values"]
                            if values and values[0] == f"cat_{cat[0]}":
                                print(f"Found category in Treeview: {values}")  # Débogage
                                self.tree.selection_set(tree_item)
                                break
                break

    def on_treeview_select(self, event):
        """Gère la sélection d'un élément dans le Treeview pour modification."""
        selected = self.tree.selection()
        if not selected:
            self.edit_meter_button.config(state="disabled")
            self.delete_meter_button.config(state="disabled")
            self.edit_cat_button.config(state="disabled")
            self.delete_cat_button.config(state="disabled")
            return
        item = self.tree.item(selected[0])["values"]
        print(f"Selected item: {item}")  # Débogage
        if str(item[0]).startswith("cat_"):
            cat_id = int(item[0].split("_")[1])
            print(f"Selected category ID: {cat_id}")  # Débogage
            self.cursor.execute("SELECT name, parent_id FROM categories WHERE id=?", (cat_id,))
            cat = self.cursor.fetchone()
            print(f"Category data: {cat}")  # Débogage
            self.cat_name_entry.delete(0, tk.END)
            self.cat_name_entry.insert(0, cat[0])  # Utiliser cat[0] pour le nom
            parent_name = "Aucune"
            if cat[1]:  # Utiliser cat[1] pour parent_id
                for display_name, c_id in self.cat_hierarchy.items():
                    if c_id == cat[1]:
                        parent_name = display_name
                        break
            self.cat_parent.set(parent_name)
            self.meter_name.delete(0, tk.END)
            self.meter_note.delete("1.0", tk.END)
            self.meter_category.set("Aucune")
            self.edit_meter_button.config(state="disabled")
            self.delete_meter_button.config(state="disabled")
            self.edit_cat_button.config(state="normal")
            self.delete_cat_button.config(state="normal")
        else:
            meter_id = item[0]
            print(f"Selected meter ID: {meter_id}")  # Débogage
            self.cursor.execute("SELECT name, note, category_id FROM meters WHERE id=?", (meter_id,))
            meter = self.cursor.fetchone()
            print(f"Meter data: {meter}")  # Débogage
            if meter:
                self.meter_name.delete(0, tk.END)
                self.meter_name.insert(0, meter[0])
                self.meter_note.delete("1.0", tk.END)
                self.meter_note.insert("1.0", meter[1])
                category_id = meter[2]
                category_name = "Aucune"
                if category_id:
                    for display_name, c_id in self.cat_hierarchy.items():
                        if c_id == category_id:
                            category_name = display_name
                            break
                self.meter_category.set(category_name)
                self.cat_name_entry.delete(0, tk.END)
                self.cat_parent.set("Aucune")
                self.edit_meter_button.config(state="normal")
                self.delete_meter_button.config(state="normal")
                self.edit_cat_button.config(state="disabled")
                self.delete_cat_button.config(state="disabled")
            else:
                messagebox.showwarning("Erreur", "Le compteur sélectionné n'existe pas dans la base de données.")

    def filter_treeview(self, event):
        """Filtre les éléments du Treeview en fonction de la recherche dans les champs Nom et Note."""
        search_term = self.search_entry.get().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.cursor.execute("SELECT id, name, note FROM meters")
        meters = self.cursor.fetchall()
        self.cursor.execute("SELECT id, name FROM categories")
        categories = self.cursor.fetchall()

        # Ajouter les compteurs qui correspondent à la recherche
        for meter in meters:
            meter_id, name, note = meter
            if (search_term in name.lower()) or (note and search_term in note.lower()):
                self.tree.insert("", tk.END, values=meter)

        # Ajouter les catégories qui correspondent à la recherche
        for cat in categories:
            cat_id, name = cat
            if search_term in name.lower():
                self.tree.insert("", tk.END, values=(f"cat_{cat_id}", name, ""))

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = MeterApp(root)
    root.mainloop()