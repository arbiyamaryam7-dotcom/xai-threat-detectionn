import React from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

// Horizontal bars: positive SHAP values push toward the predicted class, negative push away.
export default function ShapChart({ explanation }) {
  if (!explanation) return null;
  const data = explanation.top_features.map((f) => ({
    name: f.feature, shap: Number(f.shap.toFixed(4)), value: f.value,
  }));
  const isShap = explanation.method === "shap";
  return (
    <div>
      <h4>Why this prediction? <small>({explanation.method})</small></h4>
      {!isShap && <p className="muted">SHAP is not installed on the server, so global feature importances are shown instead.</p>}
      <ResponsiveContainer width="100%" height={data.length * 34 + 30}>
        <BarChart data={data} layout="vertical" margin={{ left: 30, right: 20 }}>
          <XAxis type="number" stroke="#8b98a9" />
          <YAxis type="category" dataKey="name" width={170} stroke="#8b98a9" tick={{ fontSize: 12 }} />
          <Tooltip formatter={(v, _n, p) => [`${v} (feature value ${p.payload.value})`, isShap ? "SHAP" : "importance"]} />
          <Bar dataKey="shap">
            {data.map((d, i) => <Cell key={i} fill={d.shap >= 0 ? "#ef4444" : "#3b82f6"} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {isShap && <p className="muted">Red = pushes toward the predicted class, blue = pushes away.</p>}
    </div>
  );
}
