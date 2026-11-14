# Explainable AI-Based Intelligent Cyber Threat Detection and Network Anomaly Analysis System

Network flows are (1) **classified** into attack types (Random Forest or XGBoost), (2) scored for **anomaly**
(Isolation Forest or Autoencoder trained on benign traffic only, so it can flag unknown attacks), and
(3) **explained** with SHAP. Results are stored in PostgreSQL, exposed through FastAPI and shown in a React dashboard.

```
CIC-IDS2017 CSVs -> ml/preprocess -> ml/train_classifier  -> classifier.joblib ┐
                                  -> ml/train_anomaly     -> autoencoder.joblib ├-> backend (FastAPI) <-> PostgreSQL
                                                                                 └-> SHAP explanations      ^
                                                                 React dashboard (Vite) -- /api -----------┘
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
| Explainable AI | SHAP explanation API successfully tested |
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

- Batch analysis successfully processed 2,000 sample network flows.
- SHAP returned feature-level explanations for individual predictions.
- PostgreSQL successfully stored prediction and alert records.
- Alert acknowledgement was verified through the API and dashboard.


## 1. Prerequisites
Python 3.10–3.12, Node.js 18+, Docker (easiest for PostgreSQL) or a local PostgreSQL 14+, VS Code.

## 2. Setup
```bash
cd xai-threat-detection
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # Windows: copy .env.example .env
```

## 3. Database (PostgreSQL)
```bash
docker compose up -d                # creates DB xai_threat, user xai_user / xai_pass
```
No Docker? Install PostgreSQL, then in `psql`:
`CREATE USER xai_user WITH PASSWORD 'xai_pass'; CREATE DATABASE xai_threat OWNER xai_user;`
Tables are created automatically when the backend starts.

## 4. Dataset
See `data/README.md`. For a quick start `data/sample_traffic.csv` (synthetic) is included. For real results download
**CIC-IDS2017 MachineLearningCSV**, extract the CSVs into `data/cicids2017/`, and set `SIMULATION_CSV=data/cicids2017` in `.env`.

## 5. Train the models (required before starting the backend)
```bash
cd ml
python train_classifier.py                                            # sample data, Random Forest
python train_anomaly.py
# real data:
python train_classifier.py --data ../data/cicids2017 --model xgboost  # or --model rf
python train_anomaly.py   --data ../data/cicids2017
cd ..
```
Outputs in `ml/artifacts/`: `classifier.joblib`, `autoencoder.joblib`, `isolation_forest.joblib`, `classifier_metrics.json`,
`anomaly_metrics.json`, `confusion_matrix.png`. Retrain on your own machine: saved models depend on your scikit-learn version.

## 6. Run the backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
Check http://localhost:8000/api/health (all "ok") and interactive docs at http://localhost:8000/docs.

## 7. Run the frontend
```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

## 8. Tests
```bash
python -m unittest discover -s tests -v      # from the project root, after training
```
Test API quickly with `data/sample_flows.json` (one flow per class): paste a `features` object into the Analyze page,
or `curl -X POST localhost:8000/api/predict -H "Content-Type: application/json" -d '{"features": {...}}'`.

## Project structure and module purposes
```
ml/config.py               paths, label-mapping rules
ml/preprocess.py           load CSVs, clean inf/NaN/duplicates, map labels, stratified split
ml/generate_sample_data.py synthetic CIC-style sample (offline smoke tests only)
ml/train_classifier.py     RF/XGBoost training + metrics + confusion matrix
ml/anomaly.py              IsolationForest and Autoencoder detectors (score 0-100; 50 = 95th pct of benign)
ml/train_anomaly.py        benign-only training, ROC-AUC / precision / recall evaluation
ml/explain.py              SHAP TreeExplainer -> top contributing features per flow
backend/app/main.py        FastAPI app, CORS, error handlers, /api/health
backend/app/config.py      settings from .env           database.py / models.py  SQLAlchemy engine, tables
backend/app/services/      predictor.py (inference+explain), alerts.py (alert rules), ingest.py (DB writes)
backend/app/routers/       predict.py, alerts.py, stats.py, reports.py
frontend/src/pages/        Dashboard, LiveMonitor, Analyze, Alerts, Reports
frontend/src/components/   ShapChart (explanation bars), Common widgets
tests/                     test_ml.py, test_backend_logic.py, test_api.py
```

## API summary (prefix /api)
`POST /predict` · `POST /predict/batch` (CSV) · `POST /simulate` · `GET /examples` · `GET /predictions` ·
`GET /predictions/{id}/explain` · `GET /alerts` · `PATCH /alerts/{id}` · `GET /stats/summary|timeline|anomaly-histogram` ·
`GET /reports/summary` · `GET /reports/export.csv` · `GET /model/metrics` · `GET /health`

## Alert rules
Known attack class → **high** (confidence ≥ 90%) or **medium**. Classified Benign but anomaly score ≥ `ANOMALY_ALERT_THRESHOLD`
→ **low** ("possible unknown attack"). This is where the anomaly detector adds value beyond the classifier.

## 9. Troubleshooting / things to verify
- `models: Missing classifier.joblib` → run step 5.
- `database: error` → PostgreSQL not running or wrong `DATABASE_URL`.
- SHAP errors with XGBoost/RF: the predictor falls back to labelled global feature importances if SHAP fails to load; check the
  `method` field in the explanation. If it says SHAP is unavailable, run `pip install shap` and restart.
- Real CIC-IDS2017 has 78 features and ~2.8M rows; use `--model rf` and ≥8 GB RAM, or subsample files.
- Real-data labels such as “Web Attack � Brute Force” contain odd characters; mapping uses the `web attack` prefix, so this is handled.

## Limitations (state these in your report)
CIC-IDS2017 is a lab dataset from 2017 and known to have labelling issues; results do not guarantee real-world performance.
Rare classes (Bot, Infiltration, Heartbleed) are merged or tiny. Autoencoder here is scikit-learn's MLP (no PyTorch needed).
Simulation replays dataset rows rather than capturing live packets.
