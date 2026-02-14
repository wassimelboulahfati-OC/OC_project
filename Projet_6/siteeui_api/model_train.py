# model_train.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb

# ============================================================
# 1. Charger les features (X) et la target (y)
# ============================================================

X = pd.read_csv("X_final_cleaned_encoded.csv")
y = pd.read_csv("y_target.csv")["SiteEnergyUse(kBtu)"]

print("Shapes chargées :")
print("   X =", X.shape)
print("   y =", y.shape)

# ============================================================
# 2. Train/Test Split
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ============================================================
# 3. Nettoyage : remplacer inf / -inf par NaN
# ============================================================

X_train = X_train.replace([np.inf, -np.inf], np.nan)
X_test = X_test.replace([np.inf, -np.inf], np.nan)

# ============================================================
# 4. Imputation des valeurs manquantes (médiane)
# ============================================================

imputer = SimpleImputer(strategy="median")

X_train = pd.DataFrame(imputer.fit_transform(X_train), columns=X_train.columns)
X_test = pd.DataFrame(imputer.transform(X_test), columns=X_test.columns)

# ============================================================
# 5. Entraînement du meilleur modèle XGBoost
# ============================================================

model = xgb.XGBRegressor(
    learning_rate=0.05,
    max_depth=4,
    n_estimators=300,
    colsample_bytree=0.8,
    n_jobs=-1,
    random_state=42,
    device="cpu"
)

print("\nEntraînement du modèle XGBoost...")
model.fit(X_train, y_train)

# ============================================================
# 6. Évaluation locale
# ============================================================

y_pred = model.predict(X_test)

rmse = mean_squared_error(y_test, y_pred) ** 0.5
r2 = r2_score(y_test, y_pred)

print("\n=== Résultats ===")
print(f"RMSE local : {rmse:.4f}")
print(f"R² local   : {r2:.4f}")

# ============================================================
# 7. Sauvegarde du modèle pour BentoML
# ============================================================

model.save_model("siteeui_xgb.json")

print("\nModèle entraîné et sauvegardé sous siteeui_xgb.json")
