from pymongo import MongoClient

# Connexion
client = MongoClient("mongodb://localhost:27017")
db = client["noscites"]
collection = db["listings_paris"]

# Étape 1 : Ajouter le champ city: "paris" aux documents existants
print("=== Étape 1 : Ajout du champ city='paris' aux documents existants ===\n")
result_paris = collection.update_many({}, {"$set": {"city": "paris"}})
print(f"Documents modifiés : {result_paris.modified_count}")

# Étape 2 : Lire le fichier CSV de Lyon et ajouter city: "lyon" à chaque document
print("\n=== Étape 2 : Import des données de Lyon ===\n")
import csv

lyon_documents = []
with open(r"C:\Users\33767\OC_project\Projet_7_Concevez_et_analysez_une_base_de_données_NoSQL\listings_Lyon.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["city"] = "lyon"
        lyon_documents.append(row)

print(f"Nombre de documents Lyon à importer : {len(lyon_documents)}")

# Insertion dans la collection
result_lyon = collection.insert_many(lyon_documents)
print(f"Documents Lyon insérés : {len(result_lyon.inserted_ids)}")

# Étape 3 : Vérification
print("\n=== Étape 3 : Vérification ===\n")
total = collection.count_documents({})
paris_count = collection.count_documents({"city": "paris"})
lyon_count = collection.count_documents({"city": "lyon"})
print(f"Total documents : {total}")
print(f"Documents Paris : {paris_count}")
print(f"Documents Lyon  : {lyon_count}")
