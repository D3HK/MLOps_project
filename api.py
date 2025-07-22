import mlflow
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Form
from pydantic import BaseModel
from typing import List 
import joblib
import os
import numpy as np
import pandas as pd
import subprocess
import logging
import requests
import time
import base64

from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from auth.dependencies import get_current_user, get_admin_user
from auth.models import Token
from auth.utils import create_access_token
from mlflow.exceptions import MlflowException
from src.models.train_model import retrain

import logging
from fastapi import Request


app = FastAPI(
    title="Accidents Prediction API",
    description="API for predicting accidents and managing models",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api.log')
    ]
)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

load_dotenv()

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
mlflow.set_registry_uri(os.getenv("MLFLOW_REGISTRY_URI", "http://mlflow:5000"))

# Authentication setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Logging setup
logging.basicConfig(filename='retrain.log', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the model at startup

# def load_model():
#     model_path = os.path.join(os.path.dirname(__file__), "src/models/trained_model.joblib")
#     return joblib.load(model_path)

def load_model():
    try:
        mlflow_model = mlflow.pyfunc.load_model("models:/Accidents_RF_Model@champion")
        sklearn_model = mlflow_model._model_impl.python_model.model
        sklearn_model.feature_names_in_ = mlflow_model.metadata.get_input_schema().input_names()
        return sklearn_model
    except Exception as e:
        logger.warning(f"MLflow loading failed: {str(e)}")
        try:
            model_path = os.path.join(os.path.dirname(__file__), "src/models/prod_model.joblib")
            return joblib.load(model_path)
        except Exception as e:
            logger.critical(f"All model loading attempts failed: {str(e)}")
            raise

# Global model variable
try:
    model = load_model()
except Exception as e:
    logger.critical(f"Failed to load model: {str(e)}")
    model = None

# Model for prediction query
class PredictionRequest(BaseModel):
    features: List[float]


@app.get("/")
def read_root():
    return {"status": "API is working", "model_loaded": model is not None}

@app.post("/auth/token", response_model=Token)
async def login(
    username: str = Form(...), 
    password: str = Form(...)
):
    """Generate access token for authenticated users"""
    if username == os.getenv("ADMIN_USERNAME") and password == os.getenv("ADMIN_PASSWORD"):
        token = create_access_token({"sub": "admin", "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Wrong login/password")


@app.post("/predict")
async def predict(
    request: PredictionRequest,
    user: dict = Depends(get_admin_user)  # Добавляем проверку авторизации
):
    """Make prediction (Admin only)"""
    try:
        features_df = pd.DataFrame(
            [request.features],
            columns=model.feature_names_in_
        )
        prediction = model.predict(features_df)
        return {"prediction": int(prediction[0])}
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(400, detail=str(e))


@app.post("/retrain")
async def retrain(user: dict = Depends(get_admin_user)):
    """
    Starts DAG dvc_pipeline в Airflow and returns the status
    """
    def trigger_dag():
        try:
            airflow_url = "http://airflow-webserver:8080/api/v1/dags/dvc_pipeline/dagRuns"
            auth = (os.getenv("AIRFLOW_API_USER"), 
                   os.getenv("AIRFLOW_API_PASS"))
            
            response = requests.post(
                airflow_url,
                json={
                    "dag_run_id": f"manual_run_{int(time.time())}",
                    "conf": {}
                },
                auth=auth,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Airflow API error: {str(e)}")
            raise

    try:
        result = trigger_dag()
        return {
            "status": "success",
            "dag_run_id": result.get("dag_run_id"),
            "airflow_response": result
        }
    except Exception as e:
        logger.exception("Failed to trigger DAG")
        raise HTTPException(500, detail=str(e))