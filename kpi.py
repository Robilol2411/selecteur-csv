"""Lecture des CSV « KPIs EMM » et extraction des séries à tracer.

Chaque CSV a deux colonnes (intitulé, valeur). Les intitulés reconnus sont ceux de INDICATEURS,
où ( ) = partie facultative et [ ] = partie obligatoire :

    Nombre d'utilisateurs (statut) [programme]
    Nombre de requêtes utilisateurs (statut) (programme)
    Nombre d'utilisateur(s) (statut) (programme) avec [nombre] messages
    Nombre total de requêtes sur la période
    Nombre d'inscrits au chatbot EMM
    Nombre d'utilisateurs du chatbot EMM

La comparaison ignore majuscules, accents, espaces en trop et le type d'apostrophe (' ou ’).

Règle des options : une valeur cochée = une série séparée ; rien de coché = « tous confondus ».
Pour « tous confondus » on prend la ligne du CSV sans cette partie (ex. « Nombre de requêtes
utilisateurs A » pour tous les statuts). Si cette ligne n'existe pas, on additionne le détail
et la valeur est marquée « somme ».
"""
import re
import unicodedata
from itertools import product
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------------------------
# Réglages à adapter : valeur affichée dans main.py -> façons dont elle est écrite dans les CSV.
# ---------------------------------------------------------------------------------------------
STATUTS = {"internes": ["internes", "interne"], "partenaires": ["partenaires", "partenaire"]}
PROGRAMMES = {"A": ["A"], "B": ["B"], "C": ["C"], "D": ["D"]}
NOMBRES = {"0-10": ["0-10"], "11-25": ["11-25"], "26+": ["26+", "+26"]}

DIMENSIONS = {"statut": STATUTS, "programme": PROGRAMMES, "nombre": NOMBRES}

# clé -> (titre, intitulé normalisé ; {statut} {programme} {nombre} = parties variables).
# Les plus précis d'abord : le premier modèle qui correspond l'emporte.
INDICATEURS = {
    "requetes_periode": ("Requêtes sur la période", r"nombre total de requetes sur la periode"),
    "inscrits": ("Inscrits au chatbot", r"nombre d'inscrits au chatbot emm"),
    "utilisateurs_chatbot": ("Utilisateurs du chatbot", r"nombre d'utilisateurs du chatbot emm"),
    "messages": ("Utilisateurs par nombre de messages",
                 r"nombre d'utilisateur(?:\(s\)|s)?(?: {statut})?(?: {programme})? avec {nombre} messages"),
    "requetes": ("Requêtes utilisateurs", r"nombre de requetes utilisateurs(?: {statut})?(?: {programme})?"),
    "utilisateurs": ("Utilisateurs", r"nombre d'utilisateur(?:\(s\)|s)(?: {statut})? {programme}"),
}

# Noms de fichiers acceptés : CS-IN_KPIs_EMM_<Mois>_<Année>.csv
MOTIF_NOM = re.compile(r"^CS-IN_KPIs_EMM_([^_]+)_(\d{4})\.csv$", re.IGNORECASE)
MOIS = ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet",
        "aout", "septembre", "octobre", "novembre", "decembre"]


