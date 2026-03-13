from pymongo import MongoClient
import csv

client = MongoClient("mongodb://localhost:27040")
db = client["noscites"]
collection = db["listings_paris"]

# Étape 1 : Supprimer les documents existants (Paris sans champ city)
print("=== Étape 1 : Suppression des documents existants ===\n")
result_delete = collection.delete_many({})
print(f"Documents supprimés : {result_delete.deleted_count}")

# Étape 2 : Import Paris avec city='paris'
print("\n=== Étape 2 : Import Paris avec city='paris' ===\n")
paris_docs = []
with open(r"C:\Users\33767\Downloads\listings_Paris+.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["city"] = "paris"
        paris_docs.append(row)

print(f"Documents Paris à insérer : {len(paris_docs)}")
collection.insert_many(paris_docs, ordered=False)
print("Import Paris terminé.")

# Étape 3 : Import Lyon avec city='lyon'
print("\n=== Étape 3 : Import Lyon avec city='lyon' ===\n")
lyon_docs = []
with open(r"C:\Users\33767\OC_project\Projet_7_Concevez_et_analysez_une_base_de_données_NoSQL\listings_Lyon.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["city"] = "lyon"
        lyon_docs.append(row)

print(f"Documents Lyon à insérer : {len(lyon_docs)}")
collection.insert_many(lyon_docs, ordered=False)
print("Import Lyon terminé.")

# Étape 4 : Vérification
print("\n=== Étape 4 : Vérification ===\n")
total = collection.count_documents({})
paris_count = collection.count_documents({"city": "paris"})
lyon_count = collection.count_documents({"city": "lyon"})
print(f"Total documents : {total}")
print(f"Documents Paris : {paris_count}")
print(f"Documents Lyon  : {lyon_count}")
