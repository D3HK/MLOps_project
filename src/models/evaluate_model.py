import os
import shutil
import joblib
import pandas as pd
from sklearn.metrics import roc_auc_score
import mlflow
from mlflow import MlflowClient

mlflow.set_tracking_uri("http://mlflow:5000")

def load_data():
    X_test = pd.read_csv("data/preprocessed/X_test.csv")
    y_test = pd.read_csv("data/preprocessed/y_test.csv").squeeze()
    return X_test, y_test

def main():
    client = MlflowClient()
    if not os.path.exists("src/models/prod_model.joblib"):
        shutil.copy("src/models/trained_model.joblib", "src/models/prod_model.joblib")
        print("Prod-model created (first version)")
        
        # Get the latest version of the model
        versions = client.search_model_versions(f"name='Accidents_RF_Model'")
        if versions:
            latest_version = max(int(v.version) for v in versions)
            client.set_registered_model_alias(
                name="Accidents_RF_Model",
                alias="champion",
                version=str(latest_version)
            )
            print(f"Version {latest_version} set as champion")
        return

    X_test, y_test = load_data()
    new_model = joblib.load("src/models/trained_model.joblib")
    prod_model = joblib.load("src/models/prod_model.joblib")

    new_auc = roc_auc_score(y_test, new_model.predict_proba(X_test)[:, 1])
    prod_auc = roc_auc_score(y_test, prod_model.predict_proba(X_test)[:, 1])

    # Update prod-model when improving (threshold +1%)
    if new_auc > prod_auc + 0.01:
        # 1. Copy the model
        shutil.copy("src/models/trained_model.joblib", "src/models/prod_model.joblib")
        
        # 2. Get the latest version (not via active_run)
        versions = client.search_model_versions("name='Accidents_RF_Model'")
        new_version = max(int(v.version) for v in versions)
        
        # 3. Update the alias
        client.set_registered_model_alias(
            name="Accidents_RF_Model",
            alias="champion",
            version=str(new_version)
        )
        print(f"Updated champion to version {new_version} (AUC: {new_auc:.3f})")

if __name__ == "__main__":
    main()