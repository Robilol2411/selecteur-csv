"""Pages de KPI (HTML ouvert dans le navigateur) construites à partir des CSV « KPIs EMM ».

Pages disponibles (--page) :
    ensemble      Vue d'ensemble : requêtes sur la période, inscrits, utilisateurs du chatbot,
                  taux d'utilisation, requêtes par utilisateur (ignore les options).
    utilisateurs  Nombre d'utilisateurs par statut / programme.
    requetes      Nombre de requêtes utilisateurs par statut / programme.
    ratio         Requêtes par utilisateur, par statut / programme.
    messages      Utilisateurs par nombre de messages, par statut / programme / nombre.

Chaque page = tuiles (dernier mois + évolution sur le mois précédent), barres par mois,
et courbes d'évolution s'il y a au moins deux mois.

Usage (c'est main.py qui construit cette commande) :
    python graphiques.py --page requetes --statuts internes --programmes A B --nombres -- a.csv b.csv
Option absente = toutes les valeurs ; option vide = tous confondus. Sans fichier : FICHIERS.
"""
import argparse
import html
import json
import webbrowser
from pathlib import Path

import altair as alt
import pandas as pd

import kpi

DOSSIER = Path(__file__).parent

# Fichiers utilisés quand main.py n'en envoie aucun : adapte le chemin.
FICHIERS = sorted((DOSSIER / "exemples").glob("CS-IN_KPIs_EMM_*.csv"))

PAGES = {
    "ensemble": "Vue d'ensemble",
    "utilisateurs": "Utilisateurs",
    "requetes": "Requêtes utilisateurs",
    "ratio": "Requêtes par utilisateur",
    "messages": "Utilisateurs par nombre de messages",
}
MAX_TUILES = 12
# 12 couleurs bien distinctes (une par mois au maximum).
COULEURS = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2", "#b279a2",
            "#eeca3b", "#9d755d", "#ff9da6", "#1f3b73", "#bab0ac", "#2ca02c"]
# Nombres à la française dans les graphiques (1 000 et 3,5).
LOCALE = {"decimal": ",", "thousands": " ", "grouping": [3], "currency": ["", " €"]}


# --- mise en forme ---------------------------------------------------------------------------

def nombre(v, decimales=0):
    """Nombre à la française : 12 345 ou 3,4."""
    return f"{v:,.{decimales}f}".replace(",", " ").replace(".", ",")


def tuile(titre, actuel, precedent=None, decimales=0, pourcent=False, note=""):
    """Tuile HTML : valeur du dernier mois et variation par rapport au mois précédent."""
    if actuel is None or pd.isna(actuel):
        valeur = "—"
    else:
        valeur = nombre(actuel * 100, 1) + " %" if pourcent else nombre(actuel, decimales)
    variation = ""
    if precedent and not pd.isna(precedent) and actuel is not None and not pd.isna(actuel):
        ecart = (actuel - precedent) / precedent * 100
        sens = "hausse" if ecart > 0 else "baisse" if ecart < 0 else ""
        variation = f'<div class="var {sens}">{"+" if ecart > 0 else ""}{nombre(ecart, 1)} % vs mois préc.</div>'
    note = f'<div class="note">{html.escape(note)}</div>' if note else ""
    return (f'<div class="tuile"><div class="titre">{html.escape(titre)}</div>'
            f'<div class="valeur">{valeur}</div>{variation}{note}</div>')


def tuiles_series(df, ordre, decimales=0):
    """Une tuile par série : dernière valeur connue et variation sur la précédente."""
    morceaux = []
    for nom in ordre[:MAX_TUILES]:
        s = df[df["serie"] == nom]
        if s.empty:
            continue
        derniere = s.iloc[-1]
        precedent = s.iloc[-2]["valeur"] if len(s) > 1 else None
        note = derniere["mois"] + (" · somme" if derniere["somme"] else "")
        morceaux.append(tuile(nom, derniere["valeur"], precedent, decimales, note=note))
    if len(ordre) > MAX_TUILES:
        morceaux.append(f'<div class="tuile vide">+{len(ordre) - MAX_TUILES} séries dans les graphiques</div>')
    return "".join(morceaux)


# --- graphiques ------------------------------------------------------------------------------

