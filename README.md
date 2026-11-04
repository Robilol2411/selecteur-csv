# selecteur-csv

Petite appli Tkinter pour choisir jusqu'à 12 CSV « KPIs EMM », cocher des options et ouvrir des pages de KPI (Altair).

| Fichier | Rôle |
|---|---|
| `main.py` | La fenêtre : 12 cases, options Statut / Programme / Messages, un bouton par page. |
| `graphiques.py` | Construit la page HTML demandée (tuiles + graphiques) et l'ouvre dans le navigateur. |
| `kpi.py` | Lecture des CSV, reconnaissance des intitulés, extraction des séries. **Les réglages sont ici.** |
| `exemples/` | CSV fictifs pour tester. |

Prérequis : `pip install pandas altair` — Lancer : `python main.py`

## Fichiers CSV
Nom imposé : `CS-IN_KPIs_EMM_<Mois>_<Année>.csv` (ex. `CS-IN_KPIs_EMM_Septembre_2026.csv`), un fichier par mois, rangés du plus ancien au plus récent.

Intitulés reconnus (`( )` facultatif, `[ ]` obligatoire) :
- Nombre d'utilisateurs (statut) [programme]
- Nombre de requêtes utilisateurs (statut) (programme)
- Nombre d'utilisateur(s) (statut) (programme) avec [nombre] messages
- Nombre total de requêtes sur la période
- Nombre d'inscrits au chatbot EMM
- Nombre d'utilisateurs du chatbot EMM

Majuscules, accents et type d'apostrophe sont ignorés. Les intitulés non reconnus sont listés en bas de chaque page.

## Pages
- **Vue d'ensemble** : requêtes sur la période, inscrits, utilisateurs, taux d'utilisation, requêtes par utilisateur (sans options).
- **Utilisateurs**, **Requêtes**, **Requêtes / utilisateur** : options Statut et Programme.
- **Nb de messages** : options Statut, Programme et Messages.

Options : coché = une série à part ; rien de coché dans une ligne = tous confondus (ligne « totale » du CSV, ou somme du détail si elle n'existe pas — marquée « somme »).

## À adapter
Dans `kpi.py`, `STATUTS`, `PROGRAMMES`, `NOMBRES` : à gauche le nom affiché, à droite les écritures possibles dans les CSV.
Dans `graphiques.py`, `FICHIERS` (fichiers par défaut).
