# MLOps Accidents Project

## API Security Implementation  

I've added security features to protect API. Here's what I did in simple terms:  

### **Authentication (Login Protection)**  
- Users must log in with a **username/password** to get a special key (JWT token)  
- Without this key, you can't access private parts of the API  
- Passwords are stored as secret codes (hashed) - nobody can see the real passwords  

### **Authorization (Access Control)**  
- Two types of users:  
  - **Admins** - can access everything (like updating models)  
  - **Regular users** - limited access  
- The API checks your permissions before allowing sensitive actions  

### **Data Protection**  
- All sensitive routes require a valid token  
- Tokens expire after some time for safety  
- Input data is checked to prevent errors or attacks  

### **How to Test It**  
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
✔️ Only logged-in users can access the API  
✔️ Admins have special privileges  
✔️ Safe password storage  
✔️ Automatic token expiration  

For developers: Check the interactive docs at `http://localhost:8000/docs`!  
 
---

## **Data & Model Versioning**  
- Uses **DVC** to track all data and models  
- Automatically saves changes to:  
  - Raw data (`data/raw/`)  
  - Cleaned data (`data/preprocessed/`)  
  - Trained models (`src/models/trained_model.joblib`)  

### **Pipeline Steps**  
```bash
dvc.yaml
├── import_data    # Get data
├── preprocess    # Clean and prepare data
├── train         # Trains the ML model
└── predict       # Makes test predictions
```
---


### **Automated Model Retraining**  
- Added `/retrain` endpoint (admin-only)  
- Compares new vs production model metrics (AUC-ROC/F1)  
- Updates production model only if quality improves by >1%  

### **Retraining Script**  
```bash
./retraining_run.sh  # Runs: dvc repro evaluate
```  
- Auto-creates `prod_model.joblib` on first run  
- Can be triggered by:  
  - Cron jobs (scheduled)  
  - API calls (manual)  

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
      - src/models/prod_model.joblib # Auto-updated
```  

### **Security**  
- Admin rights required for:  
  - `/retrain`  


### **Test it:**  

**Get a token**:  
   ```bash
   curl -X POST "http://localhost:8000/auth/token" \
        -d "username=admin&password=admin123" \
        -H "Content-Type: application/x-www-form-urlencoded"
   ```

**Use the token** (replace `$TOKEN`):
```bash 
curl -X POST "http://localhost:8000/retrain" \
     -H "Authorization: Bearer $TOKEN"
```

---

### **DVC Pipeline Dockerization**  

**What I did**:  
✅ Integrated DVC into Docker containers  
✅ Configured `docker-compose.yml` for DVC + API interaction  
✅ Set up volumes for data/model synchronization  
✅ Added API endpoint (`/retrain`) to trigger DVC pipeline  
✅ Verified full pipeline execution inside containers  

**How to test**:  
1. Start services:  
   ```bash  
   docker compose up -d  
   ```  
2. Check DVC status:  
   ```bash  
   docker compose exec api bash -c "cd /app && dvc status"  
   ```  
3. Trigger retraining via API:  
   ```bash  
   curl -X POST http://localhost:8000/retrain -H "Authorization: Bearer TOKEN"  
   ```  

**Key files modified**:  
- `docker-compose.yml` (DVC service + volumes)  
- `Dockerfile` (DVC installation)    

---

## **MLflow Tracking & Dockerization**

### **MLflow Configuration**
- Tracks all experiments automatically in `./mlruns/`
- Logs:
  - Model parameters
  - Evaluation metrics (AUC)
  - Model artifacts (`.joblib` files)
- Access UI at: `http://localhost:5000`


### **Test Commands**
```bash
# Start MLflow only
docker compose up -d mlflow

# Trigger training (logs to MLflow)
docker compose run api dvc repro --force evaluate
```
 
---

## **Airflow Integration**  

I added **Airflow** to automate and schedule ML pipelines. Here's what it does in simple terms:  

### **What Airflow Does**  
- Runs ML pipelines **automatically** on a schedule  
- Can also be triggered **manually** when needed  
- Tracks all runs and errors  

### **How to Use It**  

#### **1. Manual Run**  
 - Run DAG from Airflow UI to start the pipeline immediately.
 - Call endpoint /retrain from API.


#### **2. Scheduled Runs**  
The pipeline will run:   
- You can change the schedule in:  
  ```bash
  airflow/dags/dvc_pipeline.py
  ``` 

### **How to Access**  
1. Start Airflow:  
   ```bash
   docker compose up -d airflow
   ```
2. Open Airflow UI:  
   ```
   http://localhost:8080
   ```
   Login: `admin` / `admin`  

### If you have problem logging in, run these 2 commands:
  ```bash
  # 1. delete the user admin
  docker compose exec airflow airflow users delete -u admin

  # 2. create the user admin with new password
  docker compose exec airflow airflow users create \
    --username admin \
    --password admin \ # ⚠️ or use own - strongly recommended!
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
  ```


### **What Was Added**  
1. **Airflow setup** with Docker  
2. **DAG file** (`dvc_pipeline.py`) that runs: 
   - Data loading 
   - Data preprocessing  
   - Model training  
   - Evaluation  
3. **Two ways to run**:  
   - By schedule (auto)  
   - By API call or UI (manual) 