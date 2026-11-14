"""Inference service: classifier + anomaly detector + explanation.

Deliberately free of FastAPI/SQLAlchemy imports so it can be tested on its own.
"""
import sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
ML_DIR = ROOT / "ml"
ARTIFACTS = ML_DIR / "artifacts"
if str(ML_DIR) not in sys.path:      # lets joblib unpickle ml/anomaly.py classes
    sys.path.insert(0, str(ML_DIR))


class ModelNotReady(RuntimeError):
    """Raised when trained model files are missing."""


class Predictor:
    def __init__(self, anomaly_model: str = "autoencoder", artifacts: Path = ARTIFACTS):
        clf_path, ano_path = artifacts / "classifier.joblib", artifacts / f"{anomaly_model}.joblib"
        for p in (clf_path, ano_path):
            if not p.exists():
                raise ModelNotReady(f"Missing {p.name}. Train first: cd ml && python train_classifier.py && python train_anomaly.py")
        self.bundle = joblib.load(clf_path)
        self.model, self.le, self.features = self.bundle["model"], self.bundle["label_encoder"], self.bundle["features"]
        self.detector = joblib.load(ano_path)["detector"]
        self.anomaly_model = anomaly_model
        self._explainer = None
        self._explainer_failed = False

    def to_frame(self, rows: list[dict]) -> tuple[pd.DataFrame, list[int]]:
        """Align raw feature dicts to training columns. Returns (frame, missing_count_per_row)."""
        clean_rows = [{str(k).strip(): v for k, v in r.items()} for r in rows]
        missing = [sum(1 for f in self.features if f not in r) for r in clean_rows]
        if min(missing) > len(self.features) * 0.5:
            raise ValueError(f"Input has too few of the {len(self.features)} expected features "
                             f"(e.g. {self.features[:3]}). Missing >50%.")
        df = pd.DataFrame(clean_rows).reindex(columns=self.features)
        df = df.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
        return df, missing

    def predict(self, X: pd.DataFrame) -> list[dict]:
        proba = self.model.predict_proba(X)
        idx = proba.argmax(axis=1)
        scores = self.detector.score(X)
        return [{"predicted_class": str(self.le.classes_[i]), "confidence": float(proba[n, i]),
                 "anomaly_score": float(scores[n])} for n, i in enumerate(idx)]

    def explain(self, X: pd.DataFrame, top_k: int = 6) -> list[dict]:
        """SHAP explanation if `shap` is installed, else clearly-labelled global importances."""
        if self._explainer is None and not self._explainer_failed:
            try:
                from explain import Explainer
                self._explainer = Explainer(bundle=self.bundle)
            except Exception:  # shap missing or incompatible
                self._explainer_failed = True
        if self._explainer is not None:
            out = self._explainer.explain(X, top_k=top_k)
            return [{"method": "shap", "top_features": o["top_features"]} for o in out]
        imp = getattr(self.model, "feature_importances_", np.zeros(len(self.features)))
        order = np.argsort(-imp)[:top_k]
        res = []
        for _, row in X.iterrows():
            res.append({"method": "feature_importance (SHAP unavailable)",
                        "top_features": [{"feature": self.features[j], "value": float(row.iloc[j]),
                                          "shap": float(imp[j])} for j in order]})
        return res


_predictor = None


def get_predictor(anomaly_model: str = "autoencoder") -> Predictor:
    global _predictor
    if _predictor is None:
        _predictor = Predictor(anomaly_model)
    return _predictor
