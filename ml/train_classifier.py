"""Train a multiclass attack classifier (XGBoost if installed, else Random Forest)
and write real evaluation metrics to ml/artifacts/classifier_metrics.json."""
import argparse, json
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, ConfusionMatrixDisplay)
from sklearn.preprocessing import LabelEncoder
from config import ARTIFACTS, SAMPLE_CSV, RANDOM_STATE
import preprocess


def build_model(kind: str, n_classes: int):
    if kind == "xgboost":
        try:
            from xgboost import XGBClassifier
        except ImportError:
            raise SystemExit("xgboost not installed: pip install xgboost, or use --model rf")
        return XGBClassifier(n_estimators=200, max_depth=8, learning_rate=0.1,
                             objective="multi:softprob", tree_method="hist",
                             random_state=RANDOM_STATE, n_jobs=-1)
    return RandomForestClassifier(n_estimators=200, class_weight="balanced_subsample",
                                  n_jobs=-1, random_state=RANDOM_STATE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(SAMPLE_CSV), help="CSV file or directory of CSVs")
    ap.add_argument("--model", choices=["rf", "xgboost"], default="rf")
    a = ap.parse_args()

    X, y, yb = preprocess.clean(preprocess.load_csvs(a.data))
    Xtr, Xte, ytr, yte, _, _ = preprocess.split(X, y, yb)
    le = LabelEncoder().fit(y)
    model = build_model(a.model, len(le.classes_))
    model.fit(Xtr, le.transform(ytr))
    pred = model.predict(Xte)
    yte_enc = le.transform(yte)

    metrics = {
        "model": a.model, "data": str(a.data), "n_train": len(Xtr), "n_test": len(Xte),
        "accuracy": accuracy_score(yte_enc, pred),
        "macro_f1": f1_score(yte_enc, pred, average="macro"),
        "weighted_f1": f1_score(yte_enc, pred, average="weighted"),
        "report": classification_report(yte_enc, pred, target_names=le.classes_, output_dict=True),
        "confusion_matrix": confusion_matrix(yte_enc, pred).tolist(),
        "classes": list(le.classes_),
    }
    imp = sorted(zip(X.columns, model.feature_importances_), key=lambda t: -t[1])
    metrics["top_features"] = [(f, float(v)) for f, v in imp[:10]]

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "label_encoder": le, "features": list(X.columns)}, ARTIFACTS / "classifier.joblib")
    (ARTIFACTS / "classifier_metrics.json").write_text(json.dumps(metrics, indent=2))
    ConfusionMatrixDisplay.from_predictions(yte_enc, pred, display_labels=le.classes_, xticks_rotation=45)
    plt.tight_layout(); plt.savefig(ARTIFACTS / "confusion_matrix.png", dpi=120)
    print(classification_report(yte_enc, pred, target_names=le.classes_, digits=4))
    print(f"accuracy={metrics['accuracy']:.4f} macro_f1={metrics['macro_f1']:.4f}")


if __name__ == "__main__":
    main()
