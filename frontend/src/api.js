// Thin fetch wrapper around the FastAPI backend. Throws Error with the backend's message.
const BASE = import.meta.env.VITE_API_URL || "/api";

async function req(path, opts = {}) {
  let res;
  try {
    res = await fetch(BASE + path, opts);
  } catch {
    throw new Error("Cannot reach the backend. Is it running on port 8000?");
  }
  if (!res.ok) {
    let msg = `Request failed (HTTP ${res.status})`;
    try {
      const body = await res.json();
      msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch { /* keep default message */ }
    throw new Error(msg);
  }
  return res.json();
}

const json = (method, body) => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

export const api = {
  health: () => req("/health"),
  summary: () => req("/stats/summary"),
  timeline: (minutes = 60, bucket = 5) => req(`/stats/timeline?minutes=${minutes}&bucket=${bucket}`),
  histogram: () => req("/stats/anomaly-histogram"),
  predictions: (limit = 50) => req(`/predictions?limit=${limit}`),
  explain: (id) => req(`/predictions/${id}/explain`),
  predict: (features, source_ip) => req("/predict", json("POST", { features, source_ip: source_ip || null })),
  example: (cls) => req(`/examples${cls ? `?cls=${cls}` : ""}`),
  simulate: (count, ratio) => req(`/simulate?count=${count}&attack_ratio=${ratio}`, { method: "POST" }),
  batch: (file) => { const f = new FormData(); f.append("file", file); return req("/predict/batch", { method: "POST", body: f }); },
  alerts: (status) => req(`/alerts${status ? `?status=${status}` : ""}`),
  updateAlert: (id, status) => req(`/alerts/${id}`, json("PATCH", { status })),
  report: () => req("/reports/summary"),
  metrics: () => req("/model/metrics"),
  csvUrl: `${BASE}/reports/export.csv`,
};
