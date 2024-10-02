import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import platform
import shutil  # Pour les opérations de copie et de déplacement

# Variables globales
selected_file = None
current_directory = "/"
directory_history = []  # Liste pour stocker l'historique des répertoires

# Fonction pour lister les fichiers dans le Treeview avec filtrage
def list_files(directory, filter_text=""):
    for item in tree.get_children():
        tree.delete(item)

    try:
        files = os.listdir(directory)

        # Appliquer le filtre texte si nécessaire
        if filter_text:
            files = [f for f in files if filter_text.lower() in f.lower()]

        # Affichage des fichiers dans le Treeview
        for filename in files:
            filepath = os.path.join(directory, filename)
            if os.path.isdir(filepath):
                tree.insert("", "end", text=filename, values=("Dossier", filepath))
            else:
                tree.insert("", "end", text=filename, values=("Fichier", filepath))
    except PermissionError:
        messagebox.showerror("Erreur", "Impossible d'accéder à ce répertoire.")

# Fonction pour afficher la popup d'information sur la nomenclature
def show_nomenclature_info():
    nomenclature_window = tk.Toplevel(root)
    nomenclature_window.title("Informations Nomenclature")
    nomenclature_window.geometry("400x400")
    
    info_text = tk.Text(nomenclature_window, wrap=tk.WORD, background="#E0E0E0", font=("Helvetica", 10))
    info_text.insert(tk.END, """
NOMENCLATURE
-Offres de prix-
ODP   : Offre de prix (reçu)
ODPST : Offre de prix sous-traitant
ODPCO : Offre de prix consommable
DEV   : Devis (émis)

-Commandes-
CMDST : Commande sous-traitant
ACRST : Accusé de réception sous-traitance
CMDCO : Commande consommable
ACRCO : Accusé de réception consommable

-Divers-
CRST  : Compte rendu sous-traitant
DAST  : Demande d'Agréement Sous Traitant
SECU  : Documents relatifs à la sécurité
CRM   : Compte-rendu maintenance
RMA   : Rapport mensuel activité
RTA   : Rapport trimestriel activité
RAA   : Rapport annuel activité
""")
    info_text.config(state=tk.DISABLED)  # Empêcher l'édition du texte
    info_text.pack(expand=True, fill=tk.BOTH)

# Fonction pour sélectionner un fichier/dossier dans le Treeview
def on_item_select(event):
    global selected_file
    selected_item = tree.selection()
    if selected_item:
        item = selected_item[0]
        file_type, path = tree.item(item, "values")
        if file_type == "Fichier":
            selected_file = path
            file_label.config(text=f"Sélectionné : {os.path.basename(selected_file)}")
        else:
            selected_file = None

def on_item_double_click(event):
    global current_directory, directory_history
    selected_item = tree.selection()[0]
    file_type, path = tree.item(selected_item, "values")
    
    if file_type == "Dossier":
        directory_history.append(current_directory)  # Ajouter le répertoire actuel à l'historique
        current_directory = path
        list_files(path)

# Fonction pour renommer le fichier avec les informations fournies
def rename_file():
    if not selected_file:
        messagebox.showwarning("Attention", "Aucun fichier sélectionné.")
        return

    year = year_entry.get()
    nomenclature = nomenclature_entry.get()
    emitter = emitter_entry.get()
    obj = object_entry.get()
    ref = ref_entry.get()

    if not (year and nomenclature and emitter and obj and ref):
        messagebox.showwarning("Attention", "Veuillez remplir toutes les cases.")
        return

    new_file_name = f"{year}-{nomenclature}-{emitter}-{obj}-{ref}{os.path.splitext(selected_file)[1]}"
    new_file_path = os.path.join(os.path.dirname(selected_file), new_file_name)

    try:
        os.rename(selected_file, new_file_path)
        messagebox.showinfo("Succès", f"Le fichier a été renommé en {new_file_name}.")
        file_label.config(text=f"Sélectionné : {os.path.basename(new_file_path)}")
        list_files(current_directory)  # Actualiser la liste des fichiers
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors du renommage : {e}")

# Fonction pour supprimer un fichier ou un dossier
def delete_file():
    if not selected_file:
        messagebox.showwarning("Attention", "Aucun fichier sélectionné.")
        return

    confirm = messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer ce fichier/dossier ?")
    if confirm:
        try:
            if os.path.isfile(selected_file):
                os.remove(selected_file)
            else:
                shutil.rmtree(selected_file)  # Supprimer les dossiers et leur contenu
            list_files(current_directory)
            messagebox.showinfo("Succès", "Le fichier/dossier a été supprimé.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la suppression : {e}")

# Fonction pour copier/déplacer un fichier
def copy_or_move_file(action):
    if not selected_file:
        messagebox.showwarning("Attention", "Aucun fichier sélectionné.")
        return

    target_directory = filedialog.askdirectory()
    if target_directory:
        try:
            if action == "copy":
                shutil.copy(selected_file, target_directory)
                messagebox.showinfo("Succès", "Le fichier a été copié.")
            elif action == "move":
                shutil.move(selected_file, target_directory)
                messagebox.showinfo("Succès", "Le fichier a été déplacé.")
            list_files(current_directory)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'opération : {e}")

# Fonction pour ouvrir le fichier avec le logiciel par défaut
def open_file():
    global selected_file
    if not selected_file:
        messagebox.showwarning("Attention", "Aucun fichier sélectionné.")
        return

    try:
        if platform.system() == "Windows":
            os.startfile(selected_file)
        elif platform.system() == "Darwin":
            subprocess.Popen(['open', selected_file])
        else:
            subprocess.Popen(['xdg-open', selected_file])
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de l'ouverture du fichier : {e}")

