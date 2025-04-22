import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import shutil

class Tooltip:
    def __init__(self, canvas, item_id, text):
        self.canvas = canvas
        self.item_id = item_id
        self.text = text
        self.tooltip = None
        self.canvas.tag_bind(item_id, "<Enter>", self.show_tooltip)
        self.canvas.tag_bind(item_id, "<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        if self.item_id not in self.canvas.find_all():
            return
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        x += 20
        y += 20
        self.tooltip = self.canvas.create_text(x, y, text=self.text, font=("Arial", 8), anchor="nw", tags="tooltip", fill="black")
        self.canvas.tag_raise(self.tooltip)

    def hide_tooltip(self, event):
        if self.tooltip:
            self.canvas.delete(self.tooltip)
            self.tooltip = None

class DBDesigner:
    def __init__(self, parent, conn):
        self.parent = parent
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.create_initial_tables()

        self.zoom_factor = 1.0
        self.node_positions = {}
        self.meter_sizes = {}
        self.expanded_nodes = set()
        self.dragging_node = None
        self.dragging_start = None
        self.level_positions = {}
        self.node_heights = {}
        self.cat_hierarchy = {}

        # Frame principale avec deux volets
        self.main_frame = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill="both", expand=True)

        # Volet gauche : Canvas avec scrollbars
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.canvas_frame, weight=7)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white", scrollregion=(0, 0, 1000, 1000))
        h_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.config(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        # Ajout des boutons de zoom
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
        self.main_frame.add(self.config_frame, weight=3)

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

        meter_buttons_frame = ttk.Frame(meter_frame)
        meter_buttons_frame.pack(fill="x", pady=5)
        self.create_meter_button = tk.Button(meter_buttons_frame, text="Créer Compteur", command=self.add_meter)
        self.create_meter_button.pack(side="left", padx=5)
        self.edit_meter_button = tk.Button(meter_buttons_frame, text="Modifier Compteur", command=self.edit_meter, state="disabled")
        self.edit_meter_button.pack(side="left", padx=5)
        self.delete_meter_button = tk.Button(meter_buttons_frame, text="Supprimer Compteur", command=self.delete_meter, state="disabled")
        self.delete_meter_button.pack(side="left", padx=5)

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

        cat_buttons_frame = ttk.Frame(cat_frame)
        cat_buttons_frame.pack(fill="x", pady=5)
        self.create_cat_button = tk.Button(cat_buttons_frame, text="Créer Catégorie", command=self.add_category)
        self.create_cat_button.pack(side="left", padx=5)
        self.edit_cat_button = tk.Button(cat_buttons_frame, text="Modifier Catégorie", command=self.edit_category, state="disabled")
        self.edit_cat_button.pack(side="left", padx=5)
        self.delete_cat_button = tk.Button(cat_buttons_frame, text="Supprimer Catégorie", command=self.delete_category, state="disabled")
        self.delete_cat_button.pack(side="left", padx=5)

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

        self.tree.bind("<<TreeviewSelect>>", self.on_treeview_select)
        self.canvas.bind("<MouseWheel>", self.scroll_canvas)
        self.canvas.bind("<Button-4>", self.scroll_canvas)
        self.canvas.bind("<Button-5>", self.scroll_canvas)
        self.canvas.bind("<ButtonPress-1>", self.on_node_click)
        self.canvas.bind("<Double-1>", self.on_node_double_click)
        self.canvas.bind("<B1-Motion>", self.on_node_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_node_release)

        self.update_ui()

    def scroll_canvas(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def zoom(self, factor):
        self.zoom_factor *= factor
        self.zoom_factor = max(0.1, min(self.zoom_factor, 5.0))
        self.canvas.scale("all", 0, 0, factor, factor)
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)
        self.zoom_label.config(text=f"Zoom : {int(self.zoom_factor * 100)}%")

    def reset_zoom(self):
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
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meter_id INTEGER,
            date TEXT NOT NULL,
            meter_index INTEGER NOT NULL,
            consumption INTEGER DEFAULT 0,
            note TEXT,
            FOREIGN KEY (meter_id) REFERENCES meters(id)
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS base_indices (
            meter_id INTEGER PRIMARY KEY,
            base_index INTEGER NOT NULL,
            FOREIGN KEY (meter_id) REFERENCES meters(id)
        )''')
        try:
            self.cursor.execute("ALTER TABLE readings ADD COLUMN consumption INTEGER DEFAULT 0")
        except:
            pass
        self.conn.commit()

    def update_category_combobox(self):
        self.cursor.execute("SELECT id, name, parent_id FROM categories")
        categories = self.cursor.fetchall()
        cat_names = ["Aucune"]
        self.cat_hierarchy = {"Aucune": None}
        for cat_id, name, parent_id in categories:
            hierarchy = []
            current_id = cat_id
            while current_id:
                self.cursor.execute("SELECT name, parent_id FROM categories WHERE id=?", (current_id,))
                cat = self.cursor.fetchone()
                if not cat:
                    break
                hierarchy.append(cat[0])
                current_id = cat[1]
            display_name = " > ".join(reversed(hierarchy))
            cat_names.append(display_name)
            self.cat_hierarchy[display_name] = cat_id
        self.meter_category["values"] = cat_names
        self.cat_parent["values"] = cat_names
        self.meter_category.set("Aucune")
        self.cat_parent.set("Aucune")

    def add_meter(self):
        name = self.meter_name.get()
        note = self.meter_note.get("1.0", tk.END).strip()
        category = self.meter_category.get()
        category_id = self.cat_hierarchy.get(category)
        if not name:
            messagebox.showwarning("Attention", "Entrez un nom pour le compteur.")
            return
        self.cursor.execute("INSERT INTO meters (name, note, category_id) VALUES (?, ?, ?)", (name, note, category_id))
        self.conn.commit()
        self.meter_name.delete(0, tk.END)
        self.meter_note.delete("1.0", tk.END)
        self.meter_category.set("Aucune")
        self.create_meter_button.config(text="Créer Compteur", command=self.add_meter)
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
        self.cursor.execute("SELECT name, note, category_id FROM meters WHERE id=?", (meter_id,))
        name, note, category_id = self.cursor.fetchone()
        self.meter_name.delete(0, tk.END)
        self.meter_name.insert(0, name)
        self.meter_note.delete("1.0", tk.END)
        self.meter_note.insert("1.0", note if note else "")
        category_name = "Aucune"
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
            if not new_name:
                messagebox.showwarning("Attention", "Entrez un nom pour le compteur.")
                return
            self.cursor.execute("UPDATE meters SET name=?, note=?, category_id=? WHERE id=?", 
                                (new_name, new_note, new_category_id, meter_id))
            self.conn.commit()
            self.meter_name.delete(0, tk.END)
            self.meter_note.delete("1.0", tk.END)
            self.meter_category.set("Aucune")
            self.create_meter_button.config(text="Créer Compteur", command=self.add_meter)
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
        if messagebox.askyesno("Confirmation", "Supprimer ce compteur et ses relevés ?"):
            self.cursor.execute("DELETE FROM readings WHERE meter_id=?", (meter_id,))
            self.cursor.execute("DELETE FROM base_indices WHERE meter_id=?", (meter_id,))
            self.cursor.execute("DELETE FROM meters WHERE id=?", (meter_id,))
            self.conn.commit()
            self.update_ui()

    def add_category(self):
        name = self.cat_name_entry.get()
        parent = self.cat_parent.get()
        parent_id = self.cat_hierarchy.get(parent)
        if not name:
            messagebox.showwarning("Attention", "Entrez un nom pour la catégorie.")
            return
        self.cursor.execute("SELECT id FROM categories WHERE name=?", (name,))
        if self.cursor.fetchone():
            messagebox.showwarning("Attention", "Une catégorie avec ce nom existe déjà.")
            return
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
        self.create_cat_button.config(text="Créer Catégorie", command=self.add_category)
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
        name, parent_id = self.cursor.fetchone()
        self.cat_name_entry.delete(0, tk.END)
        self.cat_name_entry.insert(0, name)
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
            if not new_name:
                messagebox.showwarning("Attention", "Entrez un nom pour la catégorie.")
                return
            self.cursor.execute("SELECT id FROM categories WHERE name=? AND id!=?", (new_name, cat_id))
            if self.cursor.fetchone():
                messagebox.showwarning("Attention", "Une catégorie avec ce nom existe déjà.")
                return
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
            self.create_cat_button.config(text="Créer Catégorie", command=self.add_category)
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
            self.cursor.execute("SELECT id FROM meters WHERE category_id=?", (cat_id,))
            meters = self.cursor.fetchall()
            for meter in meters:
                meter_id = meter[0]
                self.cursor.execute("DELETE FROM readings WHERE meter_id=?", (meter_id,))
                self.cursor.execute("DELETE FROM base_indices WHERE meter_id=?", (meter_id,))
            self.cursor.execute("DELETE FROM meters WHERE category_id=?", (cat_id,))
            self.delete_subcategories(cat_id)
            self.cursor.execute("DELETE FROM categories WHERE id=?", (cat_id,))
            self.conn.commit()
            self.update_ui()

    def delete_subcategories(self, cat_id):
        self.cursor.execute("SELECT id FROM categories WHERE parent_id=?", (cat_id,))
        subcats = self.cursor.fetchall()
        for subcat_id in subcats:
            self.cursor.execute("SELECT id FROM meters WHERE category_id=?", (subcat_id[0],))
            meters = self.cursor.fetchall()
            for meter in meters:
                meter_id = meter[0]
                self.cursor.execute("DELETE FROM readings WHERE meter_id=?", (meter_id,))
                self.cursor.execute("DELETE FROM base_indices WHERE meter_id=?", (meter_id,))
            self.cursor.execute("DELETE FROM meters WHERE category_id=?", (subcat_id[0],))
            self.delete_subcategories(subcat_id[0])
            self.cursor.execute("DELETE FROM categories WHERE id=?", (subcat_id[0],))
        self.conn.commit()

    def update_ui(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.cursor.execute("SELECT id, name, note FROM meters")
        meters = self.cursor.fetchall()
        for meter in meters:
            self.tree.insert("", tk.END, values=meter)
        self.cursor.execute("SELECT id, name FROM categories")
        categories = self.cursor.fetchall()
        for cat in categories:
            self.tree.insert("", tk.END, values=(f"cat_{cat[0]}", cat[1], ""))

        self.update_category_combobox()

        # Mise à jour du Canvas - Arborescence interactive
        self.canvas.delete("all")
        self.node_positions = {}
        self.meter_sizes = {}
        self.level_positions = {0: 20}  # Initialiser les positions Y par niveau
        self.node_heights = {}  # Réinitialiser les hauteurs des sous-arbres
        x_pos = 20
        text_font = tk.font.Font(family="Arial", size=12, weight="bold")
        meter_font = tk.font.Font(family="Arial", size=10)

        # Calculer les tailles des compteurs
        self.cursor.execute("SELECT id, name, category_id FROM meters ORDER BY name")
        meters = self.cursor.fetchall()
        for meter_id, name, category_id in meters:
            text_width = meter_font.measure(name) + 20
            text_height = meter_font.metrics("linespace") + 10
            self.meter_sizes[meter_id] = (max(130, text_width), max(30, text_height))

        # Calculer les hauteurs des sous-arbres
        self.cursor.execute("SELECT id FROM categories WHERE parent_id IS NULL")
        top_categories = self.cursor.fetchall()
        for cat_id, in top_categories:
            self.calculate_subtree_height(cat_id)

        # Dessiner l'arborescence
        for cat_id, in top_categories:
            self.draw_category_tree(cat_id, x_pos, 0)

        # Dessiner les nœuds et connexions
        self.draw_nodes()

        self.canvas.configure(scrollregion=self.canvas.bbox("all") or (0, 0, 1000, 1000))

    def calculate_subtree_height(self, cat_id):
        text_font = tk.font.Font(family="Arial", size=12, weight="bold")
        self.cursor.execute("SELECT name FROM categories WHERE id=?", (cat_id,))
        name = self.cursor.fetchone()[0]
        text_height = text_font.metrics("linespace") + 10
        height = max(30, text_height)

        if cat_id not in self.expanded_nodes:
            self.node_heights[cat_id] = height + 60  # Augmenté de 40 à 60
            return self.node_heights[cat_id]

        total_height = height + 60  # Augmenté de 40 à 60
        self.cursor.execute("SELECT id FROM categories WHERE parent_id=?", (cat_id,))
        subcats = self.cursor.fetchall()
        for subcat_id, in subcats:
            sub_height = self.calculate_subtree_height(subcat_id)
            total_height += sub_height

        self.cursor.execute("SELECT id FROM meters WHERE category_id=? ORDER BY name", (cat_id,))
        meters = self.cursor.fetchall()
        for meter_id, in meters:
            _, meter_height = self.meter_sizes[meter_id]
            total_height += meter_height + 30  # Augmenté de 20 à 30

        self.node_heights[cat_id] = total_height
        return total_height

    def draw_category_tree(self, cat_id, x_base, level):
        text_font = tk.font.Font(family="Arial", size=12, weight="bold")
        x_pos = x_base + level * 300  # Augmenté de 250 à 300 pour l'espacement horizontal

        if level not in self.level_positions:
            self.level_positions[level] = 20
        y_pos = self.level_positions[level]

        self.cursor.execute("SELECT name FROM categories WHERE id=?", (cat_id,))
        name = self.cursor.fetchone()[0]
        text_width = text_font.measure(name) + 20
        text_height = text_font.metrics("linespace") + 10
        width = max(150, text_width)
        height = max(30, text_height)
        self.node_positions[(cat_id, "category")] = (x_pos, y_pos, width, height)

        self.level_positions[level] = y_pos + self.node_heights.get(cat_id, height + 60)

        if cat_id not in self.expanded_nodes:
            return

        self.cursor.execute("SELECT id, name FROM categories WHERE parent_id=?", (cat_id,))
        subcats = self.cursor.fetchall()
        y_offset = y_pos + height + 60  # Augmenté de 40 à 60
        for subcat_id, _ in subcats:
            self.level_positions[level + 1] = y_offset
            self.draw_category_tree(subcat_id, x_base, level + 1)
            y_offset += self.node_heights.get(subcat_id, 0)

        self.cursor.execute("SELECT id, name FROM meters WHERE category_id=? ORDER BY name", (cat_id,))
        meters = self.cursor.fetchall()
        meter_level = level + 1
        y_pos = y_offset if subcats else y_pos + height + 60  # Augmenté de 40 à 60
        self.level_positions[meter_level] = y_pos
        for meter_id, _ in meters:
            width, height = self.meter_sizes[meter_id]
            self.node_positions[(meter_id, "meter")] = (x_pos + 300, y_pos, width, height)  # Augmenté de 250 à 300
            self.cursor.execute("UPDATE meters SET x_pos=?, y_pos=? WHERE id=?", (x_pos + 300, y_pos, meter_id))
            y_pos += height + 30  # Augmenté de 20 à 30
        if meters:
            self.level_positions[meter_level] = y_pos

    def draw_nodes(self):
        self.canvas.delete("all")
        tooltips = []
        for (node_id, node_type), (x, y, width, height) in self.node_positions.items():
            if node_type == "category":
                fill_color = "#D3D3D3" if not self.cursor.execute("SELECT parent_id FROM categories WHERE id=?", (node_id,)).fetchone()[0] else "#ADD8E6"
                self.cursor.execute("SELECT name FROM categories WHERE id=?", (node_id,))
                name = self.cursor.fetchone()[0]
                prefix = "+" if node_id not in self.expanded_nodes else "-"
                rect = self.canvas.create_rectangle(x, y - height/2, x + width, y + height/2, fill=fill_color, tags=f"cat_{node_id}")
                self.canvas.create_text(x + 10, y, text=f"{prefix} {name}", font=("Arial", 12, "bold"), anchor="w", tags=f"cat_{node_id}_text")
                self.cursor.execute("SELECT COUNT(*) FROM meters WHERE category_id=?", (node_id,))
                meter_count = self.cursor.fetchone()[0]
                tooltip_text = f"Catégorie: {name}\nCompteurs: {meter_count}"
                tooltips.append(Tooltip(self.canvas, rect, tooltip_text))
            elif node_type == "meter":
                self.cursor.execute("SELECT name, note FROM meters WHERE id=?", (node_id,))
                name, note = self.cursor.fetchone()
                rect = self.canvas.create_rectangle(x, y - height/2, x + width, y + height/2, fill="#FFC107", tags=f"meter_{node_id}")
                self.canvas.create_text(x + 10, y, text=name, font=("Arial", 10), anchor="w", tags=f"meter_{node_id}_text")
                tooltip_text = f"Compteur: {name}\nNote: {note if note else 'Aucune'}"
                tooltips.append(Tooltip(self.canvas, rect, tooltip_text))

        self.cursor.execute("SELECT id, parent_id FROM categories")
        categories = self.cursor.fetchall()
        for cat_id, parent_id in categories:
            if parent_id and (cat_id, "category") in self.node_positions and (parent_id, "category") in self.node_positions:
                if parent_id in self.expanded_nodes:
                    x1, y1, w1, _ = self.node_positions[(parent_id, "category")]
                    x2, y2, w2, _ = self.node_positions[(cat_id, "category")]
                    mid_x = x1 + w1 + (x2 - (x1 + w1)) / 2
                    self.canvas.create_line(x1 + w1, y1, mid_x, y1, mid_x, y2, x2, y2, fill="black", width=1)

        self.cursor.execute("SELECT id, category_id FROM meters")
        meters = self.cursor.fetchall()
        for meter_id, category_id in meters:
            if (meter_id, "meter") in self.node_positions and (category_id, "category") in self.node_positions:
                if category_id in self.expanded_nodes:
                    x1, y1, w1, _ = self.node_positions[(category_id, "category")]
                    x2, y2, w2, _ = self.node_positions[(meter_id, "meter")]
                    mid_x = x1 + w1 + (x2 - (x1 + w1)) / 2
                    self.canvas.create_line(x1 + w1, y1, mid_x, y1, mid_x, y2, x2, y2, fill="black", width=1)

    def on_node_click(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        items = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)
        for item in items:
            tags = self.canvas.gettags(item)
            if tags:
                if "cat_" in tags[0]:
                    cat_id = int(tags[0].split("_")[1])
                    for tree_item in self.tree.get_children():
                        values = self.tree.item(tree_item)["values"]
                        if values and values[0] == f"cat_{cat_id}":
                            self.tree.selection_set(tree_item)
                            break
                    self.dragging_node = (cat_id, "category")
                    self.dragging_start = (x, y)
                    return
                elif "meter_" in tags[0]:
                    meter_id = tags[0].split("_")[1]
                    for tree_item in self.tree.get_children():
                        values = self.tree.item(tree_item)["values"]
                        if values and str(values[0]) == meter_id:
                            self.tree.selection_set(tree_item)
                            break
                    self.dragging_node = (meter_id, "meter")
                    self.dragging_start = (x, y)
                    return
        self.dragging_node = None

    def on_node_double_click(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        items = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)
        for item in items:
            tags = self.canvas.gettags(item)
            if tags:
                if "cat_" in tags[0]:
                    cat_id = int(tags[0].split("_")[1])
                    if cat_id in self.expanded_nodes:
                        self.expanded_nodes.remove(cat_id)
                    else:
                        self.expanded_nodes.add(cat_id)
                    self.dragging_node = None
                    self.update_ui()
                    return
                elif "meter_" in tags[0]:
                    meter_id = tags[0].split("_")[1]
                    self.open_add_reading_window(meter_id)
                    return

    def open_add_reading_window(self, meter_id):
        popup = tk.Toplevel(self.parent)
        popup.title("Ajouter un Relevé")
        popup.transient(self.parent)

        # Variables pour le formulaire
        month_var = tk.StringVar(value=f"{datetime.now().month:02d}")
        year_var = tk.StringVar(value=str(datetime.now().year))
        index_var = tk.StringVar()
        note_var = tk.StringVar()

        # Formulaire
        form_frame = ttk.Frame(popup)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Compteur (affiché mais non modifiable)
        self.cursor.execute("SELECT name FROM meters WHERE id=?", (meter_id,))
        meter_name = self.cursor.fetchone()[0]
        ttk.Label(form_frame, text="Compteur :").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(form_frame, text=meter_name).grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="w")

        # Date (mois et année)
        ttk.Label(form_frame, text="Mois :").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        month_combobox = ttk.Combobox(form_frame, textvariable=month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly")
        month_combobox.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Année :").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        year_combobox = ttk.Combobox(form_frame, textvariable=year_var, values=[str(i) for i in range(2000, 2030)], width=7, state="readonly")
        year_combobox.grid(row=1, column=3, padx=5, pady=5)

        # Index
        ttk.Label(form_frame, text="Index :").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        index_entry = ttk.Entry(form_frame, textvariable=index_var, width=30)
        index_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Note
        ttk.Label(form_frame, text="Note :").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        note_entry = ttk.Entry(form_frame, textvariable=note_var, width=30)
        note_entry.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Boutons
        buttons_frame = ttk.Frame(popup)
        buttons_frame.pack(fill="x", pady=10)
        ttk.Button(buttons_frame, text="Enregistrer", command=lambda: self.add_reading_from_popup(meter_id, month_var.get(), year_var.get(), index_var.get(), note_var.get(), popup)).pack(side="right", padx=5)
        ttk.Button(buttons_frame, text="Annuler", command=popup.destroy).pack(side="right", padx=5)

        popup.after(100, lambda: self.set_popup_grab(popup))

    def set_popup_grab(self, popup):
        try:
            if popup.winfo_exists():
                popup.update_idletasks()
                popup.wait_visibility()
                popup.grab_set()
        except tk.TclError as e:
            print(f"Erreur lors de grab_set: {e}")

    def add_reading_from_popup(self, meter_id, month, year, index, note, popup):
        if not (month and year and index):
            messagebox.showwarning("Erreur", "Veuillez remplir tous les champs requis (date, index).")
            return
        index = index.replace(" ", "")
        if not index.isdigit():
            messagebox.showwarning("Erreur", "L'index doit être un nombre entier.")
            return
        index = int(index)
        date = f"{year}-{month}"
        try:
            self.cursor.execute("INSERT INTO readings (meter_id, date, meter_index, note) VALUES (?, ?, ?, ?)", 
                               (meter_id, date, index, note))
            self.conn.commit()
            # Mettre à jour les consommations
            self.update_all_consumptions(meter_id)
            popup.destroy()
            messagebox.showinfo("Succès", "Relevé enregistré.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def update_all_consumptions(self, meter_id):
        self.cursor.execute("SELECT base_index FROM base_indices WHERE meter_id=?", (meter_id,))
        base_index = self.cursor.fetchone()
        base_index = base_index[0] if base_index else 0
        self.cursor.execute("SELECT id, meter_index, date FROM readings WHERE meter_id=? ORDER BY date", (meter_id,))
        readings = self.cursor.fetchall()
        prev_index = base_index
        for reading in readings:
            reading_id, current_index, date = reading
            consumption = current_index - prev_index if current_index >= prev_index else 0
            self.cursor.execute("UPDATE readings SET consumption=? WHERE id=?", (consumption, reading_id))
            prev_index = current_index
        self.conn.commit()

    def on_node_drag(self, event):
        if not self.dragging_node:
            return
        node_id, node_type = self.dragging_node
        if (node_id, node_type) not in self.node_positions:
            self.dragging_node = None
            return
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        dx = x - self.dragging_start[0]
        dy = y - self.dragging_start[1]
        current_pos = self.node_positions[(node_id, node_type)]
        new_pos = (current_pos[0] + dx, current_pos[1] + dy, current_pos[2], current_pos[3])
        self.node_positions[(node_id, node_type)] = new_pos
        self.dragging_start = (x, y)
        self.draw_nodes()

    def on_node_release(self, event):
        if not self.dragging_node:
            return
        node_id, node_type = self.dragging_node
        if (node_id, node_type) not in self.node_positions:
            self.dragging_node = None
            return
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if node_type == "meter":
            closest_cat = None
            min_dist = float("inf")
            for (cat_id, cat_type), (cx, cy, cw, ch) in self.node_positions.items():
                if cat_type == "category":
                    dist = ((x - cx)**2 + (y - cy)**2)**0.5
                    if dist < min_dist:
                        min_dist = dist
                        closest_cat = cat_id
            if closest_cat:
                self.cursor.execute("UPDATE meters SET category_id=? WHERE id=?", (closest_cat, node_id))
                self.conn.commit()
        self.dragging_node = None
        self.update_ui()

    def filter_treeview(self, event):
        search_term = self.search_entry.get().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.cursor.execute("SELECT id, name, note FROM meters")
        meters = self.cursor.fetchall()
        self.cursor.execute("SELECT id, name FROM categories")
        categories = self.cursor.fetchall()

        for meter in meters:
            meter_id, name, note = meter
            if (search_term in name.lower()) or (note and search_term in note.lower()):
                self.tree.insert("", tk.END, values=meter)

        for cat in categories:
            cat_id, name = cat
            if search_term in name.lower():
                self.tree.insert("", tk.END, values=(f"cat_{cat_id}", name, ""))

    def on_treeview_select(self, event):
        selected = self.tree.selection()
        if not selected:
            self.edit_meter_button.config(state="disabled")
            self.delete_meter_button.config(state="disabled")
            self.edit_cat_button.config(state="disabled")
            self.delete_cat_button.config(state="disabled")
            return
        item = self.tree.item(selected[0])["values"]
        if str(item[0]).startswith("cat_"):
            cat_id = int(item[0].split("_")[1])
            self.cursor.execute("SELECT name, parent_id FROM categories WHERE id=?", (cat_id,))
            cat = self.cursor.fetchone()
            self.cat_name_entry.delete(0, tk.END)
            self.cat_name_entry.insert(0, cat[0])
            parent_name = "Aucune"
            if cat[1]:
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
            self.cursor.execute("SELECT name, note, category_id FROM meters WHERE id=?", (meter_id,))
            meter = self.cursor.fetchone()
            if meter:
                self.meter_name.delete(0, tk.END)
                self.meter_name.insert(0, meter[0])
                self.meter_note.delete("1.0", tk.END)
                self.meter_note.insert("1.0", meter[1] if meter[1] else "")
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