"""Sélecteur CSV : choisir jusqu'à 12 fichiers « KPIs EMM », cocher des options, lancer des graphiques.

Fenêtre Tkinter, de haut en bas :
  1. les graphiques à lancer (cases à cocher, plusieurs possibles) ;
  2. la grille de 12 fichiers (clic gauche = parcourir, clic droit = vider),
     avec dessous le rappel « * = obligatoire » et le bouton « Tout effacer » ;
  3. les options : Messages, Statut, Programme. Une * apparaît à côté d'une option
     quand un graphique coché l'exige (partie [ ] de son intitulé) ;
  4. le bouton « Lancer », qui ouvre chaque graphique coché.

Seuls les fichiers nommés CS-IN_KPIs_EMM_<Mois>_<Année>.csv sont acceptés
(ex. CS-IN_KPIs_EMM_Septembre_2026.csv). Ils sont toujours rangés par date :
la case 1 contient le mois le plus ancien.

Options : une valeur cochée = une série à part ; rien de coché dans une ligne = tous confondus
(interdit pour une option marquée *).

Chaque graphique est lancé dans un processus à part, sous la forme :
    python graphiques.py --graphique requetes --statuts internes --programmes A B --nombres -- a.csv b.csv

Usage :
    python main.py               # fenêtre vide
    python main.py a.csv b.csv   # fenêtre pré-remplie avec ces fichiers
"""
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

import donnees as d

DOSSIER = Path(__file__).parent

# Script qui dessine les graphiques : adapte le chemin si tu le déplaces.
SCRIPT = DOSSIER / "graphiques.py"

# Graphiques proposés en haut : texte affiché -> nom du graphique dans graphiques.py.
GRAPHIQUES = {
    "Nombre de messages": "messages",
    "Utilisateurs": "utilisateurs",
    "Requêtes": "requetes",
    "Chiffres globaux": "globaux",
}

# Options : (titre affiché, argument passé à graphiques.py, dimension dans donnees.py, valeurs).
OPTIONS = [
    ("Messages", "nombres", "nombre", list(d.NOMBRES)),
    ("Statut", "statuts", "statut", list(d.STATUTS)),
    ("Programme", "programmes", "programme", list(d.PROGRAMMES)),
]

NB_CASES = 12
COLONNES = 4
GRIS = "#777"


def dimensions_obligatoires(graphique):
    """Dimensions [ ] obligatoires pour un graphique (aucune pour « globaux »)."""
    return [] if graphique == "globaux" else d.obligatoires(graphique)


