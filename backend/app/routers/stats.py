"""Aggregated statistics for the dashboard graphs."""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Alert, Prediction

router = APIRouter(prefix="/stats", tags=["stats"])


def _aware(ts: datetime) -> datetime:
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)   # SQLite returns naive datetimes


def summary_data(db: Session) -> dict:
    total = db.scalar(select(func.count(Prediction.id))) or 0
    attacks = db.scalar(select(func.count(Prediction.id)).where(Prediction.predicted_class != "Benign")) or 0
    by_class = {c: n for c, n in db.execute(select(Prediction.predicted_class, func.count(Prediction.id))
                                            .group_by(Prediction.predicted_class)).all()}
    by_status = {s: n for s, n in db.execute(select(Alert.status, func.count(Alert.id)).group_by(Alert.status)).all()}
    by_sev = {s: n for s, n in db.execute(select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)).all()}
    return {"total_flows": total, "attack_flows": attacks, "benign_flows": total - attacks,
            "avg_anomaly_score": round(db.scalar(select(func.avg(Prediction.anomaly_score))) or 0.0, 2),
            "open_alerts": by_status.get("open", 0), "alerts_by_status": by_status,
            "alerts_by_severity": by_sev, "by_class": by_class}


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return summary_data(db)


@router.get("/timeline")
def timeline(minutes: int = Query(60, ge=5, le=1440), bucket: int = Query(5, ge=1, le=60),
             db: Session = Depends(get_db)):
    """Flows per time bucket: total, attacks and mean anomaly score."""
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    rows = db.execute(select(Prediction.created_at, Prediction.predicted_class, Prediction.anomaly_score)
                      .where(Prediction.created_at >= since)).all()
    size, buckets = bucket * 60, {}
    for ts, cls, score in rows:
        key = int(_aware(ts).timestamp() // size * size)
        b = buckets.setdefault(key, {"total": 0, "attacks": 0, "score_sum": 0.0})
        b["total"] += 1
        b["attacks"] += cls != "Benign"
        b["score_sum"] += score
    return [{"t": datetime.fromtimestamp(k, timezone.utc).isoformat(), "total": b["total"], "attacks": b["attacks"],
             "benign": b["total"] - b["attacks"], "avg_anomaly": round(b["score_sum"] / b["total"], 2)}
            for k, b in sorted(buckets.items())]


@router.get("/anomaly-histogram")
def anomaly_histogram(db: Session = Depends(get_db)):
    """Distribution of anomaly scores (10 bins), split by Benign vs Attack."""
    rows = db.execute(select(Prediction.anomaly_score, Prediction.predicted_class)
                      .order_by(Prediction.id.desc()).limit(50000)).all()
    bins = [{"range": f"{i * 10}-{i * 10 + 10}", "benign": 0, "attack": 0} for i in range(10)]
    for score, cls in rows:
        bins[min(int(score // 10), 9)]["benign" if cls == "Benign" else "attack"] += 1
    return bins
