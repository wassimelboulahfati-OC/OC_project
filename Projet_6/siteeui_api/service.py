import bentoml
import pandas as pd
from pydantic import BaseModel
from bentoml.io import JSON

# Charger le modèle BentoML
model_ref = bentoml.xgboost.get("siteeui_xgb:latest")
runner = model_ref.to_runner()

svc = bentoml.Service("siteeui_service", runners=[runner])

feature_names = model_ref.custom_objects["feature_names"]

class InputData(BaseModel):
    __root__: dict

@svc.api(input=JSON(pydantic_model=InputData), output=JSON())
async def predict(payload: InputData):
    data = payload.__root__

    df = pd.DataFrame([data])
    df = df[feature_names]

    pred = await runner.predict.async_run(df)

    return {"prediction": float(pred[0])}
