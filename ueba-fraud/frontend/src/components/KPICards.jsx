// src/components/KPICards.jsx
function Card({ label, value, hint }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
      {hint ? <div className="text-xs text-slate-500 mt-0.5">{hint}</div> : null}
    </div>
  );
}

export default function KPICards({ txns = [], anomalies = [], minRisk }) {
  const total = txns.length;
  const anomCount = anomalies.length;
  const highRiskPct = total > 0 ? Math.round((anomCount / total) * 100) : 0;

  // avg risk over visible txns (if field present)
  const avgRisk =
    total > 0
      ? Math.round(
          (txns.reduce((s, t) => s + (t.final_risk ?? 0), 0) / total) * 100
        )
      : 0;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <Card label="Transactions (window)" value={total} />
      <Card label="Anomalies" value={anomCount} hint={`≥ ${Math.round(minRisk * 100)}% threshold`} />
      <Card label="High-risk %" value={`${highRiskPct}%`} />
      <Card label="Avg risk (txns)" value={`${avgRisk}%`} />
    </div>
  );
}
