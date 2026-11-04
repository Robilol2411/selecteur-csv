"""Sélecteur CSV : choisir jusqu'à 12 fichiers CSV, cocher des options, lancer un graphique.

Fenêtre Tkinter avec :
  - une grille de 12 cases (clic gauche = parcourir, clic droit = vider) ;
  - trois lignes d'options à cocher : statut, programme, nombre de messages ;
  - une rangée de boutons, un par graphique déclaré dans GRAPHIQUES.

Chaque bouton lance le script du graphique dans un processus à part, sous la forme :
    python graphique_1.py --statuts internes --programmes A B --nombres 26+ -- a.csv b.csv

Usage :
    python main.py               # fenêtre vide
    python main.py a.csv b.csv   # fenêtre pré-remplie avec ces fichiers
"""
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

DOSSIER = Path(__file__).parent

# Boutons de lancement : texte du bouton -> script à exécuter.
# Adapte les chemins à ton arborescence ; ajoute une ligne par graphique.
GRAPHIQUES = {
    "Graphique 1": DOSSIER / "graphique_1.py",
}

# Lignes d'options : (titre affiché, nom de l'argument passé au graphique, valeurs à cocher).
# Les valeurs sont transmises telles quelles au script du graphique.
OPTIONS = [
    ("Statut", "statuts", ["internes", "partenaires"]),
    ("Programme", "programmes", ["A", "B", "C", "D"]),
    ("Messages", "nombres", ["0-10", "11-25", "26+"]),
]

NB_CASES = 12
COLONNES = 4


class Selecteur(tk.Tk):
    """Fenêtre principale : grille de fichiers, options à cocher et boutons de lancement."""

    def __init__(self):
        """Construit la fenêtre et pré-remplit la grille avec les CSV passés en argument."""
        super().__init__()
        self.title("Sélecteur CSV")
        self.configure(bg="white")
        self.geometry("900x620")
        self.fichiers = [None] * NB_CASES
        # nom d'argument -> {valeur: BooleanVar}
        self.coches = {}

        tk.Label(self, text="Sélecteur CSV", font=("Segoe UI", 16, "bold"),
                 bg="white").pack(anchor="w", padx=20, pady=(16, 0))
        tk.Label(self, text="Clic sur une case pour parcourir, clic droit pour vider.",
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
        cadre.pack(fill="x", padx=20, pady=(0, 8))
        for ligne, (titre, argument, valeurs) in enumerate(OPTIONS):
            tk.Label(cadre, text=titre, width=10, anchor="w", bg="white",
                     font=("Segoe UI", 10, "bold")).grid(row=ligne, column=0, sticky="w", pady=2)
            self.coches[argument] = {}
            for col, valeur in enumerate(valeurs, start=1):
                var = tk.BooleanVar(value=True)
                tk.Checkbutton(cadre, text=valeur, variable=var, bg="white",
                               activebackground="white").grid(row=ligne, column=col, sticky="w", padx=(0, 12))
                self.coches[argument][valeur] = var

    def creer_pied(self):
        """Crée le compteur de fichiers et les boutons (un par graphique + Tout effacer)."""
        pied = tk.Frame(self, bg="white")
        pied.pack(fill="x", padx=20, pady=(0, 16))
        self.message = tk.Label(pied, fg="#777", bg="white")
        self.message.pack(side="left")
        for nom in reversed(list(GRAPHIQUES)):
            ttk.Button(pied, text=nom, command=lambda n=nom: self.lancer(n)).pack(side="right", padx=(8, 0))
        ttk.Button(pied, text="Tout effacer", command=self.tout_effacer).pack(side="right")

    # --- gestion des fichiers ---------------------------------------------------------

    def rafraichir(self):
        """Met à jour le texte et la couleur des cases, puis le compteur de fichiers."""
        for i, (chemin, case) in enumerate(zip(self.fichiers, self.cases)):
            if chemin:
                case.config(text=f"{i + 1}. {Path(chemin).name}", fg="#222", bg="white",
                            highlightbackground="#2b6cb0")
            else:
                case.config(text=f"{i + 1}. vide", fg="#999", bg="#f6f6f6",
                            highlightbackground="#d0d0d0")
        self.message.config(text=f"{sum(1 for f in self.fichiers if f)} / {NB_CASES} fichier(s)")

    def ajouter(self, chemins):
        """Place les chemins .csv donnés dans les cases libres ; signale ceux qui ne rentrent pas."""
        csv = [c for c in chemins if c.lower().endswith(".csv")]
        vides = [i for i, f in enumerate(self.fichiers) if f is None]
        for i, chemin in zip(vides, csv):
            self.fichiers[i] = chemin
        self.rafraichir()
        if len(csv) > len(vides):
            self.message.config(text=f"{len(csv) - len(vides)} fichier(s) ignoré(s) : plus de case libre")

    def parcourir(self, i):
        """Ouvre la boîte de dialogue Windows pour choisir le CSV de la case i."""
        chemin = filedialog.askopenfilename(title="Choisir un CSV", filetypes=[("Fichiers CSV", "*.csv")])
        if chemin:
            self.fichiers[i] = chemin
            self.rafraichir()

    def vider(self, i):
        """Vide la case i."""
        self.fichiers[i] = None
        self.rafraichir()

    def tout_effacer(self):
        """Vide toutes les cases."""
        self.fichiers = [None] * NB_CASES
        self.rafraichir()

    # --- lancement des graphiques -----------------------------------------------------

    def options_cochees(self):
        """Renvoie {argument: [valeurs cochées]} pour chaque ligne d'options."""
        return {arg: [v for v, var in vars_.items() if var.get()] for arg, vars_ in self.coches.items()}

    def lancer(self, nom):
        """Lance le graphique `nom` avec les options cochées et les fichiers choisis.

        Sans fichier choisi, le graphique utilise sa propre liste de fichiers par défaut.
        """
        options = self.options_cochees()
        manquantes = [titre for titre, arg, _ in OPTIONS if not options[arg]]
        if manquantes:
            self.message.config(text=f"Coche au moins une valeur : {', '.join(manquantes)}")
            return

        commande = [sys.executable, str(GRAPHIQUES[nom])]
        for arg, valeurs in options.items():
            commande += [f"--{arg}", *valeurs]
        chemins = [f for f in self.fichiers if f]
        commande += ["--", *chemins]

        subprocess.Popen(commande)
        source = f"{len(chemins)} fichier(s)" if chemins else "les fichiers par défaut"
        self.message.config(text=f"{nom} lancé avec {source}")


if __name__ == "__main__":
    Selecteur().mainloop()
