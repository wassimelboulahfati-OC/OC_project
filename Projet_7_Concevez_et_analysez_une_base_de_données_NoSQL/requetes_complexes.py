from pymongo import MongoClient
import polars as pl

pl.Config.set_tbl_rows(30)


# Connexion
client = MongoClient("mongodb://localhost:27017")
db = client["noscites"]
collection = db["listings_paris"]

# Taux de réservation moyen par mois par type de logement
print("===  Taux de réservation moyen par mois par type de logement ===\n")

# Récupération des données depuis MongoDB
data = list(collection.find(
    { "has_availability": "t" },
    { "room_type": 1, "availability_30": 1, "_id": 0 }
))

# Conversion en DataFrame Polars
df = pl.DataFrame(data)

# Calcul du taux de réservation et moyenne par type de logement
result = df.with_columns(
    ((30 - pl.col("availability_30")) / 30 * 100).alias("taux_reservation")
).group_by("room_type").agg(
    pl.col("taux_reservation").mean().round(2).alias("taux_reservation_moyen")
).sort("taux_reservation_moyen", descending=True)

print(result)

# Médiane du nombre d'avis pour tous les logements
print("\n=== Médiane du nombre d'avis pour tous les logements ===\n")

data_reviews = list(collection.find(
    {},
    { "number_of_reviews": 1, "_id": 0 }
))

df_reviews = pl.DataFrame(data_reviews)

mediane = df_reviews.select(
    pl.col("number_of_reviews").median().alias("mediane_avis")
)

print(mediane)

# 3.3 - Médiane du nombre d'avis par catégorie d'hôte
print("\n=== 3.3 - Médiane du nombre d'avis par catégorie d'hôte ===\n")

data_host = list(collection.find(
    {},
    { "host_is_superhost": 1, "number_of_reviews": 1, "_id": 0 }
))

df_host = pl.DataFrame(data_host)

result_host = df_host.group_by("host_is_superhost").agg(
    pl.col("number_of_reviews").median().alias("mediane_avis")
).sort("host_is_superhost")

print(result_host)

#  Densité de logements par quartier de Paris
print("\n=== Densité de logements par quartier de Paris ===\n")

data_quartier = list(collection.find(
    {},
    { "neighbourhood_cleansed": 1, "_id": 0 }
))

df_quartier = pl.DataFrame(data_quartier)

result_quartier = df_quartier.group_by("neighbourhood_cleansed").agg(
    pl.col("neighbourhood_cleansed").count().alias("nombre_logements")
).with_columns(
    (pl.col("nombre_logements") / pl.col("nombre_logements").sum() * 100).round(2).alias("pourcentage")
).sort("nombre_logements", descending=True)

print(result_quartier)

# 3.5 - Quartiers avec le plus fort taux de réservation par mois
print("\n=== Quartiers avec le plus fort taux de réservation par mois ===\n")

data_resa_quartier = list(collection.find(
    { "has_availability": "t" },
    { "neighbourhood_cleansed": 1, "availability_30": 1, "_id": 0 }
))

df_resa_quartier = pl.DataFrame(data_resa_quartier)

result_resa_quartier = df_resa_quartier.with_columns(
    ((30 - pl.col("availability_30")) / 30 * 100).alias("taux_reservation")
).group_by("neighbourhood_cleansed").agg(
    pl.col("taux_reservation").mean().round(2).alias("taux_reservation_moyen")
).sort("taux_reservation_moyen", descending=True)

print(result_resa_quartier)
