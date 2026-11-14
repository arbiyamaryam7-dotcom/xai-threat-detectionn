# Explainable AI-Based Intelligent Cyber Threat Detection and Network Anomaly Analysis System

An Explainable AI-based cybersecurity system that classifies network traffic, detects anomalous activity, and explains model predictions using SHAP.

The system combines:
- **Random Forest** for network attack classification.
- **Isolation Forest and Autoencoder** for anomaly detection.
- **SHAP** for explainable AI.
- **FastAPI** for backend services.
- **PostgreSQL** for storing predictions and alerts.
- **React + Vite** for the interactive dashboard.

## System Architecture

```text
Network Traffic
      |
      v
Data Preprocessing
      |
      +----> Random Forest Classifier
      |
      +----> Isolation Forest / Autoencoder
                       |
                       v
                SHAP Explanations
                       |
                       v
                FastAPI Backend
                       |
                       v
                  PostgreSQL
                       |
                       v
                React Dashboard
```

## Honest Project Status

The project has been successfully executed and tested in a local Windows environment.

| Component | Verified Status |
|---|---|
| Machine Learning | Random Forest, Isolation Forest and Autoencoder trained and evaluated |
| Backend | FastAPI successfully running |
| Database | PostgreSQL connection verified |
| Frontend | React + Vite application successfully launched |
| Prediction API | Single-flow and batch prediction tested |
| Explainable AI | SHAP explanation API tested |
| Live Monitor | Sample traffic simulation tested |
| Alerts | Alert generation and acknowledgement verified |
| Dashboard | Statistics and visualizations verified |
| Reports | Summary API and CSV export tested |

### Model Evaluation Results

- Classifier Accuracy: **90%**
- Macro F1-score: **81.70%**
- Weighted F1-score: **88.78%**
- Autoencoder ROC-AUC: **72.32%**
- Isolation Forest ROC-AUC: **73.31%**

The classifier was evaluated on 3,000 test samples. WebAttack classification still requires improvement.

### Testing Notes

- Batch analysis processed 2,000 sample network flows.
- SHAP returned feature-level explanations for individual predictions.
- PostgreSQL stored prediction and alert records.
- Alert acknowledgement was verified through the API and dashboard.
- Unit-test discovery: 15 tests run, 9 skipped, with no failures.

**Note:** Results are based on the project's synthetic sample dataset and local testing. They do not represent real-world network deployment performance.

## 1. Prerequisites

- Python 3.10–3.12
- Node.js 18+
- PostgreSQL 14+ or Docker
- VS Code (recommended)

## 2. Setup

Open PowerShell or a terminal in the project root folder.

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Create the environment file:

```powershell
Copy-Item .env.example .env
```

Configure the required environment variables in `.env`.

## 3. Database (PostgreSQL)

The project uses PostgreSQL to store network flow predictions and security alerts.

### Option 1: Using Docker

```bash
docker compose up -d
```

### Option 2: Using Local PostgreSQL

If Docker is not installed, start PostgreSQL and open the `psql` terminal.

Run:

```sql
CREATE USER xai_user WITH PASSWORD 'xai_pass';
CREATE DATABASE xai_threat OWNER xai_user;
```

The application automatically creates the required database tables when the backend starts.

## 4. Dataset

The repository includes `data/sample_traffic.csv`, a synthetic CIC-IDS2017-style sample dataset for testing and demonstration.

For experiments with the real CIC-IDS2017 dataset:

1. Download the CIC-IDS2017 MachineLearningCSV dataset.
2. Extract the CSV files into `data/cicids2017/`.
3. Configure `SIMULATION_CSV` in `.env` to point to the dataset directory.

See `data/README.md` for additional information.

## 5. Train the Models

Training is required before starting the backend if the model artifacts are not already available.

From the project root:

```bash
cd ml
python train_classifier.py
python train_anomaly.py
cd ..
```

For real CIC-IDS2017 data:

```bash
cd ml
python train_classifier.py --data ../data/cicids2017 --model rf
python train_anomaly.py --data ../data/cicids2017
cd ..
```

Generated model artifacts and evaluation metrics are stored in `ml/artifacts/`.

## 6. Run the Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Backend health check:

`http://localhost:8000/api/health`

Interactive API documentation:

`http://localhost:8000/docs`

## 7. Run the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the dashboard:

`http://localhost:5173`

## 8. Tests

Run from the project root after setting up the environment and training the models:

```bash
python -m unittest discover -s tests -v
```

The project also provides sample network flows for testing the prediction API and Analyze page.

## Project Structure

```text
xai-threat-detection/
|
+-- backend/
|   +-- app/
|       +-- main.py
|       +-- config.py
|       +-- database.py
|       +-- models.py
|       +-- routers/
|       +-- services/
|
+-- data/
|   +-- sample_traffic.csv
|
+-- frontend/
|   +-- src/
|       +-- pages/
|       +-- components/
|
+-- ml/
|   +-- config.py
|   +-- preprocess.py
|   +-- train_classifier.py
|   +-- train_anomaly.py
|   +-- anomaly.py
|   +-- explain.py
|
+-- tests/
|
+-- .env.example
+-- .gitignore
+-- docker-compose.yml
+-- requirements.txt
+-- README.md
```

## API Summary

The backend exposes REST APIs under the `/api` prefix.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/predict` | Predict one network flow |
| POST | `/api/predict/batch` | Analyze multiple flows |
| POST | `/api/simulate` | Simulate traffic |
| GET | `/api/examples` | Get example flows |
| GET | `/api/predictions` | List predictions |
| GET | `/api/alerts` | List security alerts |
| PATCH | `/api/alerts/{id}` | Update alert status |
| GET | `/api/model/metrics` | View model metrics |
| GET | `/api/reports/summary` | Get report summary |
| GET | `/api/reports/export.csv` | Export report as CSV |
| GET | `/api/health` | Check backend health |

## Alert Rules

- Known attack classifications can generate high- or medium-priority alerts.
- Benign classifications with high anomaly scores can generate low-priority alerts for possible unknown threats.
- Alerts can be reviewed and acknowledged through the dashboard.

## Limitations

- The current evaluation uses a synthetic CIC-IDS2017-style sample dataset, not the original full CIC-IDS2017 dataset.
- Real-world performance may differ from the reported sample evaluation metrics.
- WebAttack classification requires further improvement.
- The Live Monitor replays sample dataset rows rather than capturing actual live network packets.
- CIC-IDS2017 is a laboratory dataset from 2017 and has known dataset limitations.

## Future Enhancements

- Evaluate the system on the original CIC-IDS2017 dataset.
- Improve detection of underrepresented attack classes.
- Integrate live network traffic capture.
- Improve anomaly detection and model performance.
- Add advanced security monitoring and reporting features.

## Author

**Arbiya Maryam**

Explainable AI-Based Intelligent Cyber Threat Detection and Network Anomaly Analysis System.
