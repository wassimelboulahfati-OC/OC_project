import subprocess
import os

# Chemins absolus vers les scripts, depuis l'emplacement de ce fichier
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INGESTION_SCRIPT = os.path.join(BASE_DIR, "src", "ingestion", "openagenda_ingest.py")
INDEXING_SCRIPT = os.path.join(BASE_DIR, "src", "indexing", "build_index.py")


def run_script(script_path):
    """Lance un script Python et s'arrête si une erreur survient."""
    print(f"--- Lancement de {script_path} ---")
    subprocess.run(["py", script_path], check=True)


def main():
    # 1. Ingestion des données
    run_script(INGESTION_SCRIPT)
    # 2. Construction de l'index
    run_script(INDEXING_SCRIPT)
    print("Mise à jour des données terminée.")


if __name__ == "__main__":
    main()
