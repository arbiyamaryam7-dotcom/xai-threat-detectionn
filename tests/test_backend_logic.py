"""Tests for inference + alert logic. Need trained models (cd ml && python train_classifier.py && python train_anomaly.py).
Run from project root: python -m unittest discover -s tests -v"""
import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.services.alerts import decide_alert
from app.services.predictor import ARTIFACTS, ModelNotReady, Predictor

HAVE_MODELS = (ARTIFACTS / "classifier.joblib").exists() and (ARTIFACTS / "autoencoder.joblib").exists()
FLOWS = json.loads((ROOT / "data" / "sample_flows.json").read_text())


class TestAlertLogic(unittest.TestCase):
    def test_attack_high_and_medium(self):
        self.assertEqual(decide_alert("DoS", 0.95, 80)[0], "high")
        self.assertEqual(decide_alert("DoS", 0.6, 80)[0], "medium")

    def test_benign_quiet_vs_anomalous(self):
        self.assertIsNone(decide_alert("Benign", 0.99, 20))
        self.assertEqual(decide_alert("Benign", 0.99, 90)[0], "low")


@unittest.skipUnless(HAVE_MODELS, "train models first")
class TestPredictor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = Predictor("autoencoder")

    def test_predict_shapes_and_ranges(self):
        X, missing = self.p.to_frame([f["features"] for f in FLOWS])
        res = self.p.predict(X)
        self.assertEqual(len(res), 5)
        for r in res:
            self.assertIn(r["predicted_class"], list(self.p.le.classes_))
            self.assertTrue(0 <= r["confidence"] <= 1 and 0 <= r["anomaly_score"] <= 100)
        self.assertEqual(missing, [0] * 5)

    def test_missing_features_filled_and_rejected(self):
        X, missing = self.p.to_frame([{"Flow Duration": 5, "Destination Port": 80, "Total Fwd Packets": 2,
                                       "Total Backward Packets": 1, "Flow Bytes/s": 10, "Flow Packets/s": 1,
                                       "SYN Flag Count": 1, "ACK Flag Count": 1, "RST Flag Count": 0, "Idle Mean": 0}])
        self.assertGreater(missing[0], 0)
        with self.assertRaises(ValueError):
            self.p.to_frame([{"foo": 1}])

    def test_explanation_structure(self):
        X, _ = self.p.to_frame([FLOWS[1]["features"]])
        e = self.p.explain(X)[0]
        self.assertIn("method", e)
        self.assertEqual(len(e["top_features"]), 6)
        self.assertTrue({"feature", "value", "shap"} <= set(e["top_features"][0]))

    def test_missing_model_error(self):
        with self.assertRaises(ModelNotReady):
            Predictor("autoencoder", artifacts=ROOT / "nonexistent")


if __name__ == "__main__":
    unittest.main()
