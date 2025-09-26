// src/components/TransactionsTable.jsx
import RiskBadge from "./RiskBadge";

const fmtAmt = (n) =>
  typeof n === "number" ? `$${n.toFixed(2)}` : String(n ?? "");

const fmtTs = (s) => {
  try { return new Date(s).toLocaleString(); } catch { return s; }
};

export default function TransactionsTable({ rows = [], onRowClick }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
      <div className="px-4 py-3 border-b border-gray-100 font-semibold">
        Recent Transactions
        <span className="text-gray-500 font-normal ml-2">({rows.length})</span>
      </div>

      <div className="overflow-auto max-h-[560px]">
        <table className="min-w-full text-sm">
          <thead className="sticky top-0 bg-gray-50 text-gray-600">
            <tr>
              <th className="text-left px-4 py-2 w-[200px]">Time</th>
              <th className="text-left px-4 py-2">User</th>
              <th className="text-right px-4 py-2">Amt</th>
              <th className="text-left px-4 py-2">Type</th>
              <th className="text-left px-4 py-2">Country</th>
              <th className="text-right px-4 py-2">Risk</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr
                key={r.id}
                className="hover:bg-gray-50 cursor-pointer border-b border-gray-50"
                onClick={() => onRowClick?.(r)}
              >
                <td className="px-4 py-2 text-gray-700">{fmtTs(r.ts)}</td>
                <td className="px-4 py-2">{r.user_name ?? "—"}</td>
                <td className="px-4 py-2 text-right tabular-nums">
                  {fmtAmt(r.amount)}
                </td>
                <td className="px-4 py-2">{r.type ?? "—"}</td>
                <td className="px-4 py-2">{r.country ?? "—"}</td>
                <td className="px-4 py-2 text-right">
                  <RiskBadge value={r.final_risk ?? 0} />
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td className="px-4 py-6 text-center text-gray-500" colSpan={6}>
                  No transactions yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
