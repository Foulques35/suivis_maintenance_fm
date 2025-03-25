import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
from PIL import Image, ImageTk  # Pour gérer le logo

# Fonction pour lancer Archiviste
def launch_archiviste():
    try:
        subprocess.Popen(["python", "archiviste.py"])
        #messagebox.showinfo("Succès", "Archiviste a été lancé avec succès !")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lancer Archiviste : {e}")

# Fonction pour lancer Commandes
def launch_notebook():
    try:
        subprocess.Popen(["python", "notebook.py"])
        #messagebox.showinfo("Succès", "Commandes a été lancé avec succès !")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lancer P2 Commandes : {e}")


# Fonction pour lancer Registre
def launch_registre():
    try:
        subprocess.Popen(["python", "registre-V2.py"])
        #messagebox.showinfo("Succès", "Registre a été lancé avec succès !")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lancer Registre : {e}")
        
# Fonction pour lancer Mails
def launch_mails():
    try:
        subprocess.Popen(["python", "mails.py"])
        #messagebox.showinfo("Succès", "Registre a été lancé avec succès !")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lancer Mails : {e}")
        
# Fonction pour lancer Archivision
def launch_archivision():
    try:
        subprocess.Popen(["python", "archivision.py"])
        #messagebox.showinfo("Succès", "Registre a été lancé avec succès !")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lancer Archivision : {e}")

# Créer la fenêtre principale
root = tk.Tk()
root.title("Projet-Archiviste")
root.geometry("400x500")

# Ajouter un logo (optionnel)
try:
    image = Image.open("logo.png")  # Remplacez "logo.png" par le chemin de votre logo
    image = image.resize((180, 100), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(image)
    logo_label = tk.Label(root, image=photo)
    logo_label.pack(pady=10)
except FileNotFoundError:
    print("Logo introuvable, il sera ignoré.")
except Exception as e:
    print(f"Erreur lors du chargement du logo : {e}")

# Ajouter un titre
title_label = tk.Label(root, text="Projet Archiviste", font=("Helvetica", 16, "bold"))
title_label.pack(pady=10)

# Boutons pour chaque logiciel
ttk.Button(root, text="Archiviste", command=launch_archiviste, width=20).pack(pady=5)
ttk.Button(root, text="Commandes", command=launch_notebook, width=20).pack(pady=5)
ttk.Button(root, text="Registre", command=launch_registre, width=20).pack(pady=5)
ttk.Button(root, text="Archivision", command=launch_archivision, width=20).pack(pady=5)
ttk.Button(root, text="Archives mails", command=launch_mails, width=20).pack(pady=5)

# Bouton Quitter
# ttk.Button(root, text="Quitter", command=root.quit, width=20).pack(pady=20)

# Lancer la boucle principale
root.mainloop()
