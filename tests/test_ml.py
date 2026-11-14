"""Unit tests for the ML core. Run from project root: python -m unittest discover -s tests -v"""
import sys, unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ml"))
import preprocess
from anomaly import IsolationForestDetector, AutoencoderDetector
from config import SAMPLE_CSV


class TestPreprocess(unittest.TestCase):
    def test_label_mapping(self):
        m = preprocess.map_label
        self.assertEqual(m("BENIGN"), "Benign")
        self.assertEqual(m("DoS slowloris"), "DoS")
        self.assertEqual(m("DDoS"), "DoS")
        self.assertEqual(m("FTP-Patator"), "BruteForce")
        self.assertEqual(m("Web Attack - XSS"), "WebAttack")
        self.assertEqual(m("something new"), "Other")

    def test_clean_removes_inf_nan_duplicates(self):
        df = pd.DataFrame({"a": [1.0, np.inf, np.nan, 1.0, 2.0], "Label": ["BENIGN"] * 4 + ["PortScan"]})
        X, y, yb = preprocess.clean(df)
        self.assertEqual(len(X), 2)
        self.assertEqual(list(yb), [0, 1])

    def test_missing_file_and_label(self):
        with self.assertRaises(FileNotFoundError):
            preprocess.load_csvs("does_not_exist.csv")


class TestAnomaly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        X, y, yb = preprocess.clean(preprocess.load_csvs(SAMPLE_CSV))
        cls.X, cls.yb = X, yb

    def test_scores_in_range_and_separate(self):
        for cls in (IsolationForestDetector, AutoencoderDetector):
            det = cls().fit(self.X[self.yb == 0].head(2000))
            s = det.score(self.X.head(1000))
            self.assertTrue(((s >= 0) & (s <= 100)).all())
            yb = self.yb.head(1000)
            self.assertGreater(s[yb == 1].mean(), s[yb == 0].mean())


if __name__ == "__main__":
    unittest.main()
