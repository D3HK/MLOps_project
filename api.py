from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List 
import joblib
import os
import numpy as np

app = FastAPI()

class PredictionRequest(BaseModel):
    features: List[float]

model = joblib.load(os.path.join("src", "models", "trained_model.joblib"))

@app.post("/predict")
async def predict(request: PredictionRequest):
    try:
        features = np.array(request.features).reshape(1, -1)
        prediction = model.predict(features)
        return {"prediction": prediction.tolist()[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")