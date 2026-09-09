# Explorateur des prénoms français

Dashboard interactif explorant l'évolution des prénoms donnés en France depuis 1985, à partir des données officielles de l'INSEE.

## Démo

**[App en ligne]** *(lien à venir après déploiement)*

*(capture d'écran à ajouter ici une fois le déploiement fait)*

## Fonctionnalités

- **Recherche multi-prénoms** avec autocomplétion, et comparaison de plusieurs prénoms sur un même graphique
- **Évolution temporelle** par sexe, avec filtre de période ajustable
- **Filtre géographique** par région ou département
- **Carte interactive** de la popularité d'un prénom par département, pour une année donnée
- **Classement top N** des prénoms les plus donnés par année, séparé garçons/filles, avec affichage du rang du prénom recherché

## Source des données

- **Prénoms** : fichier des prénoms par sexe, année et géographie, [INSEE / data.gouv.fr](https://www.data.gouv.fr), couvrant les naissances de 1900 à 2025 (le dashboard filtre sur 1985+)
- **Référentiel géographique** : [Code Officiel Géographique (COG) de l'INSEE](https://www.insee.fr/fr/information/2560452), millésime 2026, pour la correspondance entre codes et noms de départements/régions
- **Contours géographiques** : GeoJSON des départements français, [gregoiredavid/france-geojson](https://github.com/gregoiredavid/france-geojson)

## Stack technique

- **Python** — traitement des données
- **pandas** — nettoyage, agrégation et structuration des données
- **Streamlit** — interface du dashboard
- **Plotly** — carte choroplète interactive

## Choix techniques notables

- **Séparation national / géographique** : les données sont scindées en deux tables distinctes (`prenoms_national` et `prenoms_geo`) pour ne charger la dimension géographique que lorsqu'elle est réellement utilisée, et garder les requêtes rapides sur le cas d'usage le plus fréquent (recherche nationale).
- **Fusion sur code + niveau géographique** : les codes région et département se chevauchent dans la nomenclature INSEE (ex. le code `11` désigne à la fois un département et une région). La correspondance code → nom est donc faite sur le couple `(code, niveau_geographique)` plutôt que sur le seul code, pour éviter des associations erronées.
- **Échelle logarithmique sur la carte** : la distribution des naissances par département est très asymétrique (quelques départements très peuplés écrasent les autres visuellement). Une échelle log, avec les valeurs à 0 isolées en blanc, rend la carte lisible sur l'ensemble du territoire.
- **Classement basé sur la colonne `rang` native** : plutôt que de recalculer un classement, le dashboard exploite la colonne `rang` déjà fournie par l'INSEE (calculée séparément par sexe), plus fiable et plus rapide qu'un recalcul.

## Installation et lancement local

```bash
# Cloner le repo
git clone <url-du-repo>
cd <nom-du-dossier>

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

L'application s'ouvre automatiquement sur `http://localhost:8501`.

## Pistes d'amélioration

- Analyse de tendance (prénoms en plus forte progression/déclin récent)
- Extension de la carte au niveau régional
- Export des résultats de recherche en CSV
