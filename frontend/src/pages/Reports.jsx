import React from "react";
import { api } from "../api";
import { useFetch } from "../hooks";
import { ErrorBanner, pct } from "../components/Common";

export default function Reports() {
  const rep = useFetch(api.report);
  const met = useFetch(api.metrics);
  const r = rep.data;
  const c = met.data?.classifier;
  const a = met.data?.anomaly;

  return (
    <div className="report">
      <div className="toolbar no-print">
        <button onClick={rep.reload}>↻ Refresh</button>
        <a className="btn" href={api.csvUrl}>⬇ Export predictions (CSV)</a>
        <button className="secondary" onClick={() => window.print()}>🖨 Print / Save as PDF</button>
      </div>
      <ErrorBanner error={rep.error} />
      {r && (
        <div className="card">
          <h3>Threat summary <small className="muted">generated {new Date(r.generated_at).toLocaleString()}</small></h3>
          <p>{r.total_flows} flows analysed · {r.attack_flows} classified as attacks · {r.open_alerts} open alerts · mean anomaly score {r.avg_anomaly_score}</p>
          <div className="grid2">
            <table><thead><tr><th>Class</th><th>Flows</th></tr></thead><tbody>
              {Object.entries(r.by_class).map(([k, v]) => <tr key={k}><td>{k}</td><td>{v}</td></tr>)}</tbody></table>
            <table><thead><tr><th>Top alerting sources</th><th>Alerts</th></tr></thead><tbody>
              {r.top_alerting_sources.map((s) => <tr key={s.source_ip}><td>{s.source_ip}</td><td>{s.alerts}</td></tr>)}
              {r.top_alerting_sources.length === 0 && <tr><td colSpan="2" className="muted">none</td></tr>}</tbody></table>
          </div>
        </div>
      )}
      <div className="card">
        <h3>Model evaluation (from your training run)</h3>
        {met.error && <p className="muted">{met.error}</p>}
        {c && (
          <>
            <p><b>Classifier:</b> {c.model} · trained on {c.n_train} / tested on {c.n_test} flows · accuracy {pct(c.accuracy)} · macro-F1 {c.macro_f1.toFixed(3)}</p>
            <p className="muted">Data source: {c.data}</p>
            <table><thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr></thead><tbody>
              {c.classes.map((k) => <tr key={k}><td>{k}</td><td>{c.report[k].precision.toFixed(3)}</td><td>{c.report[k].recall.toFixed(3)}</td><td>{c.report[k]["f1-score"].toFixed(3)}</td><td>{c.report[k].support}</td></tr>)}
            </tbody></table>
          </>
        )}
        {a && (
          <table><thead><tr><th>Anomaly detector</th><th>ROC-AUC</th><th>Precision@50</th><th>Recall@50</th><th>F1@50</th></tr></thead><tbody>
            {Object.entries(a).map(([k, v]) => <tr key={k}><td>{k}</td><td>{v.roc_auc.toFixed(3)}</td><td>{v["precision@50"].toFixed(3)}</td><td>{v["recall@50"].toFixed(3)}</td><td>{v["f1@50"].toFixed(3)}</td></tr>)}
          </tbody></table>
        )}
      </div>
    </div>
  );
}
