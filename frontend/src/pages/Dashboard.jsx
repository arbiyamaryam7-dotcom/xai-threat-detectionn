import React from "react";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import { useFetch } from "../hooks";
import { ErrorBanner, StatCard, time } from "../components/Common";

export default function Dashboard() {
  const sum = useFetch(api.summary, 5000);
  const tl = useFetch(() => api.timeline(60, 1), 5000);
  const hist = useFetch(api.histogram, 5000);
  const s = sum.data;
  const classes = s ? Object.entries(s.by_class).map(([name, count]) => ({ name, count })) : [];
  const line = (tl.data || []).map((d) => ({ ...d, label: time(d.t) }));

  return (
    <>
      <ErrorBanner error={sum.error || tl.error || hist.error} />
      <div className="grid4">
        <StatCard label="Flows analysed" value={s?.total_flows ?? "–"} />
        <StatCard label="Attacks detected" value={s?.attack_flows ?? "–"} tone="red" />
        <StatCard label="Open alerts" value={s?.open_alerts ?? "–"} tone="amber" />
        <StatCard label="Avg anomaly score" value={s?.avg_anomaly_score ?? "–"} />
      </div>
      {s && s.total_flows === 0 && <p className="muted">No data yet. Open <b>Live Monitor</b> and click “Simulate traffic”, or analyse a flow.</p>}
      <div className="grid2">
        <div className="card">
          <h3>Traffic over time (1-min buckets, last hour)</h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={line}>
              <CartesianGrid stroke="#243044" />
              <XAxis dataKey="label" stroke="#8b98a9" /><YAxis stroke="#8b98a9" allowDecimals={false} />
              <Tooltip /><Legend />
              <Line type="monotone" dataKey="benign" stroke="#22c55e" dot={false} />
              <Line type="monotone" dataKey="attacks" stroke="#ef4444" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>Predicted class distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={classes}>
              <CartesianGrid stroke="#243044" /><XAxis dataKey="name" stroke="#8b98a9" /><YAxis stroke="#8b98a9" allowDecimals={false} />
              <Tooltip /><Bar dataKey="count" fill="#6366f1" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="card">
        <h3>Anomaly score distribution (score above ~50 = more unusual than 95% of benign training traffic)</h3>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={hist.data || []}>
            <CartesianGrid stroke="#243044" /><XAxis dataKey="range" stroke="#8b98a9" /><YAxis stroke="#8b98a9" allowDecimals={false} />
            <Tooltip /><Legend />
            <Bar dataKey="benign" stackId="a" fill="#22c55e" /><Bar dataKey="attack" stackId="a" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}
