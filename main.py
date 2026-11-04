"""Sélecteur CSV : choisir jusqu'à 12 fichiers « KPIs EMM », cocher des options, ouvrir une page de KPI.

Fenêtre Tkinter avec :
  - une grille de 12 cases (clic gauche = parcourir, clic droit = vider) ;
  - trois lignes d'options à cocher : statut, programme, nombre de messages ;
  - un bouton par page de KPI (voir graphiques.PAGES).

Seuls les fichiers nommés CS-IN_KPIs_EMM_<Mois>_<Année>.csv sont acceptés
(ex. CS-IN_KPIs_EMM_Septembre_2026.csv). Ils sont toujours rangés par date :
la case 1 contient le mois le plus ancien.

Options : une valeur cochée = une série à part ; rien de coché dans une ligne = tous confondus.

Chaque bouton lance graphiques.py dans un processus à part, sous la forme :
    python graphiques.py --page requetes --statuts internes --programmes A B --nombres -- a.csv b.csv

Usage :
    python main.py               # fenêtre vide
    python main.py a.csv b.csv   # fenêtre pré-remplie avec ces fichiers
"""
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

import kpi

DOSSIER = Path(__file__).parent

# Script qui dessine les pages : adapte le chemin si tu le déplaces.
SCRIPT = DOSSIER / "graphiques.py"

# Boutons : texte du bouton -> (nom de la page dans graphiques.py, lignes d'options utilisées).
BOUTONS = {
    "Vue d'ensemble": ("ensemble", ""),
    "Utilisateurs": ("utilisateurs", "statut, programme"),
    "Requêtes": ("requetes", "statut, programme"),
    "Requêtes / utilisateur": ("ratio", "statut, programme"),
    "Nb de messages": ("messages", "statut, programme, messages"),
}

# Lignes d'options : (titre affiché, argument passé à graphiques.py, valeurs à cocher).
OPTIONS = [
    ("Statut", "statuts", list(kpi.STATUTS)),
    ("Programme", "programmes", list(kpi.PROGRAMMES)),
    ("Messages", "nombres", list(kpi.NOMBRES)),
]

NB_CASES = 12
COLONNES = 4


