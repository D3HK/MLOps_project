import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import numpy as np
import mlflow
from mlflow.models import infer_signature

import os
from mlflow import set_tracking_uri, set_experiment

tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "Accidents_Prediction")

set_tracking_uri(tracking_uri)
set_experiment(experiment_name)

X_train = pd.read_csv('data/preprocessed/X_train.csv')
X_test = pd.read_csv('data/preprocessed/X_test.csv')
y_train = pd.read_csv('data/preprocessed/y_train.csv').squeeze()
y_test = pd.read_csv('data/preprocessed/y_test.csv').squeeze()

int_cols = X_train.select_dtypes(include=['int', 'int64']).columns
X_train[int_cols] = X_train[int_cols].astype('float64')
X_test[int_cols] = X_test[int_cols].astype('float64')

model = RandomForestClassifier(n_jobs=-1, verbose=1)
model.fit(X_train, y_train)

input_example = X_train.iloc[:1].copy()
signature = infer_signature(X_train, model.predict(X_train))

with mlflow.start_run():
    mlflow.log_params({
        "model_type": "RandomForest",
        "n_estimators": model.n_estimators,
        "max_depth": model.max_depth
    })
    
    mlflow.log_metrics({
        "train_accuracy": model.score(X_train, y_train),
        "test_accuracy": model.score(X_test, y_test)
    })
    
    mlflow.sklearn.log_model(
        sk_model=model,
        name="Accidents_RF_Model",
        signature=signature,
        input_example=input_example,
    )
    
    mlflow.set_tags({
        "project": "Accidents Prediction",
        "framework": "scikit-learn"
    })

joblib.dump(model, './src/models/trained_model.joblib')
print("Model successfully trained and saved")