def graphiques_series(df, ordre, mois, titre_y, format_y=",.0f"):
    """Barres groupées (une barre par mois) + courbes d'évolution par série si au moins 2 mois."""
    mois = [m for m in mois if m in set(df["mois"])]
    df = df.assign(origine=df["somme"].map({True: "somme du détail", False: "lu dans le CSV"}))
    infobulle = [alt.Tooltip("mois", title="Mois"), alt.Tooltip("serie", title="Série"),
                 alt.Tooltip("valeur", title=titre_y, format=format_y), alt.Tooltip("origine", title="Origine")]
    couleurs = alt.Scale(range=COULEURS)
    barres = alt.Chart(df, title="Comparaison par mois").mark_bar().encode(
        x=alt.X("serie:N", title=None, sort=ordre, axis=alt.Axis(labelAngle=-30, labelLimit=260)),
        xOffset=alt.XOffset("mois:N", sort=mois),
        y=alt.Y("valeur:Q", title=titre_y),
        color=alt.Color("mois:N", title="Mois", sort=mois, scale=couleurs),
        tooltip=infobulle,
    ).properties(width=820, height=360)
    if len(mois) < 2:
        return barres
    courbes = alt.Chart(df, title="Évolution").mark_line(point=True).encode(
        x=alt.X("mois:N", title=None, sort=mois, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("valeur:Q", title=titre_y),
        color=alt.Color("serie:N", title="Série", sort=ordre, scale=couleurs),
        tooltip=infobulle,
    ).properties(width=820, height=300)
    return alt.vconcat(barres, courbes).resolve_scale(color="independent")


# --- pages -----------------------------------------------------------------------------------

def page_ensemble(donnees, mois, choix):
    """Vue d'ensemble : les trois chiffres globaux et deux ratios."""
    globaux = {cle: kpi.serie(donnees, mois, cle, {})[0].set_index("mois")["valeur"]
               for cle in ("requetes_periode", "inscrits", "utilisateurs_chatbot")}
    tableau = pd.DataFrame(globaux).reindex(mois)
    if tableau.dropna(how="all").empty:
        return "", None, "Aucun des trois chiffres globaux n'a été trouvé dans les CSV."
    tableau["taux"] = tableau["utilisateurs_chatbot"] / tableau["inscrits"]
    tableau["par_utilisateur"] = tableau["requetes_periode"] / tableau["utilisateurs_chatbot"]
    tableau = tableau.dropna(how="all")
    der = tableau.iloc[-1]
    pre = tableau.iloc[-2] if len(tableau) > 1 else pd.Series(dtype=float)
    tuiles = "".join([
        tuile("Requêtes sur la période", der["requetes_periode"], pre.get("requetes_periode")),
        tuile("Inscrits au chatbot", der["inscrits"], pre.get("inscrits")),
        tuile("Utilisateurs du chatbot", der["utilisateurs_chatbot"], pre.get("utilisateurs_chatbot")),
        tuile("Taux d'utilisation", der["taux"], pre.get("taux"), pourcent=True, note="utilisateurs / inscrits"),
        tuile("Requêtes par utilisateur", der["par_utilisateur"], pre.get("par_utilisateur"), 1,
              note="requêtes / utilisateurs"),
    ])
    noms = {"requetes_periode": "Requêtes sur la période", "inscrits": "Inscrits au chatbot",
            "utilisateurs_chatbot": "Utilisateurs du chatbot", "taux": "Taux d'utilisation (%)",
            "par_utilisateur": "Requêtes par utilisateur"}
    long = (tableau.assign(taux=tableau["taux"] * 100).rename(columns=noms).rename_axis("mois")
            .reset_index().melt("mois", var_name="indicateur", value_name="valeur").dropna())
    presents = [m for m in mois if m in tableau.index]
    graphique = alt.Chart(long).mark_line(point=True).encode(
        x=alt.X("mois:N", title=None, sort=presents, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("valeur:Q", title=None),
        tooltip=[alt.Tooltip("mois", title="Mois"), alt.Tooltip("indicateur", title="Indicateur"),
                 alt.Tooltip("valeur", title="Valeur", format=",.1f")],
    ).properties(width=420, height=200).facet(
        facet=alt.Facet("indicateur:N", title=None, sort=list(noms.values())), columns=2,
    ).resolve_scale(y="independent")
    return tuiles, graphique, ""


def page_serie(indicateur, titre_y):
    """Fabrique la fonction de page pour un indicateur détaillé (utilisateurs, requêtes, messages)."""
    def construire(donnees, mois, choix):
        df, ordre = kpi.serie(donnees, mois, indicateur, choix)
        if df.empty:
            return "", None, "Aucune valeur trouvée pour ces options."
        return tuiles_series(df, ordre), graphiques_series(df, ordre, mois, titre_y), ""
    return construire


def page_ratio(donnees, mois, choix):
    """Requêtes par utilisateur pour chaque combinaison statut / programme."""
    requetes, ordre = kpi.serie(donnees, mois, "requetes", choix)
    utilisateurs, _ = kpi.serie(donnees, mois, "utilisateurs", choix)
    df = requetes.merge(utilisateurs, on=["mois", "serie"], suffixes=("_r", "_u"))
    df = df[df["valeur_u"] > 0]
    if df.empty:
        return "", None, "Il faut à la fois les requêtes et les utilisateurs pour ces options."
    df = df.assign(valeur=df["valeur_r"] / df["valeur_u"], somme=df["somme_r"] | df["somme_u"])
    df = df[["mois", "serie", "valeur", "somme"]]
    return tuiles_series(df, ordre, 1), graphiques_series(df, ordre, mois, "Requêtes / utilisateur", ",.1f"), ""


CONSTRUCTEURS = {
    "ensemble": page_ensemble,
    "utilisateurs": page_serie("utilisateurs", "Utilisateurs"),
    "requetes": page_serie("requetes", "Requêtes"),
    "ratio": page_ratio,
    "messages": page_serie("messages", "Utilisateurs"),
}


# --- HTML ------------------------------------------------------------------------------------

STYLE = """
body{font-family:"Segoe UI",system-ui,sans-serif;margin:24px;color:#222;background:#fff}
h1{font-size:22px;margin:0 0 4px} .sous-titre{color:#666;margin-bottom:18px}
.tuiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px;margin-bottom:22px}
.tuile{border:1px solid #ddd;border-radius:8px;padding:10px 12px}
.tuile .titre{font-size:12px;color:#666} .tuile .valeur{font-size:24px;font-weight:600;margin:2px 0}
.tuile .var{font-size:12px;color:#666} .var.hausse{color:#1a7f37} .var.baisse{color:#c62828}
.tuile .note{font-size:11px;color:#999} .tuile.vide{color:#999;display:flex;align-items:center}
.alerte{background:#fff4e5;border:1px solid #f0c36d;padding:10px;border-radius:6px}
details{margin-top:24px;color:#666;font-size:13px}
"""


def page_html(titre, sous_titre, tuiles, graphique, alerte, non_reconnus):
    """Assemble la page : titre, tuiles, graphique Vega-Lite, intitulés non reconnus."""
    corps = f'<div class="alerte">{html.escape(alerte)}</div>' if alerte else ""
    script = ""
    if graphique is not None:
        corps += '<div id="vis"></div>'
        script = (f'<script>vegaEmbed("#vis", {json.dumps(graphique.to_dict())}, '
                  f'{json.dumps({"formatLocale": LOCALE, "actions": {"export": True, "source": False, "compiled": False, "editor": False}})});</script>')
    if non_reconnus:
        liste = "".join(f"<li>{html.escape(i)}</li>" for i in non_reconnus)
        corps += (f"<details><summary>{len(non_reconnus)} intitulé(s) du CSV non reconnu(s) "
                  f"(à ajouter dans kpi.py si besoin)</summary><ul>{liste}</ul></details>")
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>{html.escape(titre)}</title>
<script src="https://cdn.jsdelivr.net/npm/vega@{alt.VEGA_VERSION}"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-lite@{alt.VEGALITE_VERSION}"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-embed@{alt.VEGAEMBED_VERSION}"></script>
<style>{STYLE}</style></head><body>
<h1>{html.escape(titre)}</h1><div class="sous-titre">{html.escape(sous_titre)}</div>
<div class="tuiles">{tuiles}</div>{corps}{script}
</body></html>"""


def decrire_choix(page, choix):
    """Rappel lisible des options utilisées par la page (pour le sous-titre)."""
    if page == "ensemble":
        return "Chiffres globaux (les options ne s'appliquent pas)"
    indicateur = "requetes" if page == "ratio" else page
    morceaux = []
    for nom in kpi.dimensions_de(indicateur):
        valeurs = choix.get(nom) or []
        morceaux.append(f"{nom} : {', '.join(valeurs) if valeurs else 'tous confondus'}")
    return " · ".join(morceaux)


def lire_arguments():
    """Lit la page voulue, les options et les fichiers passés en ligne de commande."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--page", choices=list(PAGES), default="ensemble")
    p.add_argument("--statuts", nargs="*", choices=list(kpi.STATUTS), default=list(kpi.STATUTS))
    p.add_argument("--programmes", nargs="*", choices=list(kpi.PROGRAMMES), default=list(kpi.PROGRAMMES))
    p.add_argument("--nombres", nargs="*", choices=list(kpi.NOMBRES), default=list(kpi.NOMBRES))
    p.add_argument("fichiers", nargs="*")
    return p.parse_args()


def main():
    """Construit la page demandée, l'enregistre en HTML et l'ouvre dans le navigateur."""
    args = lire_arguments()
    chemins = args.fichiers or FICHIERS
    if not chemins:
        raise SystemExit("Aucun fichier CSV : choisis-en dans main.py ou adapte FICHIERS.")
    donnees, mois, non_reconnus = kpi.charger(chemins)
    choix = {"statut": args.statuts, "programme": args.programmes, "nombre": args.nombres}

    tuiles, graphique, alerte = CONSTRUCTEURS[args.page](donnees, mois, choix)
    periode = mois[0] if len(mois) == 1 else f"{mois[0]} → {mois[-1]}"
    sous_titre = f"{periode} · {decrire_choix(args.page, choix)}"

    sortie = DOSSIER / f"kpi_{args.page}.html"
    sortie.write_text(page_html(PAGES[args.page], sous_titre, tuiles, graphique, alerte, non_reconnus),
                      encoding="utf-8")
    webbrowser.open(sortie.resolve().as_uri())


if __name__ == "__main__":
    main()
