import mlflow
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Form
from pydantic import BaseModel
from typing import List 
import joblib
import os
import numpy as np
import subprocess
import logging
import requests
import time

from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from auth.dependencies import get_current_user, get_admin_user
from auth.models import Token
from auth.utils import create_access_token
from mlflow.exceptions import MlflowException
from src.models.train_model import retrain

load_dotenv()

app = FastAPI(
    title="Accidents Prediction API",
    description="API for predicting accidents and managing models",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
mlflow.set_registry_uri(os.getenv("MLFLOW_REGISTRY_URI", "http://mlflow:5000"))

# Authentication setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Logging setup
logging.basicConfig(filename='retrain.log', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the model at startup
def load_model():
    try:
        # Try to load from MLflow Registry
        return mlflow.pyfunc.load_model("models:/Accidents_RF_Model@champion")
    except MlflowException as e:
        logger.warning(f"MLflow model loading failed: {str(e)}")
        try:
            # Fallback to local model
            model_path = os.path.join(os.path.dirname(__file__), "src/models/prod_model.joblib")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}")
            return joblib.load(model_path)
        except Exception as e:
            logger.error(f"Local model loading failed: {str(e)}")
            raise

# Global model variable (can be replaced by cache or dependency)
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
    if username == "admin" and password == "admin123":
        token = create_access_token({"sub": "admin", "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Wrong login/password")


@app.post("/predict")
async def predict(
    request: PredictionRequest,
    user: dict = Depends(get_admin_user)
    ):
    """Make predictions using the trained model"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        features = np.array(request.features).reshape(1, -1)
        prediction = model.predict(features)
        return {"prediction": prediction.tolist()[0]}
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")


@app.post("/retrain", status_code=202)
async def retrain(background_tasks: BackgroundTasks, user: dict = Depends(get_admin_user)):
    """
    Trigger Airflow DAG for retraining pipeline
    """
    def trigger_airflow_dag():
        airflow_url = os.getenv("AIRFLOW_API_URL")
        airflow_user = os.getenv("AIRFLOW_API_USER")
        airflow_pass = os.getenv("AIRFLOW_API_PASS")

        dag_id = "dvc_pipeline"
        endpoint = f"{airflow_url}/dags/{dag_id}/dagRuns"
        payload = {
            "dag_run_id": f"manual_trigger_{int(time.time())}"
        }

        logger.info(f"Triggering DAG {dag_id} at {endpoint}")

        response = requests.post(endpoint, json=payload, auth=(airflow_user, airflow_pass))

        if not response.ok:
            logger.error(f"Failed to trigger DAG: {response.status_code} {response.text}")
            raise HTTPException(status_code=500, detail="Failed to trigger DAG")

        logger.info("DAG triggered successfully")

    background_tasks.add_task(trigger_airflow_dag)

    return {
        "message": "Airflow retraining pipeline triggered",
        "status": "accepted"
    }