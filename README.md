# selecteur-csv

Petite appli Tkinter pour choisir jusqu'à 12 CSV, cocher des options et lancer des graphiques Altair.

- `main.py` : la fenêtre (12 cases, options Statut / Programme / Messages, un bouton par graphique).
- `graphique_1.py` : barres groupées, filtrées selon les options cochées.
- `exemples/` : CSV fictifs pour tester.

Prérequis : `pip install pandas altair`

Lancer : `python main.py`

À adapter :
- dans `main.py`, le dictionnaire `GRAPHIQUES` (chemins des scripts) ;
- dans `graphique_1.py`, `FICHIERS`, `MODELE` et les dictionnaires `STATUTS` / `PROGRAMMES` / `NOMBRES` (texte réel des intitulés).
