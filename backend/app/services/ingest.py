"""Persist predictions and raise alerts."""
from sqlalchemy.orm import Session
from ..config import settings
from ..models import Alert, Prediction
from .alerts import decide_alert


def save_results(db: Session, rows: list[dict], results: list[dict], source_ips=None, true_labels=None,
                 explanations=None) -> list[Prediction]:
    saved = []
    for i, (feat, res) in enumerate(zip(rows, results)):
        port = feat.get("Destination Port")
        p = Prediction(source_ip=(source_ips[i] if source_ips else None),
                       destination_port=int(port) if port is not None and port == port else None,
                       true_label=(true_labels[i] if true_labels else None),
                       features={k: float(v) for k, v in feat.items()}, **res,
                       explanation=(explanations[i] if explanations else None))
        decision = decide_alert(res["predicted_class"], res["confidence"], res["anomaly_score"],
                                settings.anomaly_alert_threshold)
        p.is_alert = decision is not None
        if decision:
            p.alert = Alert(severity=decision[0], message=decision[1])
        db.add(p)
        saved.append(p)
    db.commit()
    return saved
