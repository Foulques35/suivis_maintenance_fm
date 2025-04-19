import tkinter as tk
from tkinter import ttk, messagebox

class DBDesigner:
    def __init__(self, parent, conn):
        self.parent = parent
        self.conn = conn
        self.cursor = self.conn.cursor()
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
        self.canvas.bind("<ButtonPress-1>", self.select_item)
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
        ttk.Label(frame, text="Min :").pack(side="left")  # Renommé "Cible" en "Min"
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

        # Canvas
        self.canvas.delete("all")
        self.cat_positions = {}
        x_pos = 20
        y_pos = 20
        self.cursor.execute("SELECT id, name, width, height FROM categories WHERE parent_id IS NULL")
        top_categories = self.cursor.fetchall()
        top_cat_ids = [cat[0] for cat in top_categories]
        for cat_id, name, width, height in top_categories:
            self.cat_positions[cat_id] = (x_pos, y_pos, x_pos + width, y_pos + height, width, height)
            self.cursor.execute("UPDATE categories SET x_pos=?, y_pos=? WHERE id=?", (x_pos, y_pos, cat_id))
            x_pos += width + 70

        for cat_id in top_cat_ids:
            self.calculate_category_height(cat_id)

        self.cursor.execute("SELECT id, name, x_pos, y_pos, width, height, parent_id FROM categories")
        categories = self.cursor.fetchall()
        for cat_id, name, x_pos, y_pos, width, height, parent_id in categories:
            level = 0
            current_parent = parent_id
            while current_parent:
                self.cursor.execute("SELECT parent_id FROM categories WHERE id=?", (current_parent,))
                current_parent = self.cursor.fetchone()[0]
                level += 1
            fill_color = "#D3D3D3" if parent_id is None else ["#ADD8E6", "#FFB6C1", "#98FB98", "#FFDAB9", "#E6E6FA"][min(level-1, 4)]
            self.canvas.create_rectangle(x_pos, y_pos, x_pos + width, y_pos + height, fill=fill_color, tags=f"cat_{cat_id}")
            self.canvas.create_text(x_pos + width/2, y_pos + 15, text=name, font=("Arial", 10, "bold"), tags=f"cat_{cat_id}_text")

        self.cursor.execute("SELECT id, name, category_id, x_pos, y_pos FROM meters")
        meters = self.cursor.fetchall()
        for meter_id, name, category_id, x_pos, y_pos in meters:
            x_pos = x_pos or 20
            y_pos = y_pos or 60
            self.canvas.create_rectangle(x_pos, y_pos, x_pos + 130, y_pos + 30, fill="#FFC107", tags=f"meter_{meter_id}")
            self.canvas.create_text(x_pos + 65, y_pos + 15, text=name, tags=f"meter_{meter_id}_text")

        self.canvas.configure(scrollregion=self.canvas.bbox("all") or (0, 0, 1000, 1000))

    def calculate_category_height(self, cat_id):
        if cat_id not in self.cat_positions:
            return 50
        x1, y1, x2, y2, width, height = self.cat_positions[cat_id]
        y_offset = y1 + 50

        self.cursor.execute("SELECT id, width, height FROM categories WHERE parent_id=?", (cat_id,))
        subcats = self.cursor.fetchall()
        for subcat_id, sub_width, sub_height in subcats:
            self.cat_positions[subcat_id] = (x1 + 10, y_offset, x1 + 10 + sub_width, y_offset + sub_height, sub_width, sub_height)
            self.cursor.execute("UPDATE categories SET x_pos=?, y_pos=? WHERE id=?", (x1 + 10, y_offset, subcat_id))
            sub_height = self.calculate_category_height(subcat_id)
            self.cat_positions[subcat_id] = (x1 + 10, y_offset, x1 + 10 + sub_width, y_offset + sub_height, sub_width, sub_height)
            self.cursor.execute("UPDATE categories SET x_pos=?, y_pos=?, height=? WHERE id=?", (x1 + 10, y_offset, sub_height, subcat_id))
            y_offset += sub_height + 10

        self.cursor.execute("SELECT id FROM meters WHERE category_id=?", (cat_id,))
        meters = self.cursor.fetchall()
        for meter_id in meters:
            meter_id = meter_id[0]
            self.cursor.execute("UPDATE meters SET x_pos=?, y_pos=? WHERE id=?", (x1 + 10, y_offset, meter_id))
            y_offset += 40

        new_height = max(50, y_offset - y1 + 10)
        self.cat_positions[cat_id] = (x1, y1, x2, y1 + new_height, width, new_height)
        self.cursor.execute("UPDATE categories SET height=? WHERE id=?", (new_height, cat_id))
        return new_height

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
                    messagebox.showwarning("Erreur", "Min et Max doivent être des nombres ou vides.")  # Renommé "Cible" en "Min"
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
                    messagebox.showwarning("Erreur", "Min et Max doivent être des nombres ou vides.")  # Renommé "Cible" en "Min"
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

    def select_item(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        items = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)
        for item in items:
            tags = self.canvas.gettags(item)
            if tags and "text" in tags[0]:
                if "meter" in tags[0]:
                    meter_id = tags[0].split("_")[1]
                    for tree_item in self.tree.get_children():
                        values = self.tree.item(tree_item)["values"]
                        if values and str(values[0]) == meter_id:
                            self.tree.selection_set(tree_item)
                            break
                elif "cat" in tags[0]:
                    cat_id = tags[0].split("_")[1]
                    for tree_item in self.tree.get_children():
                        values = self.tree.item(tree_item)["values"]
                        if values and values[0] == f"cat_{cat_id}":
                            self.tree.selection_set(tree_item)
                            break
                break