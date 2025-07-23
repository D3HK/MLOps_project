import os
import time
import logging
from typing import List

import pandas as pd
import joblib
import bcrypt
import requests
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

import mlflow
import mlflow.pyfunc
import mlflow.sklearn
import mlflow.exceptions
import mlflow.tracking
import mlflow.store.artifact.artifact_repo

from auth.dependencies import get_current_user, get_admin_user
from auth.models import Token
from auth.utils import create_access_token


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

load_dotenv()

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
mlflow.set_registry_uri(os.getenv("MLFLOW_REGISTRY_URI", "http://mlflow:5000"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password verification failed: {str(e)}")
        return False

class DummyModel:
    def predict(self, X):
        raise HTTPException(
            status_code=503,
            detail="Service Unavailable: Model not loaded. Please retrain first."
        )

def load_model():
    try:
        mlflow_model = mlflow.pyfunc.load_model("models:/Accidents_RF_Model@champion")
        sklearn_model = mlflow_model._model_impl.python_model.model
        sklearn_model.feature_names_in_ = mlflow_model.metadata.get_input_schema().input_names()
        logger.info("MLflow model loaded successfully")
        return sklearn_model
    except Exception as e:
        logger.error(f"MLflow load failed: {str(e)}")

    local_model_path = "src/models/prod_model.joblib"
    try:
        model = joblib.load(local_model_path)
        if not hasattr(model, 'feature_names_in_') and hasattr(model, 'feature_names'):
            model.feature_names_in_ = model.feature_names
        logger.info("Local model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Local model load failed: {str(e)}")

    logger.error("No model available! Using placeholder. Training required.")
    return DummyModel()


try:
    model = load_model()
except Exception as e:
    logger.critical(f"Failed to load model: {str(e)}")
    model = None
    

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
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_hash = os.getenv("ADMIN_PASSWORD_HASH")
    
    if not admin_username or not admin_hash:
        logger.error("Auth credentials not configured in .env")
        raise HTTPException(status_code=500, detail="Server configuration error")
    
    if username != admin_username:
        logger.warning(f"Invalid username attempt: {username}")
        raise HTTPException(status_code=400, detail="Wrong login/password")

    if not verify_password(password, admin_hash):
        logger.warning(f"Invalid password attempt for user: {username}")
        raise HTTPException(status_code=400, detail="Wrong login/password")
    
    token = create_access_token({"sub": username, "role": "admin"})
    logger.info(f"Successful login for user: {username}")
    return {"access_token": token, "token_type": "bearer"}

@app.post("/predict")
async def predict(
    request: PredictionRequest,
    user: dict = Depends(get_admin_user)
):
    """Make prediction (Admin only)"""
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
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
            auth = (
                os.getenv("AIRFLOW_API_USER"), 
                os.getenv("AIRFLOW_API_PASS")
                )
            
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