"""Alert decision logic (pure Python, easy to unit test)."""


def decide_alert(pred_class: str, confidence: float, anomaly_score: float, threshold: float = 70.0):
    """Return (severity, message) if an alert should be raised, else None.

    - Known attack class -> high (confidence >= 0.9) or medium.
    - Classified Benign but very anomalous -> low severity "possible unknown attack".
    """
    if pred_class != "Benign":
        sev = "high" if confidence >= 0.9 else "medium"
        return sev, f"{pred_class} traffic detected (confidence {confidence:.0%}, anomaly score {anomaly_score:.0f})"
    if anomaly_score >= threshold:
        return "low", f"Classified Benign but highly anomalous (score {anomaly_score:.0f}): possible unknown attack"
    return None
