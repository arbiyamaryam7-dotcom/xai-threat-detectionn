import React, { useState } from "react";
import { api } from "../api";
import { Badge, ErrorBanner, pct } from "../components/Common";
import ShapChart from "../components/ShapChart";

const CLASSES = ["", "Benign", "DoS", "PortScan", "BruteForce", "WebAttack"];

export default function Analyze() {
  const [text, setText] = useState("");
  const [cls, setCls] = useState("");
  const [ip, setIp] = useState("");
  const [result, setResult] = useState(null);
  const [batch, setBatch] = useState(null);
  const [truth, setTruth] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const guard = async (fn) => { setBusy(true); setErr(null); try { await fn(); } catch (e) { setErr(e.message); } setBusy(false); };

  const loadExample = () => guard(async () => {
    const ex = await api.example(cls);
    setText(JSON.stringify(ex.features, null, 2)); setTruth(ex.true_label); setResult(null);
  });
  const classify = () => guard(async () => {
    let features;
    try { features = JSON.parse(text); } catch { throw new Error("Features must be valid JSON, e.g. {\"Flow Duration\": 1200, ...}"); }
    setResult(await api.predict(features, ip));
  });
  const upload = (e) => guard(async () => {
    const f = e.target.files[0];
    if (f) setBatch(await api.batch(f));
    e.target.value = "";
  });

  return (
    <>
      <ErrorBanner error={err} />
      <div className="grid2">
        <div className="card">
          <h3>Analyse a single flow</h3>
          <div className="toolbar">
            <select value={cls} onChange={(e) => setCls(e.target.value)}>{CLASSES.map((c) => <option key={c} value={c}>{c || "Random example"}</option>)}</select>
            <button className="secondary" onClick={loadExample} disabled={busy}>Load example flow</button>
          </div>
          <input placeholder="Source IP (optional)" value={ip} onChange={(e) => setIp(e.target.value)} />
          <textarea rows="12" placeholder='Paste flow features as JSON: {"Destination Port": 80, "Flow Duration": 1234, ...}' value={text} onChange={(e) => setText(e.target.value)} />
          <button onClick={classify} disabled={busy || !text.trim()}>Classify &amp; explain</button>
          {truth && <p className="muted">Example's ground-truth label: <b>{truth}</b></p>}
        </div>
        <div className="card">
          <h3>Result</h3>
          {result ? (
            <>
              <p><Badge kind={result.predicted_class === "Benign" ? "ok" : "bad"}>{result.predicted_class}</Badge>{" "}
                confidence {pct(result.confidence)} · anomaly score <b>{result.anomaly_score.toFixed(1)}</b>/100 · {result.is_alert ? "🚨 alert raised" : "no alert"}</p>
              {result.missing_features > 0 && <p className="muted">{result.missing_features} feature(s) were missing and filled with 0.</p>}
              <ShapChart explanation={result.explanation} />
            </>
          ) : <p className="muted">Load an example (or paste your own) and press Classify.</p>}
        </div>
      </div>
      <div className="card">
        <h3>Batch analysis (CSV upload)</h3>
        <p className="muted">CIC-IDS2017-format CSV (max 2000 rows; optional “Label” column is kept for comparison).</p>
        <input type="file" accept=".csv" onChange={upload} disabled={busy} />
        {batch && <p>Processed <b>{batch.processed}</b> flows, <b>{batch.alerts}</b> alerts. Breakdown: {Object.entries(batch.by_class).map(([k, v]) => `${k}: ${v}`).join(", ")}</p>}
      </div>
    </>
  );
}
