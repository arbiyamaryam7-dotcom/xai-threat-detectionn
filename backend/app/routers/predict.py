"""Prediction endpoints: single flow, CSV batch, simulated traffic, history, SHAP explanation."""
import io
import random
import sys
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..models import Prediction
from ..schemas import FlowInput, PredictionDetail, PredictionRow
from ..services.ingest import save_results
from ..services.predictor import ML_DIR, get_predictor

if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))
import preprocess  # noqa: E402  (ml/preprocess.py)

router = APIRouter(tags=["predictions"])
_pool = None


def _predictor():
    return get_predictor(settings.anomaly_model)


def _sim_pool():
    """Labelled flows used for traffic simulation (cached). Cleaned exactly like training data."""
    global _pool
    if _pool is None:
        try:
            X, y, _ = preprocess.clean(preprocess.load_csvs(settings.simulation_csv))
        except (FileNotFoundError, ValueError) as e:
            raise HTTPException(503, f"Simulation data unavailable: {e}")
        if len(X) > 20000:
            keep = X.sample(20000, random_state=1).index
            X, y = X.loc[keep].reset_index(drop=True), y.loc[keep].reset_index(drop=True)
        _pool = (X, y)
    return _pool


def _detail(p: Prediction, missing: int = 0) -> PredictionDetail:
    d = PredictionDetail.model_validate(p, from_attributes=True)
    d.missing_features = missing
    return d


@router.post("/predict", response_model=PredictionDetail)
def predict_one(flow: FlowInput, db: Session = Depends(get_db)):
    """Classify one flow, score its anomaly, and attach a SHAP explanation."""
    pr = _predictor()
    try:
        X, missing = pr.to_frame([flow.features])
    except ValueError as e:
        raise HTTPException(422, str(e))
    res = pr.predict(X)
    expl = pr.explain(X)
    p = save_results(db, [X.iloc[0].to_dict()], res, [flow.source_ip], explanations=expl)[0]
    return _detail(p, missing[0])


@router.post("/predict/batch")
async def predict_batch(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV of flows (CIC-IDS2017 columns). An optional 'Label' column is kept as true_label."""
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a .csv file")
    try:
        df = pd.read_csv(io.BytesIO(await file.read()))
    except Exception as e:
        raise HTTPException(400, f"Could not parse CSV: {e}")
    df.columns = [c.strip() for c in df.columns]
    if df.empty:
        raise HTTPException(400, "CSV is empty")
    df = df.head(settings.max_batch_rows)
    true = df.pop("Label").map(preprocess.map_label).tolist() if "Label" in df.columns else None
    pr = _predictor()
    try:
        X, _ = pr.to_frame(df.to_dict("records"))
    except ValueError as e:
        raise HTTPException(422, str(e))
    res = pr.predict(X)
    saved = save_results(db, X.to_dict("records"), res, true_labels=true)
    by_class: dict[str, int] = {}
    for r in res:
        by_class[r["predicted_class"]] = by_class.get(r["predicted_class"], 0) + 1
    return {"processed": len(saved), "alerts": sum(p.is_alert for p in saved),
            "by_class": by_class, "truncated_to": settings.max_batch_rows if len(df) == settings.max_batch_rows else None}


@router.post("/simulate", response_model=list[PredictionRow])
def simulate(count: int = Query(20, ge=1, le=200), attack_ratio: float = Query(0.3, ge=0, le=1),
             db: Session = Depends(get_db)):
    """Replay random labelled flows through the full pipeline to drive the live monitor (demo/testing)."""
    X, y = _sim_pool()
    n_att = int(round(count * attack_ratio))
    att, ben = y[y != "Benign"].index, y[y == "Benign"].index
    idx = (random.sample(list(att), min(n_att, len(att))) + random.sample(list(ben), min(count - n_att, len(ben))))
    random.shuffle(idx)
    pr = _predictor()
    sub = X.loc[idx]
    X2, _ = pr.to_frame(sub.to_dict("records"))
    res = pr.predict(X2)
    ips = [f"10.0.{random.randint(0, 5)}.{random.randint(2, 250)}" for _ in idx]
    return save_results(db, X2.to_dict("records"), res, ips, true_labels=y.loc[idx].tolist())


@router.get("/examples")
def example_flow(cls: str | None = None):
    """Return a random example flow (features + true label) to try in the Analyze page."""
    X, y = _sim_pool()
    pool = y[y == cls].index if cls else y.index
    if len(pool) == 0:
        raise HTTPException(404, f"No example for class '{cls}'")
    i = random.choice(list(pool))
    return {"features": X.loc[i].to_dict(), "true_label": y.loc[i]}


@router.get("/predictions", response_model=list[PredictionRow])
def list_predictions(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0),
                     cls: str | None = None, alerts_only: bool = False, db: Session = Depends(get_db)):
    q = select(Prediction).order_by(Prediction.id.desc())
    if cls:
        q = q.where(Prediction.predicted_class == cls)
    if alerts_only:
        q = q.where(Prediction.is_alert.is_(True))
    return db.scalars(q.limit(limit).offset(offset)).all()


@router.get("/predictions/{pid}/explain", response_model=PredictionDetail)
def explain_prediction(pid: int, db: Session = Depends(get_db)):
    """Return (computing + caching if needed) the SHAP explanation of a stored prediction."""
    p = db.get(Prediction, pid)
    if p is None:
        raise HTTPException(404, "Prediction not found")
    if p.explanation is None:
        pr = _predictor()
        X, _ = pr.to_frame([p.features])
        p.explanation = pr.explain(X)[0]
        db.commit()
    return _detail(p)
