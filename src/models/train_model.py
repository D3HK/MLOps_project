import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import numpy as np
import mlflow
from mlflow.models import infer_signature

# Инициализация MLflow
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("Accidents_Prediction")

# Загрузка данных с явным указанием типов
X_train = pd.read_csv('data/preprocessed/X_train.csv')
X_test = pd.read_csv('data/preprocessed/X_test.csv')
y_train = pd.read_csv('data/preprocessed/y_train.csv').squeeze()
y_test = pd.read_csv('data/preprocessed/y_test.csv').squeeze()

# Автоматическое преобразование int в float для всех колонок
int_cols = X_train.select_dtypes(include=['int', 'int64']).columns
X_train[int_cols] = X_train[int_cols].astype('float64')
X_test[int_cols] = X_test[int_cols].astype('float64')

# Обучение модели
model = RandomForestClassifier(n_jobs=-1, verbose=1)
model.fit(X_train, y_train)

# Подготовка примера данных с правильными типами
input_example = X_train.iloc[:1].copy()
signature = infer_signature(X_train, model.predict(X_train))

with mlflow.start_run():
    # Логирование параметров
    mlflow.log_params({
        "model_type": "RandomForest",
        "n_estimators": model.n_estimators,
        "max_depth": model.max_depth
    })
    
    # Логирование метрик
    mlflow.log_metrics({
        "train_accuracy": model.score(X_train, y_train),
        "test_accuracy": model.score(X_test, y_test)
    })
    
    # Логирование модели (актуальный синтаксис)
    mlflow.sklearn.log_model(
        sk_model=model,
        name="Accidents_RF_Model",
        signature=signature,
        input_example=input_example,
    )
    
    # Дополнительные теги
    mlflow.set_tags({
        "project": "Accidents Prediction",
        "framework": "scikit-learn"
    })

# Сохранение модели
joblib.dump(model, './src/models/trained_model.joblib')
print("Model successfully trained and saved")