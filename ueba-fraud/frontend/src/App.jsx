// src/App.jsx
import { useEffect, useMemo, useState } from "react";
import { getHealth, getTransactions, getAnomalies } from "./apis/api";
import TransactionsTable from "./components/TransactionsTable";
import RiskChart from "./components/RiskChart";
import TxnModal from "./components/TxnModal";
import RiskBadge from "./components/RiskBadge";

/* ---------------- CSV helpers ---------------- */
const csvEscape = (v) => {
  if (v === null || v === undefined) return "";
  const s = String(v);
  // escape " and wrap in quotes if contains comma/quote/newline
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
};
const downloadText = (filename, text, mime = "text/csv;charset=utf-8") => {
  // add BOM so Excel opens UTF-8 nicely
  const blob = new Blob(["\uFEFF" + text], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};
const txnsToCSV = (rows) => {
  const headers = [
    "ts",
    "user_name",
    "user_id",
    "amount",
    "type",
    "country",
    "final_risk",
    "anomaly_score",
    "rules_score",
    "explanations",
  ];
  const body = (rows || []).map((r) => [
    new Date(r.ts).toISOString(),
    r.user_name ?? "",
    r.user_id ?? "",
    r.amount ?? "",
    r.type ?? "",
    r.country ?? "",
    (r.final_risk ?? 0).toFixed(4),
    r.anomaly_score ?? "",
    r.rules_score ?? "",
    (r.explanations ?? []).join(" | "),
  ]);
  return [headers, ...body]
    .map((row) => row.map(csvEscape).join(","))
    .join("\n");
};
const anomsToCSV = (rows) => {
  const headers = [
    "ts",
    "user_name",
    "amount",
    "type",
    "country",
    "final_risk",
    "explanations",
  ];
  const body = (rows || []).map((r) => [
    new Date(r.ts).toISOString(),
    r.user_name ?? "",
    r.amount ?? "",
    r.type ?? "",
    r.country ?? "",
    (r.final_risk ?? 0).toFixed(4),
    (r.explanations ?? []).join(" | "),
  ]);
  return [headers, ...body]
    .map((row) => row.map(csvEscape).join(","))
    .join("\n");
};
/* ---------------------------------------------- */

export default function App() {
  const [health, setHealth] = useState(null);
  const [txns, setTxns] = useState([]);
  const [anoms, setAnoms] = useState([]);
  const [minRisk, setMinRisk] = useState(0.7);
  const [limit, setLimit] = useState(50);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const [selected, setSelected] = useState(null);
  const [auto, setAuto] = useState(true);

  async function refresh() {
    try {
      setLoading(true);
      setErr(null);
      const [h, t, a] = await Promise.all([
        getHealth(),
        getTransactions(limit),
        getAnomalies(minRisk, 20),
      ]);
      setHealth(h);
      setTxns(Array.isArray(t) ? t : []);
      setAnoms(Array.isArray(a) ? a : []);
    } catch (e) {
      console.error(e);
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, [minRisk, limit]);

  useEffect(() => {
    if (!auto) return;
    const id = setInterval(refresh, 4000);
    return () => clearInterval(id);
  }, [auto, minRisk, limit]);

  const filtered = useMemo(() => {
    if (!query) return txns;
    const q = query.toLowerCase();
    return txns.filter((r) =>
      (r.user_name ?? "").toLowerCase().includes(q) ||
      (r.country ?? "").toLowerCase().includes(q) ||
      (r.type ?? "").toLowerCase().includes(q)
    );
  }, [txns, query]);

  const chartData = useMemo(
    () =>
      txns
        .slice()
        .reverse()
        .slice(0, 40)
        .map((r) => ({
          tsLabel: new Date(r.ts).toLocaleTimeString(),
          riskPct: Math.round((r.final_risk ?? 0) * 100),
        })),
    [txns]
  );

  /* ---- CSV button actions ---- */
  const exportFilteredTxnsCSV = () => {
    const csv = txnsToCSV(filtered);
    downloadText(`transactions_${filtered.length}.csv`, csv);
  };
  const exportAnomsCSV = () => {
    const csv = anomsToCSV(anoms);
    downloadText(`anomalies_${anoms.length}.csv`, csv);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* HEADER */}
      <header className="sticky top-0 z-10 bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-4">
          <h1 className="text-xl font-bold">UEBA Dashboard</h1>
          <div className="flex items-center gap-2 ml-auto">
            <span className="text-gray-500">Backend:</span>
            <span className={health?.ok ? "text-green-700" : "text-red-700"}>
              {health?.ok ? "OK" : "DOWN"}
            </span>

            <label className="ml-4 text-gray-600">
              Min risk: <b>{Math.round(minRisk * 100)}%</b>
              <input
                className="ml-2 align-middle"
                type="range"
                min="0.5"
                max="0.95"
                step="0.01"
                value={minRisk}
                onChange={(e) => setMinRisk(parseFloat(e.target.value))}
              />
            </label>

            <label className="ml-4 text-gray-600">
              Limit:
              <select
                className="ml-2 border rounded px-1 py-0.5"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
              >
                {[20, 50, 100].map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </label>

            <input
              className="ml-4 border rounded px-2 py-1"
              placeholder="Search user/country/type…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />

            <label className="ml-3 text-gray-600 flex items-center gap-2">
              <input
                type="checkbox"
                checked={auto}
                onChange={(e) => setAuto(e.target.checked)}
              />
              Auto-refresh
            </label>

            <button
              onClick={refresh}
              className="ml-2 inline-flex items-center rounded-lg bg-blue-600 text-white px-3 py-1.5 hover:bg-blue-700"
            >
              {loading ? "Refreshing…" : "Refresh"}
            </button>
          </div>
        </div>
      </header>

      {/* BODY */}
      <main className="max-w-7xl mx-auto px-4 py-5 space-y-5">
        {err && (
          <div className="bg-red-50 text-red-700 border border-red-200 rounded-lg px-4 py-2">
            {err}
          </div>
        )}

        {/* Top grid: table + chart */}
        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-7">
            {/* small toolbar above table for CSV export */}
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-gray-500">
                Showing <b>{filtered.length}</b> of <b>{txns.length}</b> txns
              </div>
              <button
                onClick={exportFilteredTxnsCSV}
                className="inline-flex items-center text-sm rounded-lg border border-gray-300 bg-white px-3 py-1.5 hover:bg-gray-50"
                title="Download currently visible transactions as CSV"
              >
                Export CSV
              </button>
            </div>

            <TransactionsTable rows={filtered} onRowClick={setSelected} />
          </div>

          <div className="col-span-5 space-y-5">
            <RiskChart data={chartData} />

            <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
              <div className="px-4 py-3 border-b border-gray-100 font-semibold flex items-center justify-between">
                <span>
                  Anomalies{" "}
                  <span className="text-gray-500 font-normal">({anoms.length})</span>
                </span>
                <button
                  onClick={exportAnomsCSV}
                  className="inline-flex items-center text-sm rounded-lg border border-gray-300 bg-white px-3 py-1.5 hover:bg-gray-50"
                  title="Download anomalies as CSV"
                >
                  Export CSV
                </button>
              </div>
              <ul className="max-h-[260px] overflow-auto divide-y divide-gray-100">
                {anoms.length === 0 && (
                  <li className="px-4 py-6 text-gray-500">No anomalies at this threshold.</li>
                )}
                {anoms.map((a) => (
                  <li key={a.id} className="px-4 py-3">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">{a.user_name ?? "Unknown user"}</div>
                      <RiskBadge value={a.final_risk ?? 0} />
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(a.ts).toLocaleString()} • {a.type} • {a.country} • $
                      {Number(a.amount ?? 0).toFixed(2)}
                    </div>
                    <ul className="list-disc list-inside text-sm mt-1 text-gray-700">
                      {(a.explanations ?? []).slice(0, 3).map((e, i) => (<li key={i}>{e}</li>))}
                    </ul>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <footer className="text-xs text-gray-500 py-2">
          Auto refresh: {auto ? "ON" : "OFF"} • Showing {filtered.length} of {txns.length} txns
        </footer>
      </main>

      {/* MODAL */}
      <TxnModal open={!!selected} tx={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
