# selecteur-csv

Petite appli Tkinter pour choisir jusqu'à 12 CSV, cocher des options et lancer des graphiques Altair.

- `main.py` : la fenêtre (12 cases, options Statut / Programme / Messages, un bouton par graphique).
- `graphique_1.py` : barres groupées, filtrées selon les options cochées.
- `exemples/` : CSV fictifs pour tester.

Les CSV doivent s'appeler `CS-IN_KPIs_EMM_<Mois>_<Année>.csv` (ex. `CS-IN_KPIs_EMM_Septembre_2026.csv`) ; ils sont rangés du plus ancien au plus récent.
Dans une ligne d'options, ne rien cocher = faire le total de cette ligne (ex. rien dans Messages = total par statut et programme).

Prérequis : `pip install pandas altair`

Lancer : `python main.py`

À adapter :
- dans `main.py`, le dictionnaire `GRAPHIQUES` (chemins des scripts) ;
- dans `graphique_1.py`, `FICHIERS`, `MODELE` et les dictionnaires `STATUTS` / `PROGRAMMES` / `NOMBRES` (texte réel des intitulés).
