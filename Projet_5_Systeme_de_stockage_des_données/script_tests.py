from pymongo import MongoClient
import pandas as pd
import os
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["healthcareDB"]
patients = db["patients"]
logs = db["import_logs"]

folder = r"C:\Users\33767\Downloads\healthcare_dataset.csv"
liste_csv = os.listdir(folder)

# Colonnes attendues
expected_columns = [
    "Name","Age","Gender","Blood Type","Medical Condition","Date of Admission",
    "Doctor","Hospital","Insurance Provider","Billing Amount","Room Number",
    "Admission Type","Discharge Date","Medication","Test Results"
]

def run_integrity_tests(df):
    results = {}

    missing_cols = [col for col in expected_columns if col not in df.columns]
    results["missing_columns"] = missing_cols

    results["age_numeric"] = bool(pd.api.types.is_numeric_dtype(df["Age"])) if "Age" in df else False
    results["billing_numeric"] = bool(pd.api.types.is_numeric_dtype(df["Billing Amount"])) if "Billing Amount" in df else False

    results["duplicates"] = int(df.duplicated().sum())   
    results["missing_values"] = int(df.isnull().sum().sum())  

    return results


def read_csv(liste_csv:list):
    for file in liste_csv:
        if logs.find_one({"filename": file}):
            print(f"Fichier déjà inséré : {file}.")
            continue

        df = pd.read_csv(f"C:\\Users\\33767\\Downloads\\healthcare_dataset.csv\\{file}")

        # Tests d’intégrité
        integrity_results = run_integrity_tests(df)

        try:
            data = df.to_dict(orient="records")
            result = patients.insert_many(data)
            inserted_count = len(result.inserted_ids)

            # Tests d’intégration (après insertion)
            integration_results = {
                "inserted_count": inserted_count,
                "collection_count": patients.count_documents({})
            }

            print(f"{inserted_count} documents insérés depuis {file}")

            # Log complet
            logs.insert_one({
                "filename": file,
                "timestamp": datetime.now(),
                "status": "success",
                "integrity_tests": integrity_results,
                "integration_tests": integration_results
            })

        except Exception as e:
            logs.insert_one({
                "filename": file,
                "timestamp": datetime.now(),
                "status": "error",
                "error_message": str(e),
                "integrity_tests": integrity_results
            })
            print(f"Erreur lors de l’insertion du fichier {file}: {e}")

read_csv(liste_csv)

