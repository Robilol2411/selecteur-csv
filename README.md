# selecteur-csv

Petite appli Tkinter pour choisir jusqu'à 12 CSV « KPIs EMM », cocher des options et ouvrir des graphiques Altair.

| Fichier | Rôle |
|---|---|
| `main.py` | La fenêtre : choix du graphique (radio), 12 cases, options utiles au graphique choisi (* = obligatoire), bouton Lancer. |
| `graphiques.py` | Dessine le graphique demandé (barres groupées, une barre par mois) et l'ouvre dans le navigateur. |
| `donnees.py` | Lecture des CSV, reconnaissance des intitulés, extraction des séries. **Les réglages sont ici.** |
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

Majuscules, accents et type d'apostrophe sont ignorés. Les intitulés non reconnus sont affichés dans la console.

## Graphiques
- **Utilisateurs**, **Requêtes** : options Statut et Programme.
- **Nb de messages** : options Statut, Programme et Messages.
- **Chiffres globaux** : requêtes sur la période, inscrits, utilisateurs du chatbot (sans options).

Options : coché = une série à part ; rien de coché dans une ligne = tous confondus (ligne « totale » du CSV, ou somme du détail si elle n'existe pas — indiquée « somme du détail » dans l'infobulle).

## À adapter
Dans `donnees.py`, `STATUTS`, `PROGRAMMES`, `NOMBRES` : à gauche le nom affiché, à droite les écritures possibles dans les CSV.
Dans `graphiques.py`, `FICHIERS` (fichiers par défaut).
