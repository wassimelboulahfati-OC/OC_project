# Projet 2 – Analyse des données de systèmes éducatifs

Analyse exploratoire des données **EdStats** (Banque mondiale) pour identifier les pays les plus prometteurs pour l'expansion d'une activité de formation en ligne. Le traitement suit une architecture en trois couches : **bronze → silver → gold**.

## Contenu du dossier

| Fichier | Description |
|---|---|
| `Projet2_Analyse_des_données_SE.ipynb` | Notebook Google Colab : nettoyage, filtrage, agrégation, visualisations et classement |
| `Livrables/Wassim-1-présentation.pptx` | Présentation des résultats |
| `requirements.txt` | `pip freeze` de l'environnement Colab (très large) |

## Données sources

Cinq fichiers CSV EdStats, lus depuis Google Drive (`/content/drive/My Drive/Projet1_data/`) :

- `EdStatsCountry` : 241 lignes × 32 colonnes, un pays par ligne
- `EdStatsCountry-Series` : 613 lignes, sources des séries par pays
- `EdStatsData` : indicateurs par pays, de 1970 à 2100
- `EdStatsFootNote` : notes associées aux séries
- `EdStatsSeries` : définitions des indicateurs

## Démarche

1. **Bronze** : chargement brut avec `readcsv()`, contrôle des types, doublons et valeurs manquantes. Les colonnes de dates de `EdStatsCountry` sont converties en années (recensement, enquête ménages). Les « faux pays » (agrégats régionaux, groupes de revenus) sont retirés.
2. **Silver** : on garde les années **2000 à 2015** et 10 indicateurs, après analyse du taux de renseignement. Ils portent sur la population en âge scolaire, les inscriptions (secondaire et supérieur), le RNB/habitant (PPA), les utilisateurs d'Internet, la croissance démographique et la durée théorique du secondaire. Les autres tables sont filtrées pour rester cohérentes.
3. **Gold** : calcul d'une valeur moyenne par indicateur et par pays, puis pivot (une ligne par pays, une colonne par indicateur). Une matrice de corrélation de Pearson écarte deux indicateurs redondants. Il reste 6 indicateurs.
4. **Analyse** : distributions (médiane, moyenne, extrêmes) par indicateur, top 10 par indicateur, puis classement global.

## Classement des pays

`rank_countries_by_indicators(df)` classe chaque pays sur chaque indicateur (rang 1 = meilleure valeur) et additionne les rangs. Plus le score total est bas, mieux le pays est classé. Le résultat est affiché en diagramme en barres (« Top 10 tout indicateur confondu »).

## Exécution

1. Ouvrir le notebook dans Google Colab.
2. Placer les 5 CSV dans `Mon Drive/Projet1_data/`.
3. Exécuter les cellules dans l'ordre (le Drive doit être monté).

Dépendances réellement utilisées : `numpy`, `pandas`, `seaborn`, `matplotlib`.

> `google.colab` n'existe qu'à l'intérieur de Colab. Pour une exécution locale, remplacer `drive.mount` et le chemin de `readcsv()` par un chemin local.

## Livrable

Présentation : [`Livrables/Wassim-1-présentation.pptx`](./Livrables/Wassim-1-présentation.pptx)