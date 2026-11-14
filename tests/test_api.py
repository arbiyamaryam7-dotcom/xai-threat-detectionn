"""End-to-end API tests using FastAPI's TestClient and a temporary SQLite DB (no PostgreSQL needed).
Requires: pip install -r requirements.txt, trained models, then run from project root:
    python -m unittest discover -s tests -v
NOTE: written but not executed in the build environment (FastAPI could not be installed there)."""
import json, os, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
_db = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"
try:
    from fastapi.testclient import TestClient
    from app.main import app
    from app.services.predictor import ARTIFACTS
    READY = (ARTIFACTS / "classifier.joblib").exists() and (ARTIFACTS / "autoencoder.joblib").exists()
except ImportError:
    READY = False
FLOWS = json.loads((ROOT / "data" / "sample_flows.json").read_text())


@unittest.skipUnless(READY, "needs fastapi/httpx installed and trained models")
class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = TestClient(app)
        cls.c = cls.ctx.__enter__()   # runs lifespan -> creates tables

    @classmethod
    def tearDownClass(cls):
        cls.ctx.__exit__(None, None, None)

    def test_1_health(self):
        self.assertEqual(self.c.get("/api/health").json()["database"], "ok")

    def test_2_predict_and_explain(self):
        r = self.c.post("/api/predict", json={"features": FLOWS[1]["features"], "source_ip": "10.0.0.9"})
        self.assertEqual(r.status_code, 200, r.text)
        d = r.json()
        self.assertIn("predicted_class", d)
        self.assertEqual(len(d["explanation"]["top_features"]), 6)

    def test_3_bad_input(self):
        self.assertEqual(self.c.post("/api/predict", json={"features": {"foo": 1}}).status_code, 422)
        self.assertEqual(self.c.post("/api/predict", json={}).status_code, 422)

    def test_4_simulate_alerts_stats(self):
        r = self.c.post("/api/simulate?count=30&attack_ratio=0.5")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(len(r.json()), 30)
        s = self.c.get("/api/stats/summary").json()
        self.assertGreaterEqual(s["total_flows"], 30)
        alerts = self.c.get("/api/alerts").json()
        self.assertTrue(alerts)
        up = self.c.patch(f"/api/alerts/{alerts[0]['id']}", json={"status": "acknowledged"})
        self.assertEqual(up.json()["status"], "acknowledged")
        self.assertEqual(self.c.patch("/api/alerts/999999", json={"status": "resolved"}).status_code, 404)
        self.assertEqual(self.c.patch(f"/api/alerts/{alerts[0]['id']}", json={"status": "bogus"}).status_code, 422)

    def test_5_reports_and_batch(self):
        self.assertEqual(self.c.get("/api/stats/timeline").status_code, 200)
        self.assertEqual(len(self.c.get("/api/stats/anomaly-histogram").json()), 10)
        self.assertIn("generated_at", self.c.get("/api/reports/summary").json())
        csv = self.c.get("/api/reports/export.csv")
        self.assertTrue(csv.text.startswith("id,created_at"))
        f = ROOT / "data" / "sample_traffic.csv"
        head = "".join(open(f).readlines()[:51])
        r = self.c.post("/api/predict/batch", files={"file": ("t.csv", head, "text/csv")})
        self.assertEqual(r.json()["processed"], 50, r.text)
        self.assertEqual(self.c.post("/api/predict/batch", files={"file": ("t.txt", "x", "text/plain")}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
