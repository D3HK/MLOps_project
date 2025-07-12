import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import mlflow
import os
from pathlib import Path
import logging
import sys
import shutil
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient


logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Path(__file__).parent / 'training.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def save_model_locally(model, path):
    """Сохраняем модель в файл .joblib"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, path)
        logger.info(f"Model saved local: {path}")
        return True
    except Exception as e:
        logger.error(f"Model save error: {e}")
        return False

def log_to_mlflow(model, X_test, y_test, run):
    logger.info("\nStart logging in MLFLOW")

    accuracy = accuracy_score(y_test, model.predict(X_test))
    mlflow.log_params({
        "n_estimators": 100,
        "random_state": 42,
        "model_type": "RandomForestClassifier"
    })
    mlflow.log_metric("accuracy", accuracy)

    signature = infer_signature(X_test, model.predict(X_test))

    temp_dir = Path("/tmp/mlflow_temp")
    temp_dir.mkdir(exist_ok=True)
    model_path = temp_dir / "model"

    if model_path.exists():
        shutil.rmtree(model_path)

    mlflow.sklearn.save_model(model, model_path, signature=signature)
    mlflow.log_artifacts(model_path, artifact_path="model")

    model_uri = f"runs:/{run.info.run_id}/model"
    result = mlflow.register_model(model_uri, "Accidents_RF_Model")

    client = MlflowClient()

    client.update_registered_model(
        name="Accidents_RF_Model",
        description="Model Random Forest"
    )

    # Теги
    client.set_registered_model_tag("Accidents_RF_Model", "owner", "mlops-pipeline")
    client.set_registered_model_tag("Accidents_RF_Model", "type", "baseline")

    client.set_registered_model_alias(
        name="Accidents_RF_Model",
        alias="champion",
        version=result.version
    )
    logger.info(f"Model registred: version {result.version} → champion")


def retrain():
    setup_logging()
    logger.info("Start training")

    data = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(
        data.data, data.target, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    save_model_locally(model, Path("models/random_forest.joblib"))

    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("Accidents_Prediction")

    with mlflow.start_run() as run:
        log_to_mlflow(model, X_test, y_test, run)

if __name__ == "__main__":
    retrain()
