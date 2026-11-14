"""SHAP explanations for the tree classifier (TreeExplainer).

Explains WHY a flow was assigned its predicted class: for each flow it returns the
features with the largest SHAP contribution toward that class.
"""
import joblib
import numpy as np
from config import ARTIFACTS


class Explainer:
    def __init__(self, bundle=None, path=ARTIFACTS / "classifier.joblib"):
        import shap  # lazy import: the rest of the pipeline works without shap
        bundle = bundle or joblib.load(path)
        self.model, self.le, self.features = bundle["model"], bundle["label_encoder"], bundle["features"]
        self.explainer = shap.TreeExplainer(self.model)

    def explain(self, X, top_k=6):
        """X: DataFrame/array with columns in self.features order. Returns one dict per row."""
        X = np.asarray(X, dtype="float64")
        proba = self.model.predict_proba(X)
        cls = proba.argmax(axis=1)
        sv = self.explainer.shap_values(X, check_additivity=False)
        out = []
        for i, c in enumerate(cls):
            # older shap: list[class] of (n, f); newer shap: ndarray (n, f, class)
            vals = sv[c][i] if isinstance(sv, list) else np.asarray(sv)[i, :, c]
            order = np.argsort(-np.abs(vals))[:top_k]
            out.append({"prediction": str(self.le.classes_[c]), "confidence": float(proba[i, c]),
                        "top_features": [{"feature": self.features[j], "value": float(X[i, j]),
                                          "shap": float(vals[j])} for j in order]})
        return out
