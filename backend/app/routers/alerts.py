"""Alert listing and triage (acknowledge / resolve / mark false positive)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import Alert
from ..schemas import AlertUpdate

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _out(a: Alert) -> dict:
    p = a.prediction
    return {"id": a.id, "prediction_id": a.prediction_id, "severity": a.severity, "status": a.status,
            "message": a.message, "created_at": a.created_at, "predicted_class": p.predicted_class,
            "anomaly_score": p.anomaly_score, "confidence": p.confidence, "source_ip": p.source_ip}


@router.get("")
def list_alerts(status: str | None = None, severity: str | None = None,
                limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    q = select(Alert).options(joinedload(Alert.prediction)).order_by(Alert.id.desc())
    if status:
        q = q.where(Alert.status == status)
    if severity:
        q = q.where(Alert.severity == severity)
    return [_out(a) for a in db.scalars(q.limit(limit)).all()]


@router.patch("/{alert_id}")
def update_alert(alert_id: int, body: AlertUpdate, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if a is None:
        raise HTTPException(404, "Alert not found")
    a.status = body.status
    db.commit()
    return _out(a)
