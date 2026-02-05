# model_train.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
import xgboost as xgb

# Charger ton dataset local (df_encoded)
df = pd.read_csv("siteeui_clean.csv")

# Définir la colonne cible
target = "SiteEUI(kBtu/sf)"

X = df.drop(columns=[target])
y = df[target]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Remplacer les infinis
X_train = X_train.replace([np.inf, -np.inf], np.nan)
X_test = X_test.replace([np.inf, -np.inf], np.nan)

# Imputation
imputer = SimpleImputer(strategy="median")
X_train = pd.DataFrame(imputer.fit_transform(X_train), columns=X_train.columns)
X_test = pd.DataFrame(imputer.transform(X_test), columns=X_test.columns)

# Recréer ton modèle XGBRegressor (celui que tu as déjà)
model = xgb.XGBRegressor(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

# Entraîner
model.fit(X_train, y_train)

# Sauvegarder pour BentoML
model.save_model("siteeui_xgb.json")

print("Modèle entraîné et sauvegardé sous siteeui_xgb.json")
