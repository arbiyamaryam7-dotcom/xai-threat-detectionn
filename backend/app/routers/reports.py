"""Reports (JSON + CSV export) and stored model-evaluation metrics."""
import csv
import io
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Prediction
from ..services.predictor import ARTIFACTS
from .stats import summary_data

router = APIRouter(tags=["reports"])


@router.get("/reports/summary")
def report_summary(db: Session = Depends(get_db)):
    s = summary_data(db)
    top = db.execute(select(Prediction.source_ip, Prediction.predicted_class)
                     .where(Prediction.is_alert.is_(True), Prediction.source_ip.is_not(None))).all()
    counts: dict[str, int] = {}
    for ip, _ in top:
        counts[ip] = counts.get(ip, 0) + 1
    s["top_alerting_sources"] = sorted(({"source_ip": k, "alerts": v} for k, v in counts.items()),
                                       key=lambda r: -r["alerts"])[:10]
    s["generated_at"] = datetime.now(timezone.utc).isoformat()
    return s


@router.get("/reports/export.csv")
def export_csv(db: Session = Depends(get_db)):
    """Download all analysed flows (without raw features) as CSV."""
    cols = ["id", "created_at", "source_ip", "destination_port", "predicted_class", "confidence",
            "anomaly_score", "is_alert", "true_label"]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(cols)
    for p in db.scalars(select(Prediction).order_by(Prediction.id)).yield_per(1000):
        w.writerow([getattr(p, c) for c in cols])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=threat_report.csv"})


@router.get("/model/metrics")
def model_metrics():
    """Metrics written by the training scripts (real results of YOUR training run)."""
    out = {}
    for key, fn in [("classifier", "classifier_metrics.json"), ("anomaly", "anomaly_metrics.json")]:
        p = ARTIFACTS / fn
        if p.exists():
            out[key] = json.loads(p.read_text())
    if not out:
        raise HTTPException(404, "No metrics found. Run the training scripts first.")
    return out
