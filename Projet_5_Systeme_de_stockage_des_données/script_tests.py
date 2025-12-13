from pymongo import MongoClient, UpdateOne, InsertOne
import pandas as pd
import os
from datetime import datetime

# Connexion MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["healthcareDB"]
patients = db["patients"]
logs = db["import_logs"]

# Dossier source
folder = r"C:\Users\33767\Downloads\healthcare_dataset.csv"
liste_csv = os.listdir(folder)

# Colonnes attendues
expected_columns = [
    "Name","Age","Gender","Blood Type","Medical Condition","Date of Admission",
    "Doctor","Hospital","Insurance Provider","Billing Amount","Room Number",
    "Admission Type","Discharge Date","Medication","Test Results"
]

# --- Vérifications d’intégrité ---
def run_integrity_tests(df):
    results = {}
    missing_cols = [col for col in expected_columns if col not in df.columns]
    results["missing_columns"] = missing_cols
    results["age_numeric"] = bool(pd.api.types.is_numeric_dtype(df["Age"])) if "Age" in df else False
    results["billing_numeric"] = bool(pd.api.types.is_numeric_dtype(df["Billing Amount"])) if "Billing Amount" in df else False
    results["duplicates"] = int(df.duplicated().sum())   # conversion en int natif
    results["missing_values"] = int(df.isnull().sum().sum())
    return results

# --- Lecture et ingestion ---
def read_csv(liste_csv:list):
    for file in liste_csv:
        print(f"\n=== Début traitement du fichier: {file} ===")

        # Éviter de retraiter un fichier déjà loggé
        if logs.find_one({"filename": file}):
            print(f"[INFO] Fichier déjà inséré : {file}. On ignore.")
            continue

        # Lecture du CSV
        print("[INFO] Lecture du CSV...")
        df = pd.read_csv(os.path.join(folder, file))
        df["date_id"] = df["Date of Admission"].astype(str).str.strip()
        df["id_scd"] = df["Name"].astype(str).str.strip() + "_" + df["date_id"]

        # Récupérer les id_scd existants en base
        print("[INFO] Récupération des id_scd existants...")
        existing_ids = set(patients.distinct("id_scd"))

        # Séparer les nouvelles lignes et celles à mettre à jour
        print("[INFO] Séparation des nouvelles lignes et des lignes à mettre à jour...")
        mask_update = df["id_scd"].isin(existing_ids)
        mask_new = ~mask_update
        df_update = df[mask_update].copy()
        df_new = df[mask_new].copy()

        print(f"[INFO] Lignes à insérer: {df_new.shape[0]} | Lignes à mettre à jour: {df_update.shape[0]}")

        # Tests d’intégrité
        print("[INFO] Exécution des tests d’intégrité...")
        integrity_results = run_integrity_tests(df)

        try:
            inserted_count = 0
            operations = []

            # --- Cas 1 : nouvelles lignes ---
            print("[INFO] Préparation des nouvelles lignes...")
            new_docs = df_new.to_dict(orient="records")
            for doc in new_docs:
                doc["entry_date"] = datetime.now()
                doc["end_date"] = "2999-01-01"
                doc["status"] = "Current"
                operations.append(InsertOne(doc))

            # --- Cas 2 : lignes à mettre à jour (SCD2) ---
            print("[INFO] Préparation des mises à jour SCD2...")
            update_docs = df_update.to_dict(orient="records")
            for doc in update_docs:
                # Clore l’ancien enregistrement
                operations.append(
                    UpdateOne(
                        {"id_scd": doc["id_scd"], "status": "Current"},
                        {"$set": {"end_date": datetime.now(), "status": "Expired"}}
                    )
                )
                # Nouvelle version
                doc["entry_date"] = datetime.now()
                doc["end_date"] = "2999-01-01"
                doc["status"] = "Current"
                operations.append(InsertOne(doc))

            # --- Exécution en bulk ---
            if operations:
                print(f"[INFO] Envoi des {len(operations)} opérations à MongoDB...")
                result = patients.bulk_write(operations)
                inserted_count = result.inserted_count + result.upserted_count
                print("[INFO] Bulk write terminé.")

            # Tests d’intégration
            integration_results = {
                "inserted_count": inserted_count,
                "collection_count": patients.count_documents({})
            }

            print(f"[SUCCESS] {inserted_count} documents insérés/maj depuis {file}")

            # Log complet
            print("[INFO] Insertion du log...")
            logs.insert_one({
                "filename": file,
                "timestamp": datetime.now(),
                "status": "success",
                "integrity_tests": integrity_results,
                "integration_tests": integration_results
            })
            print("[INFO] Log inséré avec succès.")

        except Exception as e:
            print(f"[ERROR] Erreur lors de l’insertion du fichier {file}: {e}")
            logs.insert_one({
                "filename": file,
                "timestamp": datetime.now(),
                "status": "error",
                "error_message": str(e),
                "integrity_tests": integrity_results
            })

        print(f"=== Fin traitement du fichier: {file} ===\n")

# Lancer ingestion
read_csv(liste_csv)
