{% docs __overview__ %}
# Projet GreenAndCoop — Infrastructure de données météo

Ce projet DBT transforme les données météorologiques brutes ingérées par Airbyte
depuis trois sources (InfoClimat, Weather Underground Ichtegem, Weather Underground
La Madeleine) en un schéma analytique en étoile exploitable par les Data Scientists.

## Architecture en couches

| Couche | Schéma PostgreSQL | Rôle |
|--------|------------------|------|
| **Bronze** | `public_bronze` | Lecture fidèle des tables RAW Airbyte, contrat de colonnes forcé |
| **Silver** | `public_silver` | Standardisation des noms, conversions d'unités (impérial → métrique), alignement du schéma |
| **Gold** | `public_gold` | Union des trois sources dans un schéma unifié |
| **Datamart** | `public_datamart` | Schéma en étoile : `dim_weather_stations` + `fact_weather_observations` |

## Sources de données

- **InfoClimat** : stations SYNOP françaises (Armentières, Bergues, Lille-Lesquin, Hazebrouck)
  — données en unités SI (°C, hPa, km/h, mm)
- **Weather Underground Ichtegem** (IICHTE19, Belgique) : station amateur
  — données en unités impériales (°F, inHg, mph, pouces)
- **Weather Underground La Madeleine** (ILAMAD25, France) : station amateur
  — données en unités impériales (°F, inHg, mph, pouces)

## Qualité des données

31 tests automatisés couvrent :
- **Intégrité** : `not_null` sur toutes les clés
- **Unicité** : `unique` sur les clés de substitution + tests composites `(station_id, observed_at)` à chaque couche
- **Relations** : `relationships` entre `fact_weather_observations` et `dim_weather_stations`
- **Valeurs acceptées** : `accepted_values` sur `source_system`
- **Règles métier** : plages physiques (température, pression, humidité), cohérence point de rosée / température

{% enddocs %}

{% docs station_id %}
Identifiant unique de la station météorologique.
- Stations WU : `WU_ICHTEGEM`, `WU_LA_MADELEINE`
- Stations InfoClimat : `07015`, `00052`, `000R5`, `STATIC0010`
{% enddocs %}

{% docs observed_at %}
Horodatage de la mesure en UTC, au format `timestamp without time zone`.
Toutes les sources sont alignées sur UTC après ingestion par Airbyte.
{% enddocs %}

{% docs source_system %}
Système source de la donnée météorologique.
Valeurs possibles : `infoclimat`, `weather_underground`.
{% enddocs %}

{% docs observation_id %}
Clé de substitution de la table de faits, calculée par `md5(station_id || '_' || observed_at)`.
Garantit l'unicité de chaque observation dans le datamart.
{% enddocs %}