def normaliser(texte):
    """Minuscules, sans accents, apostrophes droites, espaces simples (« Requêtes  ’ » -> « requetes ' »)."""
    texte = unicodedata.normalize("NFD", str(texte).lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    texte = re.sub(r"[’‘`´]", "'", texte)
    return re.sub(r"\s+", " ", texte).strip()


# --- noms de fichiers ------------------------------------------------------------------------

def date_du_fichier(chemin):
    """Renvoie (année, numéro du mois) lus dans le nom du fichier, ou None si le nom n'est pas valide."""
    trouve = MOTIF_NOM.match(Path(chemin).name)
    if not trouve or normaliser(trouve.group(1)) not in MOIS:
        return None
    return int(trouve.group(2)), MOIS.index(normaliser(trouve.group(1))) + 1


def libelle_mois(chemin):
    """« Septembre 2026 » à partir du nom du fichier (ou le nom du fichier s'il n'est pas reconnu)."""
    date = date_du_fichier(chemin)
    if date is None:
        return Path(chemin).stem
    return f"{MOIS[date[1] - 1].capitalize()} {date[0]}".replace("Fevrier", "Février") \
        .replace("Aout", "Août").replace("Decembre", "Décembre")


# --- reconnaissance des intitulés ------------------------------------------------------------

def _groupe(nom):
    """Morceau de regex qui capture une valeur de la dimension `nom` sous toutes ses écritures."""
    ecritures = sorted({normaliser(e) for v in DIMENSIONS[nom].values() for e in v}, key=len, reverse=True)
    return f"(?P<{nom}>{'|'.join(re.escape(e) for e in ecritures)})"


def _compiler():
    """Compile les modèles d'INDICATEURS en regex et note les dimensions de chacun."""
    regles = {}
    for cle, (_, modele) in INDICATEURS.items():
        motif = modele
        for nom in DIMENSIONS:
            motif = motif.replace("{" + nom + "}", _groupe(nom))
        regex = re.compile(f"^{motif}$")
        regles[cle] = (regex, [nom for nom in DIMENSIONS if nom in regex.groupindex])
    return regles


REGLES = _compiler()
# écriture normalisée -> valeur affichée, par dimension
_VERS_CLE = {nom: {normaliser(e): cle for cle, ecr in valeurs.items() for e in ecr}
             for nom, valeurs in DIMENSIONS.items()}


def reconnaitre(intitule):
    """Renvoie {indicateur, statut, programme, nombre} pour un intitulé (None si non reconnu).

    Une partie absente de l'intitulé vaut None (= tous confondus).
    """
    texte = normaliser(intitule)
    for cle, (regex, dims) in REGLES.items():
        trouve = regex.match(texte)
        if trouve:
            infos = {"indicateur": cle, **{nom: None for nom in DIMENSIONS}}
            for nom in dims:
                if trouve.group(nom):
                    infos[nom] = _VERS_CLE[nom][trouve.group(nom)]
            return infos
    return None


# --- lecture ---------------------------------------------------------------------------------

def lire(chemin):
    """Lit un CSV à deux colonnes (intitulé, valeur) ; séparateur , ou ; détecté seul."""
    try:
        df = pd.read_csv(chemin, sep=None, engine="python", encoding="utf-8-sig")
    except UnicodeDecodeError:  # CSV enregistré par Excel
        df = pd.read_csv(chemin, sep=None, engine="python", encoding="latin-1")
    df = df.iloc[:, :2]
    df.columns = ["intitule", "valeur"]
    df["intitule"] = df["intitule"].astype(str).str.strip()
    df["valeur"] = pd.to_numeric(df["valeur"].astype(str).str.replace(" ", "").str.replace(",", "."),
                                 errors="coerce")
    df["mois"] = libelle_mois(chemin)
    return df


def charger(chemins):
    """Lit et reconnaît tous les CSV.

    Renvoie (données reconnues, liste des mois du plus ancien au plus récent, intitulés non reconnus).
    """
    chemins = sorted(chemins, key=lambda c: date_du_fichier(c) or (9999, 99))
    brut = pd.concat([lire(c) for c in chemins], ignore_index=True)
    infos = brut["intitule"].map(reconnaitre)
    reconnues = infos.notna()
    donnees = pd.concat([brut[reconnues].reset_index(drop=True),
                         pd.DataFrame(infos[reconnues].tolist())], axis=1)
    non_reconnus = sorted(brut.loc[~reconnues, "intitule"].unique())
    return donnees, [libelle_mois(c) for c in chemins], non_reconnus


# --- séries ----------------------------------------------------------------------------------

def dimensions_de(indicateur):
    """Dimensions (statut / programme / nombre) que peut contenir l'intitulé de cet indicateur."""
    return REGLES[indicateur][1]


def serie(donnees, mois, indicateur, choix):
    """Extrait les valeurs d'un indicateur, une série par combinaison d'options cochées.

    `choix` : {"statut": [...], "programme": [...], "nombre": [...]} ; liste vide = tous confondus.
    Renvoie (DataFrame mois / serie / valeur / somme, ordre des séries).
    """
    d = donnees[donnees["indicateur"] == indicateur]
    dims = dimensions_de(indicateur)
    listes = [choix.get(nom) or [None] for nom in dims]
    lignes, ordre = [], []
    for combo in product(*listes):
        nom_serie = " · ".join(v for v in combo if v) or "Tous"
        ordre.append(nom_serie)
        exact = pd.Series(True, index=d.index)
        detail = pd.Series(True, index=d.index)
        for nom, valeur in zip(dims, combo):
            if valeur is None:
                exact &= d[nom].isna()
                detail &= d[nom].notna()
            else:
                exact &= d[nom] == valeur
                detail &= d[nom] == valeur
        for m in mois:
            ligne = d[exact & (d["mois"] == m)]
            somme = ligne.empty
            if somme:
                ligne = d[detail & (d["mois"] == m)]
            if not ligne.empty:
                lignes.append({"mois": m, "serie": nom_serie, "valeur": ligne["valeur"].sum(), "somme": somme})
    return pd.DataFrame(lignes, columns=["mois", "serie", "valeur", "somme"]), ordre
