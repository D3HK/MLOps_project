import os
import shutil
import joblib
import pandas as pd
from sklearn.metrics import roc_auc_score
import mlflow
from mlflow import MlflowClient


mlflow.set_tracking_uri("http://localhost:5000")


def load_data():
    """Загрузка X_test и y_test без предположений о названии колонки."""
    X_test = pd.read_csv("data/preprocessed/X_test.csv")
    y_test = pd.read_csv("data/preprocessed/y_test.csv").squeeze()  # Берёт единственную колонку
    return X_test, y_test

def main():
    if not os.path.exists("src/models/prod_model.joblib"):
        shutil.copy("src/models/trained_model.joblib", "src/models/prod_model.joblib")
        print("Prod-model created (first version)")
        return

    X_test, y_test = load_data()
    new_model = joblib.load("src/models/trained_model.joblib")
    prod_model = joblib.load("src/models/prod_model.joblib")

    new_auc = roc_auc_score(y_test, new_model.predict_proba(X_test)[:, 1])
    prod_auc = roc_auc_score(y_test, prod_model.predict_proba(X_test)[:, 1])

    client = MlflowClient()

    # Обновление prod-модели при улучшении (порог +1%)
    if new_auc > prod_auc + 0.01:
        new_version = client.search_model_versions(
            f"run_id='{mlflow.active_run().info.run_id}'"
        )[0].version
        
        # Обновляем алиас Champion
        client.set_registered_model_alias(
            name="Accidents_RF_Model",
            alias="Champion",
            version=new_version
        )

    else:
        print(f"Current model is better (AUC: {prod_auc:.3f} vs {new_auc:.3f})")

if __name__ == "__main__":
    main()