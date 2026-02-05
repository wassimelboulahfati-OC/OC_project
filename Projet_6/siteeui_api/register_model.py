import bentoml
import xgboost as xgb
import pandas as pd

# Charger le modèle exporté
model = xgb.Booster()
model.load_model("siteeui_xgb.json")

# Charger le dataset pour récupérer les colonnes
df = pd.read_csv("siteeui_clean.csv")
feature_names = df.drop(columns=["SiteEUI(kBtu/sf)"]).columns.tolist()

# Enregistrer dans BentoML
bentoml.xgboost.save_model(
    "siteeui_xgb",
    model,
    signatures={"predict": {"batchable": True}},
    custom_objects={"feature_names": feature_names}
)

print("Modèle enregistré dans BentoML")
