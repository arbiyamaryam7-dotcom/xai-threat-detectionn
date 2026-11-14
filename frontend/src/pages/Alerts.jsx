import React, { useState } from "react";
import { api } from "../api";
import { useFetch } from "../hooks";
import { Badge, ErrorBanner, pct } from "../components/Common";

const SEV = { high: "bad", medium: "warn", low: "info" };

export default function Alerts() {
  const [status, setStatus] = useState("open");
  const [err, setErr] = useState(null);
  const list = useFetch(() => api.alerts(status), 5000, [status]);

  const act = async (id, s) => {
    try { await api.updateAlert(id, s); setErr(null); list.reload(); } catch (e) { setErr(e.message); }
  };

  return (
    <>
      <ErrorBanner error={err || list.error} />
      <div className="toolbar">
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          {["open", "acknowledged", "resolved", "false_positive", ""].map((s) => <option key={s} value={s}>{s || "all"}</option>)}
        </select>
      </div>
      <div className="card scroll">
        <table>
          <thead><tr><th>#</th><th>Severity</th><th>Class</th><th>Message</th><th>Source</th><th>Anomaly</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            {(list.data || []).map((a) => (
              <tr key={a.id}>
                <td>{a.id}</td><td><Badge kind={SEV[a.severity]}>{a.severity}</Badge></td><td>{a.predicted_class}</td>
                <td>{a.message}</td><td>{a.source_ip || "–"}</td><td>{a.anomaly_score.toFixed(0)}</td><td>{a.status}</td>
                <td className="actions">
                  <button className="small" onClick={() => act(a.id, "acknowledged")}>Ack</button>
                  <button className="small" onClick={() => act(a.id, "resolved")}>Resolve</button>
                  <button className="small secondary" onClick={() => act(a.id, "false_positive")}>False +</button>
                </td>
              </tr>
            ))}
            {list.data?.length === 0 && <tr><td colSpan="8" className="muted">No alerts with this status.</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
