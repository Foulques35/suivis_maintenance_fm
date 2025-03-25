import tkinter as tk
from tkinter import ttk
import os

# Importez les classes modifiées des applications
from applications.commande_devis_manager import CommandeApp, DevisApp
from applications.archiviste import EventRegisterApp
from applications.stock_manager import StockApp

class MainInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interface Multi-Applications")
        self.geometry("1280x800")

        # Appliquer le thème "clam"
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", font=("Helvetica", 10))
        style.configure("TButton", font=("Helvetica", 10), padding=5)
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        style.configure("Treeview", rowheight=25)

        # Définir le répertoire de base
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Création du Notebook pour les onglets
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Ajouter les applications dans les onglets
        self.add_app_tab(CommandeApp, "Suivi des Commandes", self.base_dir)
        self.add_app_tab(DevisApp, "Suivi des Devis", self.base_dir)
        self.add_app_tab(EventRegisterApp, "Registre Archiviste", self.base_dir)
        self.add_app_tab(StockApp, "Gestion de Stock", self.base_dir)

    def add_app_tab(self, app_class, title, base_dir):
        """Ajoute un onglet avec l'application donnée."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=title)
        
        # Instancier l'application dans le frame avec le base_dir
        app_instance = app_class(frame, base_dir)
        app_instance.pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    app = MainInterface()
    app.mainloop()