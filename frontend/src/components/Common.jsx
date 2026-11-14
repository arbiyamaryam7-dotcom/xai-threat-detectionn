import React from "react";

export const StatCard = ({ label, value, tone = "" }) => (
  <div className={`card stat ${tone}`}>
    <div className="stat-label">{label}</div>
    <div className="stat-value">{value}</div>
  </div>
);

export const Badge = ({ kind, children }) => <span className={`badge ${kind}`}>{children}</span>;

export const ErrorBanner = ({ error }) => (error ? <div className="error">⚠ {error}</div> : null);

export const pct = (x) => `${(x * 100).toFixed(1)}%`;
export const time = (iso) => new Date(iso).toLocaleTimeString();
