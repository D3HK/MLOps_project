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
    

from fastapi import BackgroundTasks
import subprocess
import logging

# Настройка логгирования
logging.basicConfig(filename='retrain.log', level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/retrain", status_code=202)
async def retrain_model(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_admin_user)
):
    """
    Starts the model retraining process in the background. 
    Requires admin.
    """
    def run_retraining():
        try:
            logger.info("Starting model retraining...")
            result = subprocess.run(
                ["./retraining_run.sh"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("Retraining completed successfully")
            else:
                logger.error(f"Retraining failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Retraining error: {str(e)}")

    background_tasks.add_task(run_retraining)
    
    return {
        "message": "Retraining process started in background",
        "status": "accepted"
    }