// src/components/AnomalyCard.jsx
import { useState } from "react";

function RiskPill({ value }) {
  const pct = Math.round((value ?? 0) * 100);
  const color =
    pct >= 90
      ? "bg-red-600"
      : pct >= 75
      ? "bg-red-500"
      : pct >= 60
      ? "bg-orange-500"
      : "bg-yellow-500";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-white text-xs ${color}`}>
      {pct}% risk
    </span>
  );
}

export default function AnomalyCard({ a }) {
  const [open, setOpen] = useState(false);
  const ts = a?.ts ? new Date(a.ts) : null;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm text-slate-500">
            {ts ? ts.toLocaleString() : "—"}
          </div>
          <div className="mt-0.5 font-medium">
            {a?.user_name ?? "Unknown"} • {a?.type ?? "-"} •{" "}
            <span className="text-slate-600">
              ${Number(a?.amount || 0).toFixed(2)}
            </span>{" "}
            • {a?.country}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <RiskPill value={a?.final_risk} />
          <button
            onClick={() => setOpen((v) => !v)}
            className="text-xs px-2 py-1 border rounded hover:bg-slate-50"
            aria-label="Toggle details"
          >
            {open ? "Hide" : "Details"}
          </button>
        </div>
      </div>

      {open && (
        <div className="mt-3 border-t pt-3">
          <div className="text-xs font-semibold text-slate-600 mb-1">
            Explanations
          </div>
          <ul className="list-disc pl-5 text-sm space-y-1">
            {(a?.explanations ?? []).map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>

          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            <div className="rounded bg-slate-50 p-2">
              <div className="text-slate-500">Anomaly score</div>
              <div className="font-mono">{(a?.anomaly_score ?? 0).toFixed(3)}</div>
            </div>
            <div className="rounded bg-slate-50 p-2">
              <div className="text-slate-500">Rules score</div>
              <div className="font-mono">{(a?.rules_score ?? 0).toFixed(2)}</div>
            </div>
            <div className="rounded bg-slate-50 p-2">
              <div className="text-slate-500">User</div>
              <div className="truncate">{a?.user_id}</div>
            </div>
            <div className="rounded bg-slate-50 p-2">
              <div className="text-slate-500">Txn ID</div>
              <div className="truncate">{a?.id}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
