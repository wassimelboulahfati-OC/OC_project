import bentoml
import pandas as pd
import numpy as np
from bentoml.io import JSON
import xgboost as xgb
from bentoml import Runnable

###############################################
# 1. Runnable XGBoost
###############################################

class XGBRunnable(Runnable):
    SUPPORTED_RESOURCES = ("cpu",)
    SUPPORTS_CPU_MULTI_THREADING = True

    def __init__(self):
        self.model = xgb.XGBRegressor()
        self.model.load_model("siteeui_xgb.json")

    @bentoml.Runnable.method(batchable=False)
    def predict(self, input_df):
        return self.model.predict(input_df)

xgb_runner = bentoml.Runner(XGBRunnable, name="xgb_runner")

###############################################
# 2. Chargement des colonnes finales
###############################################

MODEL_COLUMNS = pd.read_csv("X_final_cleaned_encoded.csv", nrows=0).columns.tolist()

# Médianes EXACTES du dataset
MEDIAN_GFA = 48229.5
MEDIAN_ENERGYSTAR = 71.0

###############################################
# 3. Service BentoML
###############################################

svc = bentoml.Service("siteeui_service", runners=[xgb_runner])

###############################################
# 4. Preprocessing identique au notebook
###############################################

def preprocess(payload: dict) -> pd.DataFrame:
    df = pd.DataFrame([payload]).copy()

    # === 4.1 Colonnes numériques manquantes ===
    numeric_defaults = [
        "PropertyGFATotal", "PropertyGFABuilding(s)", "PropertyGFAParking",
        "NumberofFloors", "NumberofBuildings", "YearBuilt",
        "Latitude", "Longitude", "LargestPropertyUseTypeGFA",
        "SecondLargestPropertyUseTypeGFA"
    ]

    for col in numeric_defaults:
        df[col] = df.get(col, 0)

    # === 4.2 Colonnes catégorielles manquantes ===
    categorical_defaults = [
        "BuildingType", "PrimaryPropertyType", "Neighborhood",
        "LargestPropertyUseType", "ListOfAllPropertyUseTypes"
    ]

    for col in categorical_defaults:
        df[col] = df.get(col, "UNKNOWN")

    # === 4.3 Recalcul des features EXACTES du notebook ===

    # BuildingAge
    df["BuildingAge"] = df["DataYear"] - df["YearBuilt"]

    # DistanceToCenter (Haversine)
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
        return 2 * R * np.arcsin(np.sqrt(a))

    df["DistanceToCenter"] = df.apply(
        lambda r: haversine(r["Latitude"], r["Longitude"], 47.6062, -122.3321),
        axis=1
    )

    # NumberOfUses
    df["NumberOfUses"] = df["ListOfAllPropertyUseTypes"].astype(str).str.count(",") + 1

    # PrimaryUseRatio
    df["PrimaryUseRatio"] = df["LargestPropertyUseTypeGFA"] / df["PropertyGFATotal"].replace(0, np.nan)

    # SecondUseRatio
    df["SecondUseRatio"] = df["SecondLargestPropertyUseTypeGFA"] / df["PropertyGFATotal"].replace(0, np.nan)

    # ParkingRatio
    df["ParkingRatio"] = df["PropertyGFAParking"] / df["PropertyGFATotal"].replace(0, np.nan)

    # AvgFloorArea
    df["AvgFloorArea"] = df["PropertyGFABuilding(s)"] / df["NumberofFloors"].replace(0, np.nan)

    # HasParking
    df["HasParking"] = (df["PropertyGFAParking"] > 0).astype(int)

    # HasMultipleUses
    df["HasMultipleUses"] = (df["NumberOfUses"] > 1).astype(int)

    # HasSecondUse
    df["HasSecondUse"] = (df["SecondLargestPropertyUseTypeGFA"] > 0).astype(int)

    # HasENERGYSTAR
    df["HasENERGYSTAR"] = df["ENERGYSTARScore"].notna().astype(int)

    # ENERGYSTARScore_Imputed
    df["ENERGYSTARScore_Imputed"] = df["ENERGYSTARScore"].fillna(MEDIAN_ENERGYSTAR)

    # ComplexityScore
    df["ComplexityScore"] = df["PropertyGFATotal"] * df["NumberOfUses"]

    # IsOldLargeBuilding
    df["IsOldLargeBuilding"] = ((df["BuildingAge"] > 50) & (df["PropertyGFATotal"] > MEDIAN_GFA)).astype(int)

    # AgeCategory
    df["AgeCategory"] = pd.cut(
        df["BuildingAge"],
        bins=[0, 20, 50, 80, 200],
        labels=["Très récent", "Récent", "Ancien", "Très ancien"]
    )

    # LocationZone
    df["LocationZone"] = pd.cut(
        df["DistanceToCenter"],
        bins=[0, 2, 5, 20],
        labels=["Centre", "Proche", "Périphérie"]
    )

    # === 4.4 OneHotEncoding identique ===
    df_encoded = pd.get_dummies(df, drop_first=True)

    # === 4.5 Alignement EXACT des colonnes ===
    df_final = df_encoded.reindex(columns=MODEL_COLUMNS, fill_value=0)

    return df_final

###############################################
# 5. Endpoint API
###############################################

@svc.api(input=JSON(), output=JSON())
def predict(payload: dict):
    X = preprocess(payload)
    pred = xgb_runner.predict.run(X)[0]
    return {"prediction": float(pred)}
