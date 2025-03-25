import tkinter as tk
from tkinter import filedialog, messagebox
import os
import zipfile

class ZipExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extracteur de ZIP en masse")
        self.root.geometry("500x300")

        # Variables pour stocker les chemins
        self.source_dir = tk.StringVar()
        self.dest_dir = tk.StringVar()

        # Création des éléments de l'interface
        # Label et bouton pour le dossier source
        tk.Label(root, text="Dossier contenant les ZIP :").pack(pady=5)
        tk.Entry(root, textvariable=self.source_dir, width=50).pack(pady=5)
        tk.Button(root, text="Choisir dossier source", command=self.select_source_dir).pack(pady=5)

        # Label et bouton pour le dossier destination
        tk.Label(root, text="Dossier de destination :").pack(pady=5)
        tk.Entry(root, textvariable=self.dest_dir, width=50).pack(pady=5)
        tk.Button(root, text="Choisir dossier destination", command=self.select_dest_dir).pack(pady=5)

        # Bouton pour lancer l'extraction
        tk.Button(root, text="Extraire tous les ZIP", command=self.extract_all_zips).pack(pady=20)

    def select_source_dir(self):
        """Ouvre une boîte de dialogue pour sélectionner le dossier source"""
        directory = filedialog.askdirectory()
        if directory:
            self.source_dir.set(directory)

    def select_dest_dir(self):
        """Ouvre une boîte de dialogue pour sélectionner le dossier destination"""
        directory = filedialog.askdirectory()
        if directory:
            self.dest_dir.set(directory)

    def extract_all_zips(self):
        """Extrait tous les fichiers ZIP du dossier source vers le dossier destination"""
        source = self.source_dir.get()
        dest = self.dest_dir.get()

        # Vérification des dossiers
        if not source or not dest:
            messagebox.showerror("Erreur", "Veuillez sélectionner les deux dossiers !")
            return

        if not os.path.exists(source):
            messagebox.showerror("Erreur", "Le dossier source n'existe pas !")
            return

        if not os.path.exists(dest):
            try:
                os.makedirs(dest)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de créer le dossier destination : {e}")
                return

        # Recherche et extraction des fichiers ZIP
        zip_count = 0
        try:
            for filename in os.listdir(source):
                if filename.lower().endswith('.zip'):
                    zip_path = os.path.join(source, filename)
                    try:
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            # Crée un sous-dossier avec le nom du ZIP (sans l'extension)
                            folder_name = os.path.splitext(filename)[0]
                            extract_path = os.path.join(dest, folder_name)
                            zip_ref.extractall(extract_path)
                        zip_count += 1
                    except zipfile.BadZipFile:
                        messagebox.showwarning("Attention", f"Le fichier {filename} est corrompu ou invalide")
                    except Exception as e:
                        messagebox.showerror("Erreur", f"Erreur lors de l'extraction de {filename} : {e}")

            if zip_count > 0:
                messagebox.showinfo("Succès", f"{zip_count} fichier(s) ZIP extrait(s) avec succès !")
            else:
                messagebox.showinfo("Info", "Aucun fichier ZIP trouvé dans le dossier source.")

        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ZipExtractorApp(root)
    root.mainloop()