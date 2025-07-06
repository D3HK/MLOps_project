import os
import shutil
import joblib
import pandas as pd
from sklearn.metrics import roc_auc_score
import mlflow


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

    # Обновление prod-модели при улучшении (порог +1%)
    if new_auc > prod_auc + 0.01:
        shutil.copy("src/models/trained_model.joblib", "src/models/prod_model.joblib")
        print(f"Prod-model updated (AUC: {prod_auc:.3f} -> {new_auc:.3f})")
    else:
        print(f"Current model is better (AUC: {prod_auc:.3f} vs {new_auc:.3f})")
    

    with mlflow.start_run():
        mlflow.log_metrics({
            "new_model_auc": new_auc,
            "prod_model_auc": prod_auc
        })
        print("Comparison metrics are logged into MLflow")

if __name__ == "__main__":
    main()