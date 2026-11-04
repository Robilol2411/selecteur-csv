"""Graphiques Altair (barres groupées, une barre par mois) à partir des CSV « KPIs EMM ».

Graphiques disponibles (--graphique) :
    utilisateurs  Nombre d'utilisateurs (statut) [programme]
    requetes      Nombre de requêtes utilisateurs (statut) (programme)
    messages      Nombre d'utilisateur(s) (statut) (programme) avec [nombre] messages
    globaux       Nombre total de requêtes sur la période, d'inscrits et d'utilisateurs du chatbot EMM

Usage (c'est main.py qui construit cette commande) :
    python graphiques.py --graphique requetes --statuts internes --programmes A B --nombres -- a.csv b.csv
Option absente = toutes les valeurs ; option vide = tous confondus. Sans fichier : FICHIERS.
"""
import argparse
import webbrowser
from pathlib import Path

import altair as alt
import pandas as pd

import donnees as d

DOSSIER = Path(__file__).parent

# Fichiers utilisés quand main.py n'en envoie aucun : adapte le chemin.
FICHIERS = sorted((DOSSIER / "exemples").glob("CS-IN_KPIs_EMM_*.csv"))

TITRES = {
    "utilisateurs": "Nombre d'utilisateurs",
    "requetes": "Nombre de requêtes utilisateurs",
    "messages": "Nombre d'utilisateurs par nombre de messages",
    "globaux": "Chiffres globaux du chatbot EMM",
}

# 12 couleurs bien distinctes (une par mois au maximum).
COULEURS = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2", "#b279a2",
            "#eeca3b", "#9d755d", "#ff9da6", "#1f3b73", "#bab0ac", "#2ca02c"]


def lire_arguments():
    """Lit le graphique voulu, les options et les fichiers passés en ligne de commande."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--graphique", choices=list(TITRES), default="requetes")
    p.add_argument("--statuts", nargs="*", choices=list(d.STATUTS), default=list(d.STATUTS))
    p.add_argument("--programmes", nargs="*", choices=list(d.PROGRAMMES), default=list(d.PROGRAMMES))
    p.add_argument("--nombres", nargs="*", choices=list(d.NOMBRES), default=list(d.NOMBRES))
    p.add_argument("fichiers", nargs="*")
    return p.parse_args()


def valeurs_globales(tableau, mois):
    """Les trois chiffres globaux, une série par chiffre."""
    morceaux, ordre = [], []
    for cle in ("requetes_periode", "inscrits", "utilisateurs_chatbot"):
        df, _ = d.serie(tableau, mois, cle, {})
        nom = d.INDICATEURS[cle][0]
        morceaux.append(df.assign(serie=nom))
        ordre.append(nom)
    return pd.concat(morceaux, ignore_index=True), ordre


def main():
    """Lit les CSV, garde les séries demandées, dessine les barres et ouvre le graphique."""
    args = lire_arguments()
    chemins = args.fichiers or FICHIERS
    if not chemins:
        raise SystemExit("Aucun fichier CSV : choisis-en dans main.py ou adapte FICHIERS.")
    tableau, mois, non_reconnus = d.charger(chemins)
    if non_reconnus:
        print("Intitulés non reconnus :", *non_reconnus, sep="\n  ")

    if args.graphique == "globaux":
        valeurs, ordre = valeurs_globales(tableau, mois)
    else:
        choix = {"statut": args.statuts, "programme": args.programmes, "nombre": args.nombres}
        valeurs, ordre = d.serie(tableau, mois, args.graphique, choix)
    if valeurs.empty:
        raise SystemExit("Aucune valeur trouvée pour ces options.")
    valeurs["origine"] = valeurs["somme"].map({True: "somme du détail", False: "lu dans le CSV"})

    graphique = alt.Chart(valeurs, title=TITRES[args.graphique]).mark_bar().encode(
        x=alt.X("serie:N", title=None, sort=ordre, axis=alt.Axis(labelAngle=-30, labelLimit=260)),
        xOffset=alt.XOffset("mois:N", sort=mois),
        y=alt.Y("valeur:Q", title="Nombre"),
        color=alt.Color("mois:N", title="Mois", sort=mois, scale=alt.Scale(range=COULEURS)),
        tooltip=[alt.Tooltip("mois", title="Mois"), alt.Tooltip("serie", title="Série"),
                 alt.Tooltip("valeur", title="Nombre"), alt.Tooltip("origine", title="Origine")],
    ).properties(width=820, height=420)

    sortie = DOSSIER / f"graphique_{args.graphique}.html"
    graphique.save(sortie)
    webbrowser.open(sortie.resolve().as_uri())


if __name__ == "__main__":
    main()