class Selecteur(tk.Tk):
    """Fenêtre principale : graphiques à lancer, grille de fichiers, options et bouton Lancer."""

    def __init__(self):
        """Construit la fenêtre de haut en bas et pré-remplit la grille avec les CSV passés en argument."""
        super().__init__()
        self.title("Sélecteur CSV")
        self.configure(bg="white")
        self.geometry("900x700")
        self.fichiers = [None] * NB_CASES
        self.choix_graphiques = {}  # graphique -> BooleanVar
        self.coches = {}            # argument -> {valeur: BooleanVar}
        self.titres_options = {}    # dimension -> Label du titre (pour l'étoile)

        tk.Label(self, text="Sélecteur CSV", font=("Segoe UI", 16, "bold"),
                 bg="white").pack(anchor="w", padx=20, pady=(16, 0))

        self.creer_graphiques()
        self.creer_grille()
        self.creer_sous_grille()
        self.creer_options()
        self.creer_pied()

        self.maj_etoiles()
        self.ajouter(sys.argv[1:])

    # --- construction de l'interface -------------------------------------------------

    def creer_graphiques(self):
        """Ligne du haut : une case à cocher par graphique (la première cochée au départ)."""
        cadre = tk.Frame(self, bg="white")
        cadre.pack(fill="x", padx=20, pady=(8, 0))
        tk.Label(cadre, text="Graphiques", width=10, anchor="w", bg="white",
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        for i, (texte, graphique) in enumerate(GRAPHIQUES.items()):
            var = tk.BooleanVar(value=(i == 0))
            tk.Checkbutton(cadre, text=texte, variable=var, command=self.maj_etoiles, bg="white",
                           activebackground="white").pack(side="left", padx=(0, 12))
            self.choix_graphiques[graphique] = var

    def creer_grille(self):
        """Grille des 12 cases cliquables qui affichent les fichiers choisis."""
        tk.Label(self, text="Clic sur une case pour parcourir, clic droit pour vider. "
                            "Fichiers : CS-IN_KPIs_EMM_<Mois>_<Année>.csv, rangés du plus ancien au plus récent.",
                 fg=GRIS, bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        grille = tk.Frame(self, bg="white")
        grille.pack(fill="both", expand=True, padx=14, pady=(4, 0))
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

    def creer_sous_grille(self):
        """Juste sous la grille : rappel des champs obligatoires (à gauche de) « Tout effacer »."""
        cadre = tk.Frame(self, bg="white")
        cadre.pack(fill="x", padx=20, pady=(2, 10))
        ttk.Button(cadre, text="Tout effacer", command=self.tout_effacer).pack(side="right")
        tk.Label(cadre, text="Les champs marqués d'une * sont obligatoires.", fg=GRIS,
                 bg="white").pack(side="right", padx=(0, 12))

    def creer_options(self):
        """Une ligne de cases à cocher par option (tout coché au départ) ; l'* est ajoutée par maj_etoiles."""
        cadre = tk.Frame(self, bg="white")
        cadre.pack(fill="x", padx=20)
        for ligne, (titre, argument, dimension, valeurs) in enumerate(OPTIONS):
            etiquette = tk.Label(cadre, text=titre, width=12, anchor="w", bg="white",
                                 font=("Segoe UI", 10, "bold"))
            etiquette.grid(row=ligne, column=0, sticky="w", pady=2)
            self.titres_options[dimension] = (etiquette, titre)
            self.coches[argument] = {}
            for col, valeur in enumerate(valeurs, start=1):
                var = tk.BooleanVar(value=True)
                tk.Checkbutton(cadre, text=valeur, variable=var, bg="white",
                               activebackground="white").grid(row=ligne, column=col, sticky="w", padx=(0, 12))
                self.coches[argument][valeur] = var
        tk.Label(self, text="Coché = une série à part · rien de coché = tous confondus (sauf champ *).",
                 fg=GRIS, bg="white").pack(anchor="w", padx=20, pady=(2, 0))

    def creer_pied(self):
        """Tout en bas : message d'état à gauche, bouton « Lancer » à droite."""
        pied = tk.Frame(self, bg="white")
        pied.pack(fill="x", padx=20, pady=(10, 16))
        ttk.Button(pied, text="Lancer", command=self.lancer).pack(side="right")
        self.message = tk.Label(pied, fg=GRIS, bg="white", anchor="w", justify="left", wraplength=760)
        self.message.pack(side="left", fill="x", expand=True)

    # --- étoiles des champs obligatoires ----------------------------------------------

    def graphiques_coches(self):
        """Noms des graphiques cochés en haut, dans l'ordre d'affichage."""
        return [g for g, var in self.choix_graphiques.items() if var.get()]

    def dimensions_requises(self):
        """Dimensions obligatoires pour au moins un des graphiques cochés."""
        return {dim for g in self.graphiques_coches() for dim in dimensions_obligatoires(g)}

    def maj_etoiles(self):
        """Ajoute « * » au titre des options exigées par les graphiques cochés, l'enlève sinon."""
        requises = self.dimensions_requises()
        for dimension, (etiquette, titre) in self.titres_options.items():
            etiquette.config(text=f"{titre} *" if dimension in requises else titre)

    # --- gestion des fichiers ---------------------------------------------------------

    def rafraichir(self):
        """Met à jour le texte et la couleur des cases, puis le compteur de fichiers."""
        for i, (chemin, case) in enumerate(zip(self.fichiers, self.cases)):
            if chemin:
                case.config(text=f"{i + 1}. {d.libelle_mois(chemin)}\n{Path(chemin).name}", fg="#222",
                            bg="white", highlightbackground="#2b6cb0")
            else:
                case.config(text=f"{i + 1}. vide", fg="#999", bg="#f6f6f6", highlightbackground="#d0d0d0")
        self.message.config(text=f"{sum(1 for f in self.fichiers if f)} / {NB_CASES} fichier(s)")

    def trier(self):
        """Range les fichiers par date (le plus ancien en case 1) et regroupe les cases vides à la fin."""
        presents = sorted((f for f in self.fichiers if f), key=d.date_du_fichier)
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
            date = d.date_du_fichier(chemin)
            if date is None:
                refuses.append(f"{Path(chemin).name} (nom invalide)")
            elif any(f and d.date_du_fichier(f) == date for f in self.fichiers):
                refuses.append(f"{Path(chemin).name} ({d.libelle_mois(chemin)} déjà présent)")
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

    # --- lancement --------------------------------------------------------------------

    def options_cochees(self):
        """Renvoie {argument: [valeurs cochées]} pour chaque ligne d'options."""
        return {arg: [v for v, var in vars_.items() if var.get()] for arg, vars_ in self.coches.items()}

    def lancer(self):
        """Vérifie les choix puis ouvre chaque graphique coché avec les options et les fichiers des cases.

        Refuse si aucun graphique n'est coché ou si une option marquée * n'a aucune valeur cochée.
        Sans fichier choisi, graphiques.py utilise sa propre liste de fichiers par défaut.
        """
        graphiques = self.graphiques_coches()
        if not graphiques:
            self.message.config(text="Coche au moins un graphique en haut.")
            return
        options = self.options_cochees()
        manquantes = [f"{titre} *" for titre, argument, dimension, _ in OPTIONS
                      if dimension in self.dimensions_requises() and not options[argument]]
        if manquantes:
            self.message.config(text="Coche au moins une valeur pour : " + ", ".join(manquantes))
            return

        chemins = [f for f in self.fichiers if f]
        for graphique in graphiques:
            commande = [sys.executable, str(SCRIPT), "--graphique", graphique]
            for argument, valeurs in options.items():
                commande += [f"--{argument}", *valeurs]
            subprocess.Popen(commande + ["--", *chemins])
        source = f"{len(chemins)} fichier(s)" if chemins else "les fichiers par défaut"
        self.message.config(text=f"{len(graphiques)} graphique(s) lancé(s) avec {source}.")


if __name__ == "__main__":
    Selecteur().mainloop()