class Selecteur(tk.Tk):
    """Fenêtre principale : grille de fichiers, options à cocher et boutons de pages."""

    def __init__(self):
        """Construit la fenêtre et pré-remplit la grille avec les CSV passés en argument."""
        super().__init__()
        self.title("Sélecteur CSV")
        self.configure(bg="white")
        self.geometry("900x660")
        self.fichiers = [None] * NB_CASES
        self.coches = {}  # argument -> {valeur: BooleanVar}

        tk.Label(self, text="Sélecteur CSV", font=("Segoe UI", 16, "bold"),
                 bg="white").pack(anchor="w", padx=20, pady=(16, 0))
        tk.Label(self, text="Clic sur une case pour parcourir, clic droit pour vider. "
                            "Fichiers : CS-IN_KPIs_EMM_<Mois>_<Année>.csv, rangés du plus ancien au plus récent.",
                 fg="#777", bg="white").pack(anchor="w", padx=20)

        self.creer_grille()
        self.creer_options()
        self.creer_pied()

        self.ajouter(sys.argv[1:])

    # --- construction de l'interface -------------------------------------------------

    def creer_grille(self):
        """Crée les 12 cases cliquables qui affichent les fichiers choisis."""
        grille = tk.Frame(self, bg="white")
        grille.pack(fill="both", expand=True, padx=14, pady=10)
        self.cases = []
        for i in range(NB_CASES):
            case = tk.Label(grille, bg="#f6f6f6", highlightthickness=1,
                            highlightbackground="#d0d0d0", cursor="hand2")
            case.grid(row=i // COLONNES, column=i % COLONNES, padx=6, pady=6, sticky="nsew")
            case.bind("<Button-1>", lambda e, i=i: self.parcourir(i))
            case.bind("<Button-3>", lambda e, i=i: self.vider(i))
            self.cases.append(case)
        for c in range(COLONNES):
            grille.columnconfigure(c, weight=1, uniform="c")
        for r in range(NB_CASES // COLONNES):
            grille.rowconfigure(r, weight=1, uniform="r")

    def creer_options(self):
        """Crée une ligne de cases à cocher par entrée de OPTIONS (tout est coché au départ)."""
        cadre = tk.Frame(self, bg="white")
        cadre.pack(fill="x", padx=20, pady=(0, 4))
        for ligne, (titre, argument, valeurs) in enumerate(OPTIONS):
            tk.Label(cadre, text=titre, width=10, anchor="w", bg="white",
                     font=("Segoe UI", 10, "bold")).grid(row=ligne, column=0, sticky="w", pady=2)
            self.coches[argument] = {}
            for col, valeur in enumerate(valeurs, start=1):
                var = tk.BooleanVar(value=True)
                tk.Checkbutton(cadre, text=valeur, variable=var, bg="white",
                               activebackground="white").grid(row=ligne, column=col, sticky="w", padx=(0, 12))
                self.coches[argument][valeur] = var
        tk.Label(self, text="Coché = une série à part · rien de coché dans une ligne = tous confondus.",
                 fg="#777", bg="white").pack(anchor="w", padx=20, pady=(0, 6))

    def creer_pied(self):
        """Crée la zone de message et la rangée de boutons (une page par bouton + Tout effacer)."""
        self.message = tk.Label(self, fg="#777", bg="white", anchor="w", justify="left", wraplength=860)
        self.message.pack(fill="x", padx=20)
        pied = tk.Frame(self, bg="white")
        pied.pack(fill="x", padx=20, pady=(4, 16))
        for texte, (page, utilise) in BOUTONS.items():
            bouton = ttk.Button(pied, text=texte, command=lambda p=page, t=texte: self.lancer(p, t))
            bouton.pack(side="left", padx=(0, 8))
            aide = f"{texte} : options {utilise}" if utilise else f"{texte} : chiffres globaux, sans options"
            bouton.bind("<Enter>", lambda e, a=aide: self.message.config(text=a))
            bouton.bind("<Leave>", lambda e: self.rafraichir())
        ttk.Button(pied, text="Tout effacer", command=self.tout_effacer).pack(side="right")

    # --- gestion des fichiers ---------------------------------------------------------

    def rafraichir(self):
        """Met à jour le texte et la couleur des cases, puis le compteur de fichiers."""
        for i, (chemin, case) in enumerate(zip(self.fichiers, self.cases)):
            if chemin:
                case.config(text=f"{i + 1}. {kpi.libelle_mois(chemin)}\n{Path(chemin).name}", fg="#222",
                            bg="white", highlightbackground="#2b6cb0")
            else:
                case.config(text=f"{i + 1}. vide", fg="#999", bg="#f6f6f6", highlightbackground="#d0d0d0")
        self.message.config(text=f"{sum(1 for f in self.fichiers if f)} / {NB_CASES} fichier(s)")

    def trier(self):
        """Range les fichiers par date (le plus ancien en case 1) et regroupe les cases vides à la fin."""
        presents = sorted((f for f in self.fichiers if f), key=kpi.date_du_fichier)
        self.fichiers = presents + [None] * (NB_CASES - len(presents))
        self.rafraichir()

    def ajouter(self, chemins, remplace=None):
        """Ajoute les CSV valides, rejette les autres, puis trie par date.

        `remplace` : indice d'une case dont on remplace le contenu (choix via « parcourir »).
        Un message résume les fichiers refusés : mauvais nom, mois déjà présent ou plus de case libre.
        """
        if remplace is not None:
            self.fichiers[remplace] = None
        refuses = []
        for chemin in chemins:
            date = kpi.date_du_fichier(chemin)
            if date is None:
                refuses.append(f"{Path(chemin).name} (nom invalide)")
            elif any(f and kpi.date_du_fichier(f) == date for f in self.fichiers):
                refuses.append(f"{Path(chemin).name} ({kpi.libelle_mois(chemin)} déjà présent)")
            elif None not in self.fichiers:
                refuses.append(f"{Path(chemin).name} (plus de case libre)")
            else:
                self.fichiers[self.fichiers.index(None)] = chemin
        self.trier()
        if refuses:
            self.message.config(text="Refusé : " + ", ".join(refuses))

    def parcourir(self, i):
        """Ouvre la boîte de dialogue Windows pour choisir le CSV de la case i (puis retrie)."""
        chemin = filedialog.askopenfilename(title="Choisir un CSV",
                                            filetypes=[("KPIs EMM", "CS-IN_KPIs_EMM_*.csv"), ("Fichiers CSV", "*.csv")])
        if chemin:
            self.ajouter([chemin], remplace=i)

    def vider(self, i):
        """Vide la case i (les fichiers suivants remontent d'une case)."""
        self.fichiers[i] = None
        self.trier()

    def tout_effacer(self):
        """Vide toutes les cases."""
        self.fichiers = [None] * NB_CASES
        self.rafraichir()

    # --- lancement des pages ----------------------------------------------------------

    def options_cochees(self):
        """Renvoie {argument: [valeurs cochées]} pour chaque ligne d'options."""
        return {arg: [v for v, var in vars_.items() if var.get()] for arg, vars_ in self.coches.items()}

    def lancer(self, page, texte):
        """Ouvre la page `page` avec les options cochées et les fichiers choisis (dans l'ordre des cases).

        Une ligne sans rien de coché est transmise vide : la page prend « tous confondus ».
        Sans fichier choisi, graphiques.py utilise sa propre liste de fichiers par défaut.
        """
        commande = [sys.executable, str(SCRIPT), "--page", page]
        for arg, valeurs in self.options_cochees().items():
            commande += [f"--{arg}", *valeurs]
        chemins = [f for f in self.fichiers if f]
        commande += ["--", *chemins]

        subprocess.Popen(commande)
        source = f"{len(chemins)} fichier(s)" if chemins else "les fichiers par défaut"
        self.message.config(text=f"{texte} : ouverture avec {source}…")


if __name__ == "__main__":
    Selecteur().mainloop()
