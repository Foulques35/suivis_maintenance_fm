import os
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser

class StockApp(tk.Frame):  # Changé de ttk.Frame à tk.Frame
    def __init__(self, parent, base_dir):
        super().__init__(parent)
        self.base_dir = base_dir
        self.DB_PATH = os.path.join(self.base_dir, "db/stock.db")  # Déplacé dans le dossier "db"
        self.FILES_DIR = os.path.join(self.base_dir, "Fichiers")

        # Initialisation
        self.init_db()
        self.create_files_dir()
        self.attachments = []

        # Configuration de l'interface
        self.configure(bg="white")  # Fonctionne maintenant avec tk.Frame
        style = ttk.Style(self)
        style.theme_use("clam")

        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(paned, width=800)  # 66% de 1200px
        paned.add(self.left_frame, weight=2)

        self.right_frame = ttk.Frame(paned, width=400)  # 33% de 1200px
        paned.add(self.right_frame, weight=1)

        # Recherche
        search_frame = ttk.LabelFrame(self.left_frame, text="Recherche", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        for label, var_name in [("Fournisseur", "search_supplier_var"), ("Référence", "search_ref_var"), 
                                ("Désignation", "search_design_var"), ("Notes", "search_notes_var")]:
            ttk.Label(search_frame, text=label).pack(side=tk.LEFT, padx=5)
            setattr(self, var_name, tk.StringVar())
            entry = ttk.Entry(search_frame, textvariable=getattr(self, var_name))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            entry.bind("<Return>", lambda e: self.search_stock())
            getattr(self, var_name).trace("w", lambda *args: self.search_stock())

        # Treeview
        self.stock_list = ttk.Treeview(self.left_frame, columns=("supplier", "reference", "designation", "notes", "stock", "attachments"),
                                       show="headings", height=20)
        self.stock_list.heading("supplier", text="Fournisseur", command=lambda: self.sort_column("supplier", False))
        self.stock_list.heading("reference", text="Référence", command=lambda: self.sort_column("reference", False))
        self.stock_list.heading("designation", text="Désignation", command=lambda: self.sort_column("designation", False))
        self.stock_list.heading("notes", text="Notes", command=lambda: self.sort_column("notes", False))
        self.stock_list.heading("stock", text="Stock", command=lambda: self.sort_column("stock", False))
        self.stock_list.heading("attachments", text="Fichiers joints", command=lambda: self.sort_column("attachments", False))
        self.stock_list.column("supplier", width=150, anchor="w", stretch=True)
        self.stock_list.column("reference", width=100, anchor="w", stretch=True)
        self.stock_list.column("designation", width=200, anchor="w", stretch=True)
        self.stock_list.column("notes", width=150, anchor="w", stretch=True)
        self.stock_list.column("stock", width=50, anchor="center", stretch=True)
        self.stock_list.column("attachments", width=150, anchor="w", stretch=True)
        self.stock_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.stock_list.bind("<ButtonRelease-1>", self.load_details)

        self.create_right_panel()
        self.load_stock()
        self.selected_item_id = None

    def init_db(self):
        # Créer le dossier "db" s'il n'existe pas
        db_dir = os.path.dirname(self.DB_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier TEXT NOT NULL,
            reference TEXT NOT NULL,
            designation TEXT NOT NULL,
            notes TEXT,
            stock INTEGER DEFAULT 0,
            attachments TEXT
        )''')
        for col in ["supplier", "reference", "designation", "stock"]:
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{col} ON stock({col});')
        conn.commit()
        conn.close()

    def create_files_dir(self):
        if not os.path.exists(self.FILES_DIR):
            os.makedirs(self.FILES_DIR)

    def create_right_panel(self):
        panel = ttk.LabelFrame(self.right_frame, text="Détails de l'Article", padding=10)
        panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Boutons d'action placés en haut
        action_frame = ttk.Frame(panel)
        action_frame.pack(fill=tk.X, pady=5)
        for text, cmd in [("Créer Nouveau", self.create_new), ("Enregistrer", self.save_item), ("Supprimer", self.delete_item)]:
            ttk.Button(action_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=5)

        # Champs
        for label, var_name in [("Fournisseur", "supplier_var"), ("Référence", "ref_var"), ("Désignation", "design_var")]:
            ttk.Label(panel, text=label).pack(anchor="w", pady=2)
            setattr(self, var_name, tk.StringVar())
            ttk.Entry(panel, textvariable=getattr(self, var_name)).pack(fill=tk.X, pady=2)

        ttk.Label(panel, text="Notes").pack(anchor="w", pady=2)
        self.notes_text = tk.Text(panel, height=4, font=("Helvetica", 10))
        self.notes_text.pack(fill=tk.X, pady=2)

        ttk.Label(panel, text="Stock").pack(anchor="w", pady=2)
        self.stock_var = tk.IntVar()
        ttk.Entry(panel, textvariable=self.stock_var).pack(fill=tk.X, pady=2)

        # Boutons Stock
        stock_btn_frame = ttk.Frame(panel)
        stock_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(stock_btn_frame, text="Retirer -1", command=self.decrement_stock).pack(side=tk.LEFT, padx=5)
        ttk.Button(stock_btn_frame, text="Ajouter +1", command=self.increment_stock).pack(side=tk.LEFT, padx=5)

        ttk.Label(panel, text="Fichiers Joints").pack(anchor="w", pady=2)
        self.attachment_listbox = tk.Listbox(panel, height=4, font=("Helvetica", 10))
        self.attachment_listbox.pack(fill=tk.X, pady=2)
        for text, cmd in [("Ajouter", self.add_attachments), ("Supprimer", self.remove_attachment), ("Ouvrir", self.open_attachment)]:
            ttk.Button(panel, text=f"{text} Fichier", command=cmd).pack(fill=tk.X, pady=2)

    def sort_column(self, col, reverse):
        data = [(self.stock_list.set(k, col), k) for k in self.stock_list.get_children('')]
        data.sort(key=lambda x: int(x[0]) if col == "stock" else x[0], reverse=reverse)
        for index, (val, k) in enumerate(data):
            self.stock_list.move(k, '', index)
        self.stock_list.heading(col, command=lambda: self.sort_column(col, not reverse))

    def load_stock(self):
        self.stock_list.delete(*self.stock_list.get_children())
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT supplier, reference, designation, notes, stock, attachments FROM stock ORDER BY supplier")
        for i, item in enumerate(cursor.fetchall()):
            tag = f"row{i}"
            self.stock_list.insert("", "end", values=item, tags=(tag,))
            self.stock_list.tag_configure(tag, background="#ffcccc" if item[4] == 0 else "#ffffff" if i % 2 == 0 else "#f0f0f0")
        conn.close()

    def search_stock(self):
        self.stock_list.delete(*self.stock_list.get_children())
        conn = sqlite3.connect(self.DB_PATH)
        query = "SELECT supplier, reference, designation, notes, stock, attachments FROM stock WHERE 1=1"
        params = []
        for var, col in [(self.search_supplier_var, "supplier"), (self.search_ref_var, "reference"), 
                         (self.search_design_var, "designation"), (self.search_notes_var, "notes")]:
            if var.get():
                query += f" AND LOWER({col}) LIKE LOWER(?)"
                params.append(f"%{var.get()}%")
        cursor = conn.cursor()
        cursor.execute(query, params)
        for i, item in enumerate(cursor.fetchall()):
            tag = f"row{i}"
            self.stock_list.insert("", "end", values=item, tags=(tag,))
            self.stock_list.tag_configure(tag, background="#ffcccc" if item[4] == 0 else "#ffffff" if i % 2 == 0 else "#f0f0f0")
        conn.close()

    def load_details(self, event):
        sel = self.stock_list.selection()
        if sel:
            values = self.stock_list.item(sel, "values")
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, supplier, reference, designation, notes, stock, attachments FROM stock WHERE supplier=? AND reference=? AND designation=?", 
                           (values[0], values[1], values[2]))
            item = cursor.fetchone()
            conn.close()
            if item:
                self.selected_item_id = item[0]
                self.supplier_var.set(item[1])
                self.ref_var.set(item[2])
                self.design_var.set(item[3])
                self.notes_text.delete("1.0", tk.END)
                self.notes_text.insert("1.0", item[4] if item[4] else "")
                self.stock_var.set(item[5])
                self.attachment_listbox.delete(0, tk.END)
                self.attachments = item[6].split(",") if item[6] and item[6] != "None" else []
                for att in self.attachments:
                    self.attachment_listbox.insert(tk.END, att)

    def save_item(self):
        supplier = self.supplier_var.get()
        reference = self.ref_var.get()
        designation = self.design_var.get()
        notes = self.notes_text.get("1.0", tk.END).strip()
        stock = self.stock_var.get()
        attachments = ",".join(self.attachments) if self.attachments else "None"

        if not all([supplier, reference, designation]):
            messagebox.showerror("Erreur", "Fournisseur, Référence et Désignation sont obligatoires")
            return

        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        if self.selected_item_id:
            cursor.execute("UPDATE stock SET supplier=?, reference=?, designation=?, notes=?, stock=?, attachments=? WHERE id=?",
                           (supplier, reference, designation, notes, stock, attachments, self.selected_item_id))
        else:
            cursor.execute("INSERT INTO stock (supplier, reference, designation, notes, stock, attachments) VALUES (?, ?, ?, ?, ?, ?)",
                           (supplier, reference, designation, notes, stock, attachments))
        conn.commit()
        conn.close()
        self.reset_form()
        self.search_stock()
        messagebox.showinfo("Succès", "Article sauvegardé")

    def create_new(self):
        self.selected_item_id = None
        self.save_item()

    def delete_item(self):
        if self.selected_item_id and messagebox.askyesno("Confirmation", "Supprimer cet article ?"):
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stock WHERE id=?", (self.selected_item_id,))
            conn.commit()
            conn.close()
            self.reset_form()
            self.search_stock()
            messagebox.showinfo("Succès", "Article supprimé")

    def reset_form(self):
        self.supplier_var.set("")
        self.ref_var.set("")
        self.design_var.set("")
        self.notes_text.delete("1.0", tk.END)
        self.stock_var.set(0)
        self.attachment_listbox.delete(0, tk.END)
        self.attachments = []
        self.selected_item_id = None

    def add_attachments(self):
        filepaths = filedialog.askopenfilenames()
        supplier = self.supplier_var.get()
        if not supplier:
            messagebox.showerror("Erreur", "Veuillez spécifier un fournisseur avant d'ajouter des fichiers")
            return
        supplier_dir = os.path.join(self.FILES_DIR, supplier)
        if not os.path.exists(supplier_dir):
            os.makedirs(supplier_dir)
        for filepath in filepaths:
            filename = os.path.basename(filepath)
            dest = os.path.join(supplier_dir, filename)
            os.rename(filepath, dest)
            if filename not in self.attachments:
                self.attachments.append(filename)
                self.attachment_listbox.insert(tk.END, filename)

    def remove_attachment(self):
        sel = self.attachment_listbox.curselection()
        if sel:
            filename = self.attachment_listbox.get(sel)
            self.attachments.remove(filename)
            self.attachment_listbox.delete(sel)

    def open_attachment(self):
        sel = self.attachment_listbox.curselection()
        if sel:
            filename = self.attachment_listbox.get(sel)
            supplier = self.supplier_var.get()
            filepath = os.path.join(self.FILES_DIR, supplier, filename)
            if os.path.exists(filepath):
                webbrowser.open(filepath)
            else:
                messagebox.showerror("Erreur", f"Fichier {filename} introuvable")

    def decrement_stock(self):
        current_stock = self.stock_var.get()
        if current_stock > 0:
            self.stock_var.set(current_stock - 1)
            self.save_item()

    def increment_stock(self):
        current_stock = self.stock_var.get()
        self.stock_var.set(current_stock + 1)
        self.save_item()

if __name__ == "__main__":
    # Pour tester standalone
    root = tk.Tk()
    root.title("Gestion de Stock")
    root.geometry("1200x800")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app = StockApp(root, base_dir)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()