"""Train + evaluate both anomaly detectors (benign-only training, attack-vs-benign test)."""
import argparse, json
import joblib
import numpy as np
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support, average_precision_score
from config import ARTIFACTS, SAMPLE_CSV
from anomaly import IsolationForestDetector, AutoencoderDetector
import preprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(SAMPLE_CSV))
    ap.add_argument("--max-benign", type=int, default=200000, help="cap benign training rows")
    a = ap.parse_args()
    X, y, yb = preprocess.clean(preprocess.load_csvs(a.data))
    Xtr, Xte, ytr, yte, ybtr, ybte = preprocess.split(X, y, yb)
    Xben = Xtr[ybtr == 0].head(a.max_benign)
    results = {}
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    for name, cls in [("isolation_forest", IsolationForestDetector), ("autoencoder", AutoencoderDetector)]:
        det = cls().fit(Xben)
        s = det.score(Xte)
        pred = (s > 50).astype(int)
        p, r, f, _ = precision_recall_fscore_support(ybte, pred, average="binary", zero_division=0)
        results[name] = {"roc_auc": roc_auc_score(ybte, s), "avg_precision": average_precision_score(ybte, s),
                         "precision@50": p, "recall@50": r, "f1@50": f,
                         "mean_score_benign": float(s[ybte == 0].mean()),
                         "mean_score_attack": float(s[ybte == 1].mean()),
                         "n_benign_train": len(Xben), "n_test": len(Xte)}
        joblib.dump({"detector": det, "features": list(X.columns)}, ARTIFACTS / f"{name}.joblib")
        print(name, json.dumps(results[name], indent=2))
    (ARTIFACTS / "anomaly_metrics.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
