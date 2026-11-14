import React, { useState } from "react";
import { api } from "./api";
import { useFetch } from "./hooks";
import Dashboard from "./pages/Dashboard";
import LiveMonitor from "./pages/LiveMonitor";
import Analyze from "./pages/Analyze";
import Alerts from "./pages/Alerts";
import Reports from "./pages/Reports";

const PAGES = { Dashboard, "Live Monitor": LiveMonitor, Analyze, Alerts, Reports };

export default function App() {
  const [page, setPage] = useState("Dashboard");
  const health = useFetch(api.health, 15000);
  const Page = PAGES[page];
  const h = health.data;
  const ok = h && h.database === "ok" && h.models === "ok";

  return (
    <div className="layout">
      <aside className="no-print">
        <h1>🛡 XAI Threat<br />Detection</h1>
        {Object.keys(PAGES).map((p) => (
          <button key={p} className={`nav ${p === page ? "active" : ""}`} onClick={() => setPage(p)}>{p}</button>
        ))}
        <div className="status muted">
          {health.error ? "Backend offline" : h ? (ok ? "● System healthy" : "● Degraded") : "…"}
        </div>
      </aside>
      <main>
        {h && !ok && <div className="error">⚠ {h.database !== "ok" && `Database: ${h.database}. `}{h.models !== "ok" && `Models: ${h.models}`}</div>}
        <Page />
      </main>
    </div>
  );
}
