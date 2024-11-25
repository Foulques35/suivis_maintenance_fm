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

# Fonction pour lancer P2 Commandes
def launch_p2_commandes():
    try:
        subprocess.Popen(["python", "p2-commandes.py"])
        #messagebox.showinfo("Succès", "P2 Commandes a été lancé avec succès !")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lancer P2 Commandes : {e}")

# Fonction pour lancer P5 Travaux
def launch_p5_travaux():
    try:
        subprocess.Popen(["python", "p5-travaux.py"])
        #messagebox.showinfo("Succès", "P5 Travaux a été lancé avec succès !")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lancer P5 Travaux : {e}")

# Fonction pour lancer Registre
def launch_registre():
    try:
        subprocess.Popen(["python", "registre.py"])
        #messagebox.showinfo("Succès", "Registre a été lancé avec succès !")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lancer Registre : {e}")

# Créer la fenêtre principale
root = tk.Tk()
root.title("Gestionnaire de Logiciels")
root.geometry("400x400")

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
title_label = tk.Label(root, text="Prohet Tilia", font=("Helvetica", 16, "bold"))
title_label.pack(pady=10)

# Boutons pour chaque logiciel
ttk.Button(root, text="Archiviste", command=launch_archiviste, width=20).pack(pady=5)
ttk.Button(root, text="P2 Commandes", command=launch_p2_commandes, width=20).pack(pady=5)
ttk.Button(root, text="P5 Travaux", command=launch_p5_travaux, width=20).pack(pady=5)
ttk.Button(root, text="Registre", command=launch_registre, width=20).pack(pady=5)

# Bouton Quitter
ttk.Button(root, text="Quitter", command=root.quit, width=20).pack(pady=20)

# Lancer la boucle principale
root.mainloop()
