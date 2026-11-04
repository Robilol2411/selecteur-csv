"""Graphique 1 : barres groupées par intitulé, une barre par fichier (mois).

Garde seulement les lignes dont l'intitulé correspond aux options reçues
(statuts x programmes x nombres), dans cet ordre.

Usage (c'est main.py qui construit cette commande) :
    python graphique_1.py --statuts internes --programmes A B --nombres 26+ -- a.csv b.csv
Sans fichier, on utilise la liste FICHIERS ci-dessous.
"""
import argparse
import webbrowser
from pathlib import Path

import altair as alt
import pandas as pd

DOSSIER = Path(__file__).parent

# Fichiers utilisés quand main.py n'en envoie aucun : adapte le chemin.
FICHIERS = [DOSSIER / "exemples" / f"{m}.csv" for m in ("janvier", "fevrier", "mars", "avril")]

# Modèle d'intitulé tel qu'il apparaît dans la 1re colonne des CSV.
MODELE = "Nombre d'utilisateur(s) {statut} {programme} avec {nombre} messages"

# Option cochée dans main.py -> texte réellement écrit dans les CSV.
# Adapte la partie de droite à tes vrais intitulés.
STATUTS = {"internes": "internes", "partenaires": "partenaires"}
PROGRAMMES = {"A": "A", "B": "B", "C": "C", "D": "D"}
NOMBRES = {"0-10": "0-10", "11-25": "11-25", "26+": "26+"}


def lire_arguments():
    """Lit les options et les fichiers passés en ligne de commande."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--statuts", nargs="+", default=list(STATUTS))
    p.add_argument("--programmes", nargs="+", default=list(PROGRAMMES))
    p.add_argument("--nombres", nargs="+", default=list(NOMBRES))
    p.add_argument("fichiers", nargs="*")
    return p.parse_args()


def intitules_voulus(args):
    """Construit la liste ordonnée des intitulés à afficher à partir des options."""
    return [MODELE.format(statut=STATUTS[s], programme=PROGRAMMES[p], nombre=NOMBRES[n])
            for s in args.statuts for p in args.programmes for n in args.nombres]


def lire(chemin):
    """Lit un CSV à deux colonnes (intitulé, valeur) ; séparateur , ou ; détecté seul."""
    try:
        df = pd.read_csv(chemin, sep=None, engine="python", encoding="utf-8-sig")
    except UnicodeDecodeError:  # CSV enregistré par Excel
        df = pd.read_csv(chemin, sep=None, engine="python", encoding="latin-1")
    df = df.iloc[:, :2]
    df.columns = ["intitule", "valeur"]
    df["intitule"] = df["intitule"].astype(str).str.strip()
    df["valeur"] = pd.to_numeric(df["valeur"].astype(str).str.replace(",", "."), errors="coerce")
    df["fichier"] = Path(chemin).stem
    return df


def main():
    """Filtre les données selon les options, dessine le graphique et l'ouvre dans le navigateur."""
    args = lire_arguments()
    chemins = args.fichiers or FICHIERS
    donnees = pd.concat([lire(c) for c in chemins])

    ordre = intitules_voulus(args)
    donnees = donnees[donnees["intitule"].isin(ordre)]
    if donnees.empty:
        raise SystemExit("Aucune ligne ne correspond aux options cochées : vérifie MODELE et les "
                         "dictionnaires STATUTS / PROGRAMMES / NOMBRES.")

    graphique = alt.Chart(donnees, title="Utilisateurs par programme et nombre de messages").mark_bar().encode(
        x=alt.X("intitule:N", title=None, sort=ordre, axis=alt.Axis(labelAngle=-30, labelLimit=320)),
        xOffset=alt.XOffset("fichier:N", sort=None),
        y=alt.Y("valeur:Q", title="Utilisateurs"),
        color=alt.Color("fichier:N", title="Fichier", sort=None),
        tooltip=["fichier", "intitule", "valeur"],
    ).properties(width=900, height=420)

    sortie = DOSSIER / "graphique_1.html"
    graphique.save(sortie)
    webbrowser.open(sortie.resolve().as_uri())


if __name__ == "__main__":
    main()
