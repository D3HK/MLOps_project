from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List 
import joblib
import os
import numpy as np
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends
from auth.dependencies import get_current_user
from auth.models import Token

from auth.utils import get_user, verify_password
from auth.dependencies import get_admin_user

from auth.utils import create_access_token

from fastapi import Form


# app = FastAPI()


from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
app = FastAPI(swagger_ui_parameters={"defaultModelsExpandDepth": -1})


@app.get("/")
def read_root():
    return {"status": "API is working"}


@app.post("/auth/token", response_model=Token)
async def login(
    username: str = Form(...), 
    password: str = Form(...)
):
    if username == "admin" and password == "admin123":
        token = create_access_token({"sub": "admin", "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Wrong login/password")


@app.get("/secure-data")
async def secure_data(user: dict = Depends(get_current_user)):
    return {"data": "secret", "user": user}


@app.post("/admin/update-model")
async def update_model(user: dict = Depends(get_admin_user)):
    return {"message": "Модель обновлена"}


class PredictionRequest(BaseModel):
    features: List[float]

model = joblib.load(os.path.join("src", "models", "trained_model.joblib"))

@app.post("/predict")
async def predict(
    request: PredictionRequest,
    user: dict = Depends(get_admin_user)  # Добавляем проверку
):
    try:
        features = np.array(request.features).reshape(1, -1)
        prediction = model.predict(features)
        return {"prediction": prediction.tolist()[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")