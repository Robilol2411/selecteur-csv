"""Graphique 1 : barres groupées, une barre par mois.

Chaque intitulé des CSV suit MODELE et contient un statut, un programme et un nombre de messages.
Pour chaque ligne d'options :
  - des valeurs cochées -> on garde ces valeurs et on les sépare sur l'axe ;
  - rien de coché       -> on additionne toutes les valeurs de cette ligne (total).
Ex. statuts internes partenaires, programmes A B C D, nombres vide
    -> total des requêtes par statut et programme, tous nombres de messages confondus.

Usage (c'est main.py qui construit cette commande) :
    python graphique_1.py --statuts internes --programmes A B --nombres -- a.csv b.csv
Sans fichier, on utilise la liste FICHIERS ci-dessous.
"""
import argparse
import re
import unicodedata
import webbrowser
from itertools import product
from pathlib import Path

import altair as alt
import pandas as pd

DOSSIER = Path(__file__).parent

# Fichiers utilisés quand main.py n'en envoie aucun : adapte le chemin.
FICHIERS = [DOSSIER / "exemples" / f"CS-IN_KPIs_EMM_{m}_2026.csv"
            for m in ("Janvier", "Fevrier", "Mars", "Avril")]

# Modèle d'intitulé tel qu'il apparaît dans la 1re colonne des CSV.
MODELE = "Nombre d'utilisateur(s) {statut} {programme} avec {nombre} messages"

# Option cochée dans main.py -> texte réellement écrit dans les CSV.
# Adapte la partie de droite à tes vrais intitulés.
STATUTS = {"internes": "internes", "partenaires": "partenaires"}
PROGRAMMES = {"A": "A", "B": "B", "C": "C", "D": "D"}
NOMBRES = {"0-10": "0-10", "11-25": "11-25", "26+": "26+"}

# (colonne, argument en ligne de commande, dictionnaire des valeurs), dans l'ordre d'affichage.
DIMENSIONS = [("statut", "statuts", STATUTS), ("programme", "programmes", PROGRAMMES),
              ("nombre", "nombres", NOMBRES)]

MOIS = ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet",
        "aout", "septembre", "octobre", "novembre", "decembre"]
MOTIF_NOM = re.compile(r"^CS-IN_KPIs_EMM_([^_]+)_(\d{4})$", re.IGNORECASE)


def lire_arguments():
    """Lit les options et les fichiers passés en ligne de commande.

    Option absente -> toutes les valeurs séparées ; option présente mais vide -> total.
    """
    p = argparse.ArgumentParser(description=__doc__)
    for _, argument, valeurs in DIMENSIONS:
        p.add_argument(f"--{argument}", nargs="*", default=list(valeurs), choices=list(valeurs))
    p.add_argument("fichiers", nargs="*")
    return p.parse_args()


def nom_du_mois(chemin):
    """Renvoie (clé de tri, libellé) à partir du nom de fichier, ex. ((2026, 9), "Septembre 2026")."""
    stem = Path(chemin).stem
    trouve = MOTIF_NOM.match(stem)
    if trouve:
        mois = "".join(c for c in unicodedata.normalize("NFD", trouve.group(1).lower())
                       if unicodedata.category(c) != "Mn")
        if mois in MOIS:
            annee = int(trouve.group(2))
            return (annee, MOIS.index(mois) + 1), f"{trouve.group(1).capitalize()} {annee}"
    return (9999, 99), stem  # nom inattendu : on le met à la fin, libellé = nom du fichier


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
    df["fichier"] = nom_du_mois(chemin)[1]
    return df


def decouper_intitules(donnees):
    """Ajoute les colonnes statut / programme / nombre en reconnaissant chaque intitulé ; jette le reste."""
    correspondance = {}
    for combo in product(*(valeurs.items() for _, _, valeurs in DIMENSIONS)):
        texte = MODELE.format(**{col: ecrit for (col, _, _), (_, ecrit) in zip(DIMENSIONS, combo)})
        correspondance[texte] = [cle for cle, _ in combo]
    reconnues = donnees[donnees["intitule"].isin(correspondance)].copy()
    colonnes = [col for col, _, _ in DIMENSIONS]
    reconnues[colonnes] = pd.DataFrame(reconnues["intitule"].map(correspondance).tolist(), index=reconnues.index)
    return reconnues


def regrouper(donnees, args):
    """Filtre selon les options puis additionne les lignes dont l'option n'a rien de coché.

    Renvoie (données avec une colonne « groupe », ordre des groupes sur l'axe, titre).
    """
    separees = []  # (colonne, valeurs cochées) des lignes à garder séparées
    for col, argument, _ in DIMENSIONS:
        cochees = getattr(args, argument)
        if cochees:
            donnees = donnees[donnees[col].isin(cochees)]
            separees.append((col, cochees))
    colonnes = [col for col, _ in separees]

    totaux = donnees.groupby(["fichier", *colonnes], sort=False, as_index=False)["valeur"].sum()
    if colonnes:
        totaux["groupe"] = totaux[colonnes].astype(str).agg(" · ".join, axis=1)
        ordre = [" · ".join(c) for c in product(*(cochees for _, cochees in separees))]
        titre = "Total par " + " et ".join(colonnes)
    else:
        totaux["groupe"] = "Total"
        ordre = ["Total"]
        titre = "Total général"
    return totaux, ordre, titre


def main():
    """Lit les CSV, filtre et totalise selon les options, dessine le graphique et l'ouvre."""
    args = lire_arguments()
    chemins = sorted(args.fichiers or FICHIERS, key=lambda c: nom_du_mois(c)[0])
    donnees = decouper_intitules(pd.concat([lire(c) for c in chemins]))
    if donnees.empty:
        raise SystemExit("Aucun intitulé reconnu : vérifie MODELE et les dictionnaires "
                         "STATUTS / PROGRAMMES / NOMBRES.")

    totaux, ordre, titre = regrouper(donnees, args)
    mois = [nom_du_mois(c)[1] for c in chemins]

    graphique = alt.Chart(totaux, title=titre).mark_bar().encode(
        x=alt.X("groupe:N", title=None, sort=ordre, axis=alt.Axis(labelAngle=-30, labelLimit=320)),
        xOffset=alt.XOffset("fichier:N", sort=mois),
        y=alt.Y("valeur:Q", title="Nombre"),
        color=alt.Color("fichier:N", title="Mois", sort=mois),
        tooltip=[alt.Tooltip("fichier", title="Mois"), alt.Tooltip("groupe", title="Groupe"),
                 alt.Tooltip("valeur", title="Nombre")],
    ).properties(width=900, height=420)

    sortie = DOSSIER / "graphique_1.html"
    graphique.save(sortie)
    webbrowser.open(sortie.resolve().as_uri())


if __name__ == "__main__":
    main()
