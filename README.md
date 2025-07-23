# MLOps Accidents Project

## Project Repository
All project files and source code are available on GitHub:  
🔗 [https://github.com/D3HK/MLOps_project](https://github.com/D3HK/MLOps_project)

---

## **Initial Setup: Folder Permissions & Database Configuration**

Before starting the services, run these preparation commands to ensure proper permissions and database setup:

### **1. Airflow Logs Setup**
```bash
# Clean and recreate logs directory
sudo rm -rf /workspaces/MLOps_project/airflow/logs/scheduler
mkdir -p /workspaces/MLOps_project/airflow/logs/scheduler

# Set correct permissions
sudo chown -R 1000:0 /workspaces/MLOps_project/airflow/logs
sudo chmod -R 775 /workspaces/MLOps_project/airflow/logs
```

### **2. Database Initialization**
```bash
# Recreate SQLite database file
sudo rm -rf /workspaces/MLOps_project/airflow/airflow.db
touch /workspaces/MLOps_project/airflow/airflow.db

# Set database permissions
sudo chown 1000:0 /workspaces/MLOps_project/airflow/airflow.db
sudo chmod 660 /workspaces/MLOps_project/airflow/airflow.db

# Initialize database
docker-compose up -d airflow-webserver
docker-compose exec airflow-webserver airflow db init
```

### **3. Start All Services**
```bash
docker-compose up -d
```

### **4. Key Ports**
- **MLflow UI**: `http://localhost:5000`
- **API Docs**: `http://localhost:8000/docs` 
- **Airflow UI**: `http://localhost:8080`

---

## API Security Implementation  

I implemented security features to protect the API. Here's what I did:  

### **Authentication (Login Protection)**  
- Added username/password login to get JWT tokens  
- Without a valid token, private API endpoints are inaccessible  
- Passwords are securely hashed before storage  

### **Authorization (Access Control)**  
- Created two user roles:  
  - **Admins** - full access (including model updates)  
  - **Regular users** - restricted access  
- Implemented permission checks for sensitive operations  

### **Data Protection**  
- All protected routes require valid tokens  
- Tokens have expiration for security  
- Added input validation to prevent attacks  

### **How to Test**  
1. **Get a token**:  
   ```bash
   curl -X POST "http://localhost:8000/auth/token" \
        -d "username=admin&password=admin123" \
        -H "Content-Type: application/x-www-form-urlencoded"
   ```
2. **Use the token** (replace `$TOKEN`):  
   ```bash
   curl -X POST "http://localhost:8000/predict" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"features": [10, 3, 1, 0.0, 2021, 60, 2, 1, 1, 3, 2, 1, 1, 50, 7, 12, 5, 77, 
            77317, 2, 1, 0, 6, 48.60, 2.89, 17, 2, 1]}'
   ```

### **Key Features**  
✔️ Token-based authentication  
✔️ Role-based access control  
✔️ Secure password storage  
✔️ Token expiration  

For developers: Interactive docs available at `http://localhost:8000/docs`  

---

## **Data & Model Versioning**  
- Implemented DVC for tracking:  
  - Raw data (`data/raw/`)  
  - Processed data (`data/preprocessed/`)  
  - Trained models (`src/models/trained_model.joblib`)  

### **Pipeline Structure**  
```bash
dvc.yaml
├── import_data    # Data ingestion
├── preprocess     # Data cleaning
├── train          # Model training
└── predict        # Predictions
```

---

## **Automated Model Retraining**  
- Added `/retrain` endpoint (admin-only)  
- Compares new model metrics (AUC-ROC/F1) with production  
- Updates production model only if improvement >1%  

### **Retraining Process**  
```bash
./retraining_run.sh  # Executes: dvc repro evaluate
```  
- Creates `prod_model.joblib` on first run  
- Can be triggered by:  
  - Scheduled jobs  
  - API calls  

### **Pipeline Updates**  
```yaml
# dvc.yaml
evaluate:
    cmd: python src/models/evaluate_model.py
    deps:
      - src/models/trained_model.joblib
      - data/preprocessed/X_test.csv
      - data/preprocessed/y_test.csv
    outs:
      - src/models/prod_model.joblib
```  

### **Test Commands**  
```bash 
curl -X POST "http://localhost:8000/retrain" \
     -H "Authorization: Bearer $TOKEN"
```

---

## **DVC Pipeline Dockerization**  

### **Implementation**  
- Integrated DVC with Docker containers  
- Configured `docker-compose.yml` for DVC-API interaction  
- Set up shared volumes for data synchronization  
- Added API endpoint for pipeline triggering  

### **Testing**  
1. Start services:  
   ```bash  
   docker compose up -d  
   ```  
2. Check DVC status:  
   ```bash  
   docker compose exec api bash -c "cd /app && dvc status"  
   ```  
3. Trigger retraining:  
   ```bash  
   curl -X POST http://localhost:8000/retrain -H "Authorization: Bearer $TOKEN"  
   ```  

### **Modified Files**  
- `docker-compose.yml`  
- `Dockerfile`  

---

## **MLflow Tracking & Dockerization**  

### **Setup**  
- Automatic experiment tracking in `./mlruns/`  
- Logs:  
  - Model parameters  
  - Evaluation metrics  
  - Model artifacts  

### **Testing**  
```bash
# Start MLflow
docker compose up -d mlflow

# Run training with logging
docker compose run api dvc repro --force evaluate
```

Access UI at: `http://localhost:5000`  

---

## **Airflow Integration**  

### **Implementation**  
- Automated pipeline scheduling  
- Manual triggering capability  
- Run history tracking  

### **Usage**  
1. Start Airflow:  
   ```bash
   docker compose up -d airflow
   ```
2. Access UI:  
   ```
   http://localhost:8080
   ```
   Credentials: `admin` / `admin`  

### **Troubleshooting**  
```bash
# Reset admin user if needed
docker compose exec airflow airflow users delete -u admin
docker compose exec airflow airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com
```

### **Features**  
- Scheduled pipeline execution  
- Manual triggering via UI or API  
- Complete DVC pipeline integration