# Fonction pour revenir au dossier précédent
def go_back():
    global current_directory, directory_history
    if directory_history:
        current_directory = directory_history.pop()  # Récupère le dernier répertoire visité
        list_files(current_directory)

# Fonction pour ouvrir le navigateur de fichiers pour changer de répertoire de base
def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        global directory_history, current_directory
        directory_history.append(current_directory)  # Ajouter le répertoire actuel à l'historique
        current_directory = directory
        list_files(directory)

# Fonction pour filtrer les fichiers en fonction du texte saisi dans la barre de recherche
def filter_files(event=None):
    filter_text = search_entry.get().strip()  # Récupère le texte de recherche
    list_files(current_directory, filter_text)

# Fenêtre principale
root = tk.Tk()
root.title("Gestionnaire de Fichiers")
root.geometry("1280x720")

# Volet supérieur
frame_top = ttk.Frame(root)
frame_top.pack(padx=10, pady=10, fill=tk.X)

# Barre de recherche pour filtrer les fichiers
ttk.Label(frame_top, text="Recherche de fichiers :").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
search_entry = ttk.Entry(frame_top)
search_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
search_entry.bind("<KeyRelease>", filter_files)

# Bouton "Retour" pour revenir au répertoire précédent
back_button = ttk.Button(frame_top, text="Retour", command=go_back)
back_button.grid(row=0, column=2, padx=5, pady=5)

# Bouton "Naviguer" pour ouvrir le navigateur de fichiers
browse_button = ttk.Button(frame_top, text="Naviguer", command=browse_directory)
browse_button.grid(row=0, column=3, padx=5, pady=5)

# Ajouter une ligne de séparation sous la recherche de fichiers
separator_search = ttk.Separator(root, orient='horizontal')
separator_search.pack(fill='x', padx=10, pady=10)

# Champs texte pour renommer les fichiers
ttk.Label(frame_top, text="Année :").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
year_entry = ttk.Entry(frame_top)
year_entry.grid(row=1, column=1, padx=5, pady=5)

# Nomenclature avec bouton pour ouvrir la popup d'information
ttk.Label(frame_top, text="Nomenclature :").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
nomenclature_entry = ttk.Entry(frame_top)
nomenclature_entry.grid(row=1, column=3, padx=5, pady=5)

# Ajouter un bouton "?" pour ouvrir la popup d'informations sur la nomenclature
nomenclature_help_button = ttk.Button(frame_top, text="?", command=show_nomenclature_info)
nomenclature_help_button.grid(row=1, column=4, padx=5, pady=5)

# Autres champs de texte
ttk.Label(frame_top, text="Émetteur :").grid(row=1, column=5, padx=5, pady=5, sticky=tk.W)
emitter_entry = ttk.Entry(frame_top)
emitter_entry.grid(row=1, column=6, padx=5, pady=5)

ttk.Label(frame_top, text="Objet :").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
object_entry = ttk.Entry(frame_top)
object_entry.grid(row=2, column=1, padx=5, pady=5)

ttk.Label(frame_top, text="Référence :").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
ref_entry = ttk.Entry(frame_top)
ref_entry.grid(row=2, column=3, padx=5, pady=5)

# Bouton Renommer à la place des boutons Retour et Naviguer
rename_button = ttk.Button(frame_top, text="Renommer", command=rename_file)
rename_button.grid(row=2, column=6, padx=5, pady=5)

# Bouton "Ouvrir Fichier" à côté du bouton "Renommer"
open_button = ttk.Button(frame_top, text="Ouvrir Fichier", command=open_file)
open_button.grid(row=2, column=7, padx=5, pady=5)

# Sélectionné : fichier
file_label = ttk.Label(frame_top, text="Aucun fichier sélectionné")
file_label.grid(row=2, column=8, padx=5, pady=5)

# Ajouter une ligne de séparation entre la barre de navigation et le reste
separator = ttk.Separator(root, orient='horizontal')
separator.pack(fill='x', padx=10, pady=10)

# Volet pour le Treeview (fichiers et dossiers)
frame_right = ttk.Frame(root)
frame_right.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=True)

# Treeview pour afficher les fichiers et dossiers
tree = ttk.Treeview(frame_right, columns=("type"), show="tree")
tree.pack(fill=tk.BOTH, expand=True)
tree.bind("<ButtonRelease-1>", on_item_select)
tree.bind("<Double-1>", on_item_double_click)

# Nouveau volet pour les boutons "Supprimer", "Copier", "Déplacer", au-dessus du navigateur de fichiers
frame_buttons = ttk.Frame(root)
frame_buttons.pack(fill=tk.X, padx=10, pady=10)

# Boutons de gestion des fichiers
delete_button = ttk.Button(frame_buttons, text="Supprimer", command=delete_file)
delete_button.pack(side=tk.LEFT, padx=5, pady=5)

copy_button = ttk.Button(frame_buttons, text="Copier", command=lambda: copy_or_move_file("copy"))
copy_button.pack(side=tk.LEFT, padx=5, pady=5)

move_button = ttk.Button(frame_buttons, text="Déplacer", command=lambda: copy_or_move_file("move"))
move_button.pack(side=tk.LEFT, padx=5, pady=5)

# Initialisation sans sauvegarde des préférences utilisateur
list_files(current_directory)

root.mainloop()
