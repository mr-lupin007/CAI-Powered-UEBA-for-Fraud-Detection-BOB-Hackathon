import React, { useMemo, useState } from "react";

function Bar({ pct }) {
  return (
    <div style={{ width: 120, height: 8, background: "#e5e7eb", borderRadius: 999 }}>
      <div style={{
        width: `${Math.min(100, Math.max(0, pct*100))}%`,
        height: "100%",
        background: pct >= 0.75 ? "#ef4444" : pct >= 0.5 ? "#f59e0b" : "#22c55e",
        borderRadius: 999
      }}/>
    </div>
  );
}

/**
 * props:
 *  - txns: array of transactions (with user_name, final_risk)
 *  - anoms: array of anomalies (subset of txns is fine)
 */
export default function Leaderboard({ txns = [], anoms = [] }) {
  const [mode, setMode] = useState("risk"); // "risk" | "count"

  const top = useMemo(() => {
    if (mode === "count") {
      const byUser = new Map();
      for (const a of anoms) {
        const k = a.user_id ?? a.user_name ?? "Unknown";
        const name = a.user_name ?? k;
        const cur = byUser.get(k) ?? { user_id: k, user_name: name, count: 0 };
        cur.count += 1;
        byUser.set(k, cur);
      }
      return [...byUser.values()]
        .sort((a, b) => b.count - a.count)
        .slice(0, 5);
    } else {
      const byUser = new Map();
      for (const t of txns) {
        const k = t.user_id ?? t.user_name ?? "Unknown";
        const name = t.user_name ?? k;
        const cur = byUser.get(k) ?? { user_id: k, user_name: name, sum: 0, n: 0 };
        cur.sum += Number(t.final_risk ?? 0);
        cur.n += 1;
        byUser.set(k, cur);
      }
      return [...byUser.values()]
        .filter(x => x.n > 0)
        .map(x => ({ ...x, avg: x.sum / x.n }))
        .sort((a, b) => b.avg - a.avg)
        .slice(0, 5);
    }
  }, [mode, txns, anoms]);

  return (
    <section style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
                    padding: "10px 12px", borderBottom: "1px solid #e5e7eb" }}>
        <div style={{ fontWeight: 700 }}>Top 5 Users — {mode === "count" ? "Anomaly Count" : "Avg Risk"}</div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => setMode("risk")}
            style={{ padding: "4px 8px", borderRadius: 6, background: mode==="risk" ? "#111827" : "#e5e7eb",
                     color: mode==="risk" ? "#fff" : "#111827" }}>
            Avg Risk
          </button>
          <button onClick={() => setMode("count")}
            style={{ padding: "4px 8px", borderRadius: 6, background: mode==="count" ? "#111827" : "#e5e7eb",
                     color: mode==="count" ? "#fff" : "#111827" }}>
            Anomaly Count
          </button>
        </div>
      </div>

      <div style={{ padding: 12 }}>
        {top.length === 0 ? (
          <div style={{ color: "#6b7280" }}>No data yet.</div>
        ) : (
          <ol style={{ display: "grid", gap: 10, margin: 0, paddingLeft: 16 }}>
            {top.map((row, i) => (
              <li key={row.user_id ?? row.user_name} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ width: 18, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>{i+1}.</div>
                <div style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {row.user_name}
                </div>
                {mode === "count" ? (
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <strong>{row.count}</strong>
                  </div>
                ) : (
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <Bar pct={row.avg}/>
                    <div style={{ width: 52, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                      {(row.avg*100).toFixed(0)}%
                    </div>
                  </div>
                )}
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  );
}
