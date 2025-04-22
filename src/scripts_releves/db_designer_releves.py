import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import subprocess

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
    def __init__(self, parent, conn, conn_library):
        self.parent = parent
        self.conn = conn
        self.conn_library = conn_library  # Connexion à library.db
        self.cursor = self.conn.cursor()
        self.cursor_library = self.conn_library.cursor()
        self.zoom_factor = 1.0
        self.param_entries = []

        self.main_frame = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill="both", expand=True)

        # Canvas
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

        # Zoom
        self.zoom_frame = ttk.Frame(self.canvas_frame)
        self.zoom_frame.grid(row=2, column=0, pady=5)
        self.zoom_label = tk.Label(self.zoom_frame, text="Zoom : 100%")
        self.zoom_label.pack(side="left", padx=5)
        tk.Button(self.zoom_frame, text="Zoom +", command=lambda: self.zoom(1.1)).pack(side="left", padx=5)
        tk.Button(self.zoom_frame, text="Zoom -", command=lambda: self.zoom(0.9)).pack(side="left", padx=5)
        tk.Button(self.zoom_frame, text="100%", command=self.reset_zoom).pack(side="left", padx=5)

        # Formulaire
        self.config_frame = ttk.Frame(self.main_frame, width=300)
        self.main_frame.add(self.config_frame, weight=3)

        # Compteurs
        meter_frame = ttk.Frame(self.config_frame)
        meter_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(meter_frame, text="Compteur", font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(meter_frame, text="Nom :").pack(anchor="w")
        self.meter_name = tk.Entry(meter_frame)
        self.meter_name.pack(fill="x")
        tk.Label(meter_frame, text="Catégorie :").pack(anchor="w")
        self.meter_category = ttk.Combobox(meter_frame, state="readonly")
        self.meter_category.pack(fill="x")
        tk.Label(meter_frame, text="Note :").pack(anchor="w")
        self.meter_note = tk.Text(meter_frame, height=4)
        self.meter_note.pack(fill="x")
        tk.Label(meter_frame, text="Paramètres :").pack(anchor="w")
        self.params_frame = ttk.Frame(meter_frame)
        self.params_frame.pack(fill="x")
        ttk.Button(meter_frame, text="Ajouter Paramètre", command=self.add_param_entry).pack(pady=5)
        meter_buttons = ttk.Frame(meter_frame)
        meter_buttons.pack(fill="x")
        self.create_meter_btn = ttk.Button(meter_buttons, text="Créer", command=self.add_meter)
        self.create_meter_btn.pack(side="left", padx=5)
        self.edit_meter_btn = ttk.Button(meter_buttons, text="Modifier", command=self.edit_meter, state="disabled")
        self.edit_meter_btn.pack(side="left", padx=5)
        self.delete_meter_btn = ttk.Button(meter_buttons, text="Supprimer", command=self.delete_meter, state="disabled")
        self.delete_meter_btn.pack(side="left", padx=5)

        # Catégories
        ttk.Separator(self.config_frame, orient="horizontal").pack(fill="x", pady=10)
        cat_frame = ttk.Frame(self.config_frame)
        cat_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(cat_frame, text="Catégorie", font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(cat_frame, text="Nom :").pack(anchor="w")
        self.cat_name = tk.Entry(cat_frame)
        self.cat_name.pack(fill="x")
        tk.Label(cat_frame, text="Parent :").pack(anchor="w")
        self.cat_parent = ttk.Combobox(cat_frame, state="readonly")
        self.cat_parent.pack(fill="x")
        cat_buttons = ttk.Frame(cat_frame)
        cat_buttons.pack(fill="x")
        self.create_cat_btn = ttk.Button(cat_buttons, text="Créer", command=self.add_category)
        self.create_cat_btn.pack(side="left", padx=5)
        self.edit_cat_btn = ttk.Button(cat_buttons, text="Modifier", command=self.edit_category, state="disabled")
        self.edit_cat_btn.pack(side="left", padx=5)
        self.delete_cat_btn = ttk.Button(cat_buttons, text="Supprimer", command=self.delete_category, state="disabled")
        self.delete_cat_btn.pack(side="left", padx=5)

        # Treeview
        ttk.Separator(self.config_frame, orient="horizontal").pack(fill="x", pady=10)
        self.tree = ttk.Treeview(self.config_frame, columns=("ID", "Name", "Note"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Nom")
        self.tree.heading("Note", text="Note")
        self.tree.column("ID", width=50)
        self.tree.column("Name", width=150)
        self.tree.column("Note", width=100)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Variables pour l'arborescence interactive
        self.node_positions = {}
        self.meter_sizes = {}
        self.expanded_nodes = set()  # Suivre les nœuds dépliés
        self.dragging_node = None
        self.dragging_start = None
        self.level_positions = {}  # Suivre les positions Y par niveau pour l'alignement
        self.node_heights = {}  # Suivre les hauteurs des sous-arbres

        # Bindings pour interactions
        self.canvas.bind("<Button-1>", self.on_node_click)
        self.canvas.bind("<Double-1>", self.on_node_double_click)  # Double-clic pour déplier/replier ou ouvrir formulaire
        self.canvas.bind("<B1-Motion>", self.on_node_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_node_release)
        self.canvas.bind("<MouseWheel>", self.scroll_canvas)
        self.canvas.bind("<Button-4>", self.scroll_canvas)
        self.canvas.bind("<Button-5>", self.scroll_canvas)

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

    def add_param_entry(self):
        frame = ttk.Frame(self.params_frame)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Nom :").pack(side="left")
        name_entry = ttk.Entry(frame)
        name_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Label(frame, text="Min :").pack(side="left")
        target_entry = ttk.Entry(frame, width=10)
        target_entry.pack(side="left", padx=5)
        ttk.Label(frame, text="Max :").pack(side="left")
        max_entry = ttk.Entry(frame, width=10)
        max_entry.pack(side="left", padx=5)
        ttk.Label(frame, text="Unité :").pack(side="left")
        unit_entry = ttk.Entry(frame, width=10)
        unit_entry.pack(side="left", padx=5)
        self.param_entries.append((frame, name_entry, target_entry, max_entry, unit_entry))

    def update_ui(self):
        # Catégories
        self.cursor.execute("SELECT id, name, parent_id FROM categories")
        categories = self.cursor.fetchall()
        cat_names = ["Aucune"]
        self.cat_hierarchy = {"Aucune": None}
        for cat_id, name, parent_id in categories:
            hierarchy = []
            current_id = cat_id
            while current_id:
                self.cursor.execute("SELECT id, name, parent_id FROM categories WHERE id=?", (current_id,))
                cat = self.cursor.fetchone()
                if not cat:
                    break
                hierarchy.append(cat[1])
                current_id = cat[2]
            display_name = " > ".join(reversed(hierarchy))
            cat_names.append(display_name)
            self.cat_hierarchy[display_name] = cat_id
        self.meter_category["values"] = cat_names
        self.cat_parent["values"] = cat_names
        self.meter_category.set("Aucune")
        self.cat_parent.set("Aucune")

        # Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.cursor.execute("SELECT id, name, note FROM meters")
        for meter in self.cursor.fetchall():
            self.tree.insert("", tk.END, values=meter)
        self.cursor.execute("SELECT id, name FROM categories")
        for cat in self.cursor.fetchall():
            self.tree.insert("", tk.END, values=(f"cat_{cat[0]}", cat[1], ""))

        # Canvas - Arborescence interactive
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
        # Calculer la hauteur du nœud de la catégorie
        self.cursor.execute("SELECT name FROM categories WHERE id=?", (cat_id,))
        name = self.cursor.fetchone()[0]
        text_height = text_font.metrics("linespace") + 10
        height = max(30, text_height)

        # Si le nœud n'est pas déplié, sa hauteur est juste celle du nœud
        if cat_id not in self.expanded_nodes:
            self.node_heights[cat_id] = height + 40  # Espace minimal
            return self.node_heights[cat_id]

        # Calculer la hauteur des sous-catégories
        total_height = height + 40  # Hauteur du nœud + espace
        self.cursor.execute("SELECT id FROM categories WHERE parent_id=?", (cat_id,))
        subcats = self.cursor.fetchall()
        for subcat_id, in subcats:
            sub_height = self.calculate_subtree_height(subcat_id)
            total_height += sub_height

        # Calculer la hauteur des compteurs
        self.cursor.execute("SELECT id FROM meters WHERE category_id=? ORDER BY name", (cat_id,))
        meters = self.cursor.fetchall()
        for meter_id, in meters:
            _, meter_height = self.meter_sizes[meter_id]
            total_height += meter_height + 20  # Espace entre compteurs

        self.node_heights[cat_id] = total_height
        return total_height

    def draw_category_tree(self, cat_id, x_base, level):
        text_font = tk.font.Font(family="Arial", size=12, weight="bold")
        x_pos = x_base + level * 250  # Espacement horizontal entre niveaux

        # Initialiser la position Y pour ce niveau si nécessaire
        if level not in self.level_positions:
            self.level_positions[level] = 20
        y_pos = self.level_positions[level]

        # Dessiner le nœud de la catégorie
        self.cursor.execute("SELECT name FROM categories WHERE id=?", (cat_id,))
        name = self.cursor.fetchone()[0]
        text_width = text_font.measure(name) + 20
        text_height = text_font.metrics("linespace") + 10
        width = max(150, text_width)
        height = max(30, text_height)
        self.node_positions[(cat_id, "category")] = (x_pos, y_pos, width, height)

        # Mettre à jour la position Y pour le prochain nœud du même niveau
        self.level_positions[level] = y_pos + self.node_heights.get(cat_id, height + 40)

        # Si le nœud n'est pas déplié, on s'arrête ici
        if cat_id not in self.expanded_nodes:
            return

        # Dessiner les sous-catégories
        self.cursor.execute("SELECT id, name FROM categories WHERE parent_id=?", (cat_id,))
        subcats = self.cursor.fetchall()
        y_offset = y_pos + height + 40
        for subcat_id, _ in subcats:
            self.level_positions[level + 1] = y_offset
            self.draw_category_tree(subcat_id, x_base, level + 1)
            y_offset += self.node_heights.get(subcat_id, 0)

        # Dessiner les compteurs
        self.cursor.execute("SELECT id, name FROM meters WHERE category_id=? ORDER BY name", (cat_id,))
        meters = self.cursor.fetchall()
        meter_level = level + 1
        y_pos = y_offset if subcats else y_pos + height + 40
        self.level_positions[meter_level] = y_pos
        for meter_id, _ in meters:
            width, height = self.meter_sizes[meter_id]
            self.node_positions[(meter_id, "meter")] = (x_pos + 250, y_pos, width, height)
            self.cursor.execute("UPDATE meters SET x_pos=?, y_pos=? WHERE id=?", (x_pos + 250, y_pos, meter_id))
            y_pos += height + 20  # Espace entre compteurs
        if meters:
            self.level_positions[meter_level] = y_pos

    def draw_nodes(self):
        self.canvas.delete("all")
        # Dessiner les nœuds
        tooltips = []
        for (node_id, node_type), (x, y, width, height) in self.node_positions.items():
            if node_type == "category":
                fill_color = "#D3D3D3" if not self.cursor.execute("SELECT parent_id FROM categories WHERE id=?", (node_id,)).fetchone()[0] else "#ADD8E6"
                self.cursor.execute("SELECT name FROM categories WHERE id=?", (node_id,))
                name = self.cursor.fetchone()[0]
                prefix = "+" if node_id not in self.expanded_nodes else "-"
                # Aligner à gauche
                rect = self.canvas.create_rectangle(x, y - height/2, x + width, y + height/2, fill=fill_color, tags=f"cat_{node_id}")
                self.canvas.create_text(x + 10, y, text=f"{prefix} {name}", font=("Arial", 12, "bold"), anchor="w", tags=f"cat_{node_id}_text")
                # Ajouter une infobulle
                self.cursor.execute("SELECT COUNT(*) FROM meters WHERE category_id=?", (node_id,))
                meter_count = self.cursor.fetchone()[0]
                tooltip_text = f"Catégorie: {name}\nCompteurs: {meter_count}"
                tooltips.append(Tooltip(self.canvas, rect, tooltip_text))
            elif node_type == "meter":
                self.cursor.execute("SELECT name, note FROM meters WHERE id=?", (node_id,))
                name, note = self.cursor.fetchone()
                # Aligner à gauche
                rect = self.canvas.create_rectangle(x, y - height/2, x + width, y + height/2, fill="#FFC107", tags=f"meter_{node_id}")
                self.canvas.create_text(x + 10, y, text=name, font=("Arial", 10), anchor="w", tags=f"meter_{node_id}_text")
                # Ajouter une infobulle
                tooltip_text = f"Compteur: {name}\nNote: {note if note else 'Aucune'}"
                tooltips.append(Tooltip(self.canvas, rect, tooltip_text))

        # Dessiner les connexions avec des coudes
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
                    # Sélectionner la catégorie dans le Treeview
                    for tree_item in self.tree.get_children():
                        values = self.tree.item(tree_item)["values"]
                        if values and values[0] == f"cat_{cat_id}":
                            self.tree.selection_set(tree_item)
                            self.edit_category()  # Remplir le formulaire
                            break
                    self.dragging_node = (cat_id, "category")
                    self.dragging_start = (x, y)
                    return
                elif "meter_" in tags[0]:
                    meter_id = tags[0].split("_")[1]
                    # Sélectionner le compteur dans le Treeview
                    for tree_item in self.tree.get_children():
                        values = self.tree.item(tree_item)["values"]
                        if values and str(values[0]) == meter_id:
                            self.tree.selection_set(tree_item)
                            self.edit_meter()  # Remplir le formulaire
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
                    # Basculer l'état déplié/replié
                    if cat_id in self.expanded_nodes:
                        self.expanded_nodes.remove(cat_id)
                    else:
                        self.expanded_nodes.add(cat_id)
                    self.dragging_node = None  # Annuler le drag-and-drop
                    self.update_ui()
                    return
                elif "meter_" in tags[0]:
                    meter_id = tags[0].split("_")[1]
                    self.open_add_reading_window(meter_id)
                    return

    def open_add_reading_window(self, meter_id):
        # Créer une fenêtre popup pour ajouter un relevé
        popup = tk.Toplevel(self.parent)
        popup.title("Ajouter un Relevé")
        popup.transient(self.parent)
        popup.geometry("800x600")

        # Variables pour le formulaire
        parameter_var = tk.StringVar()
        day_var = tk.StringVar(value=f"{datetime.now().day:02d}")
        month_var = tk.StringVar(value=f"{datetime.now().month:02d}")
        year_var = tk.StringVar(value=str(datetime.now().year))
        value_var = tk.StringVar()
        note_var = tk.StringVar()
        library_file_id_var = tk.StringVar()  # Pour stocker l'ID du fichier
        file_title_var = tk.StringVar(value="Aucun fichier sélectionné")  # Pour afficher le titre

        # Formulaire
        form_frame = ttk.Frame(popup)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Compteur (affiché mais non modifiable)
        self.cursor.execute("SELECT name FROM meters WHERE id=?", (meter_id,))
        meter_name = self.cursor.fetchone()[0]
        ttk.Label(form_frame, text="Compteur :").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(form_frame, text=meter_name).grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="w")

        # Paramètre
        ttk.Label(form_frame, text="Paramètre :").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        parameter_combobox = ttk.Combobox(form_frame, textvariable=parameter_var, state="readonly", width=30)
        parameter_combobox.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        # Charger les paramètres pour ce compteur
        self.cursor.execute("SELECT id, name FROM parameters WHERE meter_id=?", (meter_id,))
        parameters = self.cursor.fetchall()
        param_names = [param_name for _, param_name in parameters]
        parameter_map = {param_name: param_id for param_id, param_name in parameters}
        parameter_combobox["values"] = param_names
        if param_names:
            parameter_var.set(param_names[0])

        # Date
        ttk.Label(form_frame, text="Date :").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        day_combobox = ttk.Combobox(form_frame, textvariable=day_var, values=[f"{i:02d}" for i in range(1, 32)], width=5, state="readonly")
        day_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        month_combobox = ttk.Combobox(form_frame, textvariable=month_var, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly")
        month_combobox.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        year_combobox = ttk.Combobox(form_frame, textvariable=year_var, values=[str(i) for i in range(2000, 2051)], width=7, state="readonly")
        year_combobox.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        # Valeur
        ttk.Label(form_frame, text="Valeur :").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        value_entry = ttk.Entry(form_frame, textvariable=value_var, width=30)
        value_entry.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Note
        ttk.Label(form_frame, text="Note :").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        note_entry = ttk.Entry(form_frame, textvariable=note_var, width=30)
        note_entry.grid(row=4, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Fichier joint
        ttk.Label(form_frame, text="Fichier :").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        file_label = ttk.Label(form_frame, textvariable=file_title_var)
        file_label.grid(row=5, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ttk.Button(form_frame, text="Associer Fichier", command=lambda: self.associate_file_popup(library_file_id_var, file_title_var)).grid(row=5, column=3, padx=5, pady=5)

        # Boutons
        buttons_frame = ttk.Frame(popup)
        buttons_frame.pack(fill="x", pady=10)
        ttk.Button(buttons_frame, text="Enregistrer", command=lambda: self.add_reading_from_popup(meter_id, parameter_var.get(), parameter_map, day_var.get(), month_var.get(), year_var.get(), value_var.get(), note_var.get(), library_file_id_var.get(), popup)).pack(side="right", padx=5)
        ttk.Button(buttons_frame, text="Annuler", command=popup.destroy).pack(side="right", padx=5)

        # Retarder l'appel à grab_set pour s'assurer que la fenêtre est rendue
        popup.after(100, lambda: self.set_popup_grab(popup))

    def set_popup_grab(self, popup):
        try:
            if popup.winfo_exists():
                popup.update_idletasks()
                popup.wait_visibility()
                popup.grab_set()
        except tk.TclError as e:
            print(f"Erreur lors de grab_set: {e}")

    def associate_file_popup(self, library_file_id_var, file_title_var):
        select_window = tk.Toplevel(self.parent)
        select_window.title("Sélectionner une pièce")
        select_window.geometry("800x600")
        select_window.transient(self.parent)
        select_window.grab_set()

        paned_window = ttk.PanedWindow(select_window, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        folder_frame = ttk.LabelFrame(paned_window, text="Dossiers")
        paned_window.add(folder_frame, weight=1)

        search_frame = ttk.Frame(folder_frame)
        search_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(search_frame, text="Catégorie :").pack(side="left")
        category_search_var = tk.StringVar()
        category_search_entry = ttk.Entry(search_frame, textvariable=category_search_var)
        category_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(search_frame, text="Projet :").pack(side="left")
        project_search_var = tk.StringVar()
        project_search_entry = ttk.Entry(search_frame, textvariable=project_search_var)
        project_search_entry.pack(side="left", fill="x", expand=True)

        folder_tree = ttk.Treeview(folder_frame, columns=("Year", "Category", "Project"), show="headings")
        folder_tree.heading("Year", text="Année")
        folder_tree.heading("Category", text="Catégorie")
        folder_tree.heading("Project", text="Projet")
        folder_tree.column("Year", width=100)
        folder_tree.column("Category", width=150)
        folder_tree.column("Project", width=200)
        folder_tree.pack(fill="both", expand=True, padx=5, pady=5)

        file_frame = ttk.LabelFrame(paned_window, text="Fichiers")
        paned_window.add(file_frame, weight=3)

        file_search_frame = ttk.Frame(file_frame)
        file_search_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(file_search_frame, text="Rechercher fichier :").pack(side="left")
        file_search_var = tk.StringVar()
        file_search_entry = ttk.Entry(file_search_frame, textvariable=file_search_var)
        file_search_entry.pack(side="left", fill="x", expand=True)

        file_tree = ttk.Treeview(file_frame, columns=("ID", "Title"), show="headings")
        file_tree.heading("ID", text="ID")
        file_tree.heading("Title", text="Titre")
        file_tree.column("ID", width=50)
        file_tree.column("Title", width=450)
        file_tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.cursor_library.execute("SELECT DISTINCT year, category, project FROM library WHERE file_path != '' OR title = '[Dossier]'")
        folder_data = self.cursor_library.fetchall()
        for row in folder_data:
            folder_tree.insert("", tk.END, values=row)

        def filter_folders(event=None):
            for item in folder_tree.get_children():
                folder_tree.delete(item)
            category_search = category_search_var.get().lower()
            project_search = project_search_var.get().lower()
            filtered_data = [
                row for row in folder_data
                if (not category_search or category_search in row[1].lower())
                and (not project_search or project_search in row[2].lower())
            ]
            for row in filtered_data:
                folder_tree.insert("", tk.END, values=row)

        def load_and_filter_files(event=None):
            for item in file_tree.get_children():
                file_tree.delete(item)
            selected = folder_tree.selection()
            if not selected:
                return
            year, category, project = folder_tree.item(selected[0])["values"]
            file_search = file_search_var.get().lower()
            self.cursor_library.execute("SELECT id, title FROM library WHERE year=? AND category=? AND project=? AND file_path != ''",
                                       (year, category, project))
            files = self.cursor_library.fetchall()
            filtered_files = [
                row for row in files
                if not file_search or file_search in row[1].lower()
            ]
            for row in filtered_files:
                file_tree.insert("", tk.END, values=row)

        category_search_entry.bind("<KeyRelease>", filter_folders)
        project_search_entry.bind("<KeyRelease>", filter_folders)
        file_search_entry.bind("<KeyRelease>", load_and_filter_files)
        folder_tree.bind("<<TreeviewSelect>>", load_and_filter_files)
        filter_folders()

        def apply_selection():
            file_selected = file_tree.selection()
            if not file_selected:
                messagebox.showwarning("Erreur", "Veuillez sélectionner une pièce.")
                return
            file_id = file_tree.item(file_selected[0])["values"][0]
            file_title = file_tree.item(file_selected[0])["values"][1]
            library_file_id_var.set(file_id)
            file_title_var.set(file_title)
            select_window.destroy()

        ttk.Button(select_window, text="Associer", command=apply_selection).pack(pady=5)
        ttk.Button(select_window, text="Annuler", command=select_window.destroy).pack(pady=5)

    def validate_date(self, year, month, day):
        try:
            year, month, day = int(year), int(month), int(day)
            if not (1 <= month <= 12):
                return False, "Mois doit être entre 1 et 12"
            import calendar
            days_in_month = calendar.monthrange(year, month)[1]
            if not (1 <= day <= days_in_month):
                return False, f"Jour doit être entre 1 et {days_in_month}"
            datetime(year, month, day)
            return True, ""
        except ValueError as e:
            return False, f"Date invalide : {str(e)}"

    def add_reading_from_popup(self, meter_id, param_name, parameter_map, day, month, year, value, note, library_file_id, popup):
        if not (param_name and day and month and year and value):
            messagebox.showwarning("Erreur", "Remplissez tous les champs requis (paramètre, date, valeur).")
            return
        is_valid, error_message = self.validate_date(year, month, day)
        if not is_valid:
            messagebox.showwarning("Erreur", f"Date invalide : {error_message}")
            return
        date = f"{year}-{month}-{day}"
        try:
            value = float(value)
            param_id = parameter_map.get(param_name)
            if not param_id:
                messagebox.showerror("Erreur", f"Paramètre {param_name} introuvable.")
                return
            self.cursor.execute("SELECT target, max_value FROM parameters WHERE id=?", (param_id,))
            result = self.cursor.fetchone()
            if not result:
                messagebox.showerror("Erreur", f"Paramètre {param_name} introuvable dans la base de données.")
                return
            min_val, max_val = result
            if min_val is not None and value < min_val:
                messagebox.showwarning("Attention", f"Valeur inférieure au minimum ({min_val}) !")
            elif max_val is not None and value > max_val:
                messagebox.showwarning("Attention", f"Valeur dépasse le maximum ({max_val}) !")
            # Convertir library_file_id en entier ou None
            library_file_id = int(library_file_id) if library_file_id else None
            # Enregistrer le relevé
            self.cursor.execute("INSERT INTO readings (meter_id, parameter_id, date, value, note, library_file_id) VALUES (?, ?, ?, ?, ?, ?)",
                               (meter_id, param_id, date, value, note, library_file_id))
            self.conn.commit()
            popup.destroy()
            messagebox.showinfo("Succès", "Relevé enregistré.")
        except ValueError:
            messagebox.showwarning("Erreur", "La valeur doit être un nombre.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def open_file(self, library_file_id):
        if not library_file_id:
            messagebox.showwarning("Erreur", "Aucun fichier associé à ouvrir.")
            return
        self.cursor_library.execute("SELECT file_path FROM library WHERE id=?", (library_file_id,))
        file_path_result = self.cursor_library.fetchone()
        if not file_path_result:
            messagebox.showerror("Erreur", "Fichier introuvable dans la bibliothèque.")
            return
        file_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "bibliotheque", file_path_result[0]))
        if file_path and os.path.exists(file_path):
            try:
                subprocess.run(['xdg-open', file_path], check=True)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier : {str(e)}")
        else:
            messagebox.showerror("Erreur", "Fichier introuvable.")

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

    def add_meter(self):
        name = self.meter_name.get()
        category = self.meter_category.get()
        note = self.meter_note.get("1.0", tk.END).strip()
        category_id = self.cat_hierarchy.get(category)
        if not name:
            messagebox.showwarning("Erreur", "Entrez un nom pour le compteur.")
            return
        self.cursor.execute("INSERT INTO meters (name, note, category_id) VALUES (?, ?, ?)", (name, note, category_id))
        meter_id = self.cursor.lastrowid
        for _, name_entry, target_entry, max_entry, unit_entry in self.param_entries:
            param_name = name_entry.get()
            target = target_entry.get()
            max_val = max_entry.get()
            unit = unit_entry.get()
            if param_name:
                try:
                    target = float(target) if target else None
                    max_val = float(max_val) if max_val else None
                except ValueError:
                    messagebox.showwarning("Erreur", "Min et Max doivent être des nombres ou vides.")
                    return
                self.cursor.execute("INSERT INTO parameters (meter_id, name, target, max_value, unit) VALUES (?, ?, ?, ?, ?)",
                                   (meter_id, param_name, target, max_val, unit))
        self.conn.commit()
        self.clear_meter_form()
        self.update_ui()

    def edit_meter(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Sélectionnez un compteur.")
            return
        item = self.tree.item(selected[0])["values"]
        if str(item[0]).startswith("cat_"):
            messagebox.showwarning("Erreur", "Sélectionnez un compteur.")
            return
        meter_id = item[0]
        self.cursor.execute("SELECT name, note, category_id FROM meters WHERE id=?", (meter_id,))
        name, note, category_id = self.cursor.fetchone()
        self.meter_name.delete(0, tk.END)
        self.meter_name.insert(0, name)
        self.meter_note.delete("1.0", tk.END)
        self.meter_note.insert("1.0", note)
        category_name = "Aucune"
        if category_id:
            for display_name, c_id in self.cat_hierarchy.items():
                if c_id == category_id:
                    category_name = display_name
                    break
        self.meter_category.set(category_name)
        self.clear_params()
        self.cursor.execute("SELECT id, name, target, max_value, unit FROM parameters WHERE meter_id=?", (meter_id,))
        for param_id, param_name, target, max_val, unit in self.cursor.fetchall():
            self.add_param_entry()
            frame, name_entry, target_entry, max_entry, unit_entry = self.param_entries[-1]
            name_entry.insert(0, param_name)
            if target is not None:
                target_entry.insert(0, str(target))
            if max_val is not None:
                max_entry.insert(0, str(max_val))
            if unit:
                unit_entry.insert(0, unit)
            frame.param_id = param_id
        self.create_meter_btn.config(text="Sauvegarder", command=lambda: self.save_meter_edit(meter_id))

    def save_meter_edit(self, meter_id):
        name = self.meter_name.get()
        category = self.meter_category.get()
        note = self.meter_note.get("1.0", tk.END).strip()
        category_id = self.cat_hierarchy.get(category)
        if not name:
            messagebox.showwarning("Erreur", "Entrez un nom pour le compteur.")
            return

        self.cursor.execute("UPDATE meters SET name=?, note=?, category_id=? WHERE id=?", (name, note, category_id, meter_id))

        existing_params = {param_id: param_name for param_id, param_name in self.cursor.execute("SELECT id, name FROM parameters WHERE meter_id=?", (meter_id,)).fetchall()}
        existing_param_ids = set(existing_params.keys())

        new_params = []
        for frame, name_entry, target_entry, max_entry, unit_entry in self.param_entries:
            param_name = name_entry.get()
            target = target_entry.get()
            max_val = max_entry.get()
            unit = unit_entry.get()
            if param_name:
                try:
                    target = float(target) if target else None
                    max_val = float(max_val) if max_val else None
                except ValueError:
                    messagebox.showwarning("Erreur", "Min et Max doivent être des nombres ou vides.")
                    return
                param_id = getattr(frame, 'param_id', None)
                new_params.append((param_id, param_name, target, max_val, unit))

        new_param_ids = set()
        for param_id, param_name, target, max_val, unit in new_params:
            if param_id and param_id in existing_param_ids:
                self.cursor.execute("UPDATE parameters SET name=?, target=?, max_value=?, unit=? WHERE id=?",
                                   (param_name, target, max_val, unit, param_id))
                new_param_ids.add(param_id)
            else:
                self.cursor.execute("INSERT INTO parameters (meter_id, name, target, max_value, unit) VALUES (?, ?, ?, ?, ?)",
                                   (meter_id, param_name, target, max_val, unit))
                new_param_ids.add(self.cursor.lastrowid)

        params_to_delete = existing_param_ids - new_param_ids
        for param_id in params_to_delete:
            self.cursor.execute("SELECT COUNT(*) FROM readings WHERE parameter_id=?", (param_id,))
            count = self.cursor.fetchone()[0]
            if count > 0:
                messagebox.showwarning("Attention", f"Le paramètre '{existing_params[param_id]}' est utilisé dans {count} relevé(s) existant(s). Il sera conservé pour éviter de casser les relevés.")
            else:
                self.cursor.execute("DELETE FROM parameters WHERE id=?", (param_id,))

        self.conn.commit()
        self.clear_meter_form()
        self.create_meter_btn.config(text="Créer", command=self.add_meter)
        self.update_ui()

    def delete_meter(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Sélectionnez un compteur.")
            return
        item = self.tree.item(selected[0])["values"]
        if str(item[0]).startswith("cat_"):
            messagebox.showwarning("Erreur", "Sélectionnez un compteur.")
            return
        meter_id = item[0]
        if messagebox.askyesno("Confirmation", "Supprimer ce compteur et ses relevés ?"):
            self.cursor.execute("DELETE FROM parameters WHERE meter_id=?", (meter_id,))
            self.cursor.execute("DELETE FROM readings WHERE meter_id=?", (meter_id,))
            self.cursor.execute("DELETE FROM meters WHERE id=?", (meter_id,))
            self.conn.commit()
            self.clear_meter_form()
            self.update_ui()

    def add_category(self):
        name = self.cat_name.get()
        parent = self.cat_parent.get()
        parent_id = self.cat_hierarchy.get(parent)
        if not name:
            messagebox.showwarning("Erreur", "Entrez un nom pour la catégorie.")
            return
        self.cursor.execute("SELECT id FROM categories WHERE name=?", (name,))
        if self.cursor.fetchone():
            messagebox.showwarning("Erreur", "Une catégorie avec ce nom existe déjà.")
            return
        level = 0
        current_parent = parent_id
        while current_parent:
            self.cursor.execute("SELECT parent_id FROM categories WHERE id=?", (current_parent,))
            current_parent = self.cursor.fetchone()[0]
            level += 1
        if level >= 5:
            messagebox.showwarning("Erreur", "Limite de 5 niveaux de sous-catégories atteinte.")
            return
        self.cursor.execute("INSERT INTO categories (name, parent_id) VALUES (?, ?)", (name, parent_id))
        self.conn.commit()
        self.cat_name.delete(0, tk.END)
        self.cat_parent.set("Aucune")
        self.update_ui()

    def edit_category(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Sélectionnez une catégorie.")
            return
        item = self.tree.item(selected[0])["values"]
        if not str(item[0]).startswith("cat_"):
            messagebox.showwarning("Erreur", "Sélectionnez une catégorie.")
            return
        cat_id = int(item[0].split("_")[1])
        self.cursor.execute("SELECT name, parent_id FROM categories WHERE id=?", (cat_id,))
        name, parent_id = self.cursor.fetchone()
        self.cat_name.delete(0, tk.END)
        self.cat_name.insert(0, name)
        parent_name = "Aucune"
        if parent_id:
            for display_name, c_id in self.cat_hierarchy.items():
                if c_id == parent_id:
                    parent_name = display_name
                    break
        self.cat_parent.set(parent_name)
        self.create_cat_btn.config(text="Sauvegarder", command=lambda: self.save_category_edit(cat_id))

    def save_category_edit(self, cat_id):
        name = self.cat_name.get()
        parent = self.cat_parent.get()
        parent_id = self.cat_hierarchy.get(parent)
        if not name:
            messagebox.showwarning("Erreur", "Entrez un nom pour la catégorie.")
            return
        self.cursor.execute("SELECT id FROM categories WHERE name=? AND id!=?", (name, cat_id))
        if self.cursor.fetchone():
            messagebox.showwarning("Erreur", "Une catégorie avec ce nom existe déjà.")
            return
        level = 0
        current_parent = parent_id
        while current_parent:
            self.cursor.execute("SELECT parent_id FROM categories WHERE id=?", (current_parent,))
            current_parent = self.cursor.fetchone()[0]
            level += 1
        if level >= 5:
            messagebox.showwarning("Erreur", "Limite de 5 niveaux de sous-catégories atteinte.")
            return
        self.cursor.execute("UPDATE categories SET name=?, parent_id=? WHERE id=?", (name, parent_id, cat_id))
        self.conn.commit()
        self.cat_name.delete(0, tk.END)
        self.cat_parent.set("Aucune")
        self.create_cat_btn.config(text="Créer", command=self.add_category)
        self.update_ui()

    def delete_category(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Erreur", "Sélectionnez une catégorie.")
            return
        item = self.tree.item(selected[0])["values"]
        if not str(item[0]).startswith("cat_"):
            messagebox.showwarning("Erreur", "Sélectionnez une catégorie.")
            return
        cat_id = int(item[0].split("_")[1])
        if messagebox.askyesno("Confirmation", "Supprimer cette catégorie et ses compteurs ?"):
            self.cursor.execute("SELECT id FROM meters WHERE category_id=?", (cat_id,))
            for meter in self.cursor.fetchall():
                self.cursor.execute("DELETE FROM parameters WHERE meter_id=?", (meter[0],))
                self.cursor.execute("DELETE FROM readings WHERE meter_id=?", (meter[0],))
            self.cursor.execute("DELETE FROM meters WHERE category_id=?", (cat_id,))
            self.cursor.execute("DELETE FROM categories WHERE id=?", (cat_id,))
            self.conn.commit()
            self.update_ui()

    def clear_meter_form(self):
        self.meter_name.delete(0, tk.END)
        self.meter_note.delete("1.0", tk.END)
        self.meter_category.set("Aucune")
        self.clear_params()

    def clear_params(self):
        for frame, _, _, _, _ in self.param_entries:
            frame.destroy()
        self.param_entries.clear()

    def on_tree_select(self, event):
        selected = self.tree.selection()
        self.edit_meter_btn.config(state="disabled")
        self.delete_meter_btn.config(state="disabled")
        self.edit_cat_btn.config(state="disabled")
        self.delete_cat_btn.config(state="disabled")
        if selected:
            item = self.tree.item(selected[0])["values"]
            if str(item[0]).startswith("cat_"):
                self.edit_cat_btn.config(state="normal")
                self.delete_cat_btn.config(state="normal")
            else:
                self.edit_meter_btn.config(state="normal")
                self.delete_meter_btn.config(state="normal")