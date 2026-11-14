import React, { useState } from "react";
import { api } from "../api";
import { useFetch } from "../hooks";
import { Badge, ErrorBanner, pct, time } from "../components/Common";
import ShapChart from "../components/ShapChart";

export default function LiveMonitor() {
  const [auto, setAuto] = useState(true);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [selected, setSelected] = useState(null);
  const [expl, setExpl] = useState(null);
  const list = useFetch(() => api.predictions(50), auto ? 3000 : 0, [auto]);

  const simulate = async () => {
    setBusy(true);
    try { await api.simulate(20, 0.3); setErr(null); await list.reload(); } catch (e) { setErr(e.message); }
    setBusy(false);
  };
  const open = async (p) => {
    setSelected(p); setExpl(null);
    try { setExpl((await api.explain(p.id)).explanation); } catch (e) { setErr(e.message); }
  };

  return (
    <>
      <ErrorBanner error={err || list.error} />
      <div className="toolbar">
        <button onClick={simulate} disabled={busy}>{busy ? "Analysing…" : "▶ Simulate traffic (20 flows)"}</button>
        <label><input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} /> Auto-refresh (3 s)</label>
        <span className="muted">Simulation replays labelled flows from the configured dataset through the real models.</span>
      </div>
      <div className="grid2 wide-left">
        <div className="card scroll">
          <table>
            <thead><tr><th>Time</th><th>Source</th><th>Port</th><th>Prediction</th><th>Conf.</th><th>Anomaly</th><th>True label</th></tr></thead>
            <tbody>
              {(list.data || []).map((p) => (
                <tr key={p.id} className={selected?.id === p.id ? "sel" : ""} onClick={() => open(p)}>
                  <td>{time(p.created_at)}</td><td>{p.source_ip || "–"}</td><td>{p.destination_port ?? "–"}</td>
                  <td><Badge kind={p.predicted_class === "Benign" ? "ok" : "bad"}>{p.predicted_class}</Badge></td>
                  <td>{pct(p.confidence)}</td>
                  <td><span className={p.anomaly_score >= 70 ? "hot" : ""}>{p.anomaly_score.toFixed(0)}</span></td>
                  <td className="muted">{p.true_label || "–"}</td>
                </tr>
              ))}
              {list.data?.length === 0 && <tr><td colSpan="7" className="muted">No flows yet — click “Simulate traffic”.</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="card">
          {selected ? <><h3>Flow #{selected.id}: {selected.predicted_class}</h3><ShapChart explanation={expl} />{!expl && <p className="muted">Computing explanation…</p>}</>
            : <p className="muted">Click a row to see why the model classified it that way.</p>}
        </div>
      </div>
    </>
  );
}
