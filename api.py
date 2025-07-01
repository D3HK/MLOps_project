from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List 
import joblib
import os
import numpy as np

from fastapi import FastAPI, Depends
from auth.dependencies import get_current_user
from auth.models import Token

app = FastAPI()


@app.post("/auth/token", response_model=Token)
async def login(username: str, password: str):
    # Заглушка. В реальности — проверка пароля из БД.
    if username == "admin" and password == "admin123":
        token = create_access_token({"sub": "admin", "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Wrong login/password")


@app.get("/secure-data")
async def secure_data(user: dict = Depends(get_current_user)):
    return {"data": "secret", "user": user}


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