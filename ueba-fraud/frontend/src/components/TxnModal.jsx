// src/components/TxnModal.jsx
import RiskBadge from "./RiskBadge";

export default function TxnModal({ open, onClose, tx }) {
  if (!open) return null;

  const kv = (label, val, extra = "") => (
    <div className="flex justify-between gap-4 py-1">
      <div className="text-gray-500">{label}</div>
      <div className="font-medium text-right">{val}{extra}</div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-2xl rounded-xl shadow-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
          <div className="font-semibold">Transaction details</div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-800 rounded px-2 py-1"
            title="Close"
          >
            ✕
          </button>
        </div>

        <div className="p-5 space-y-4">
          {kv("Time", new Date(tx?.ts ?? Date.now()).toLocaleString())}
          {kv("User", tx?.user_name)}
          {kv("Amount", `$${(tx?.amount ?? 0).toFixed(2)}`)}
          {kv("Type", tx?.type)}
          {kv("Country", tx?.country)}
          <div className="flex justify-between gap-4 py-1">
            <div className="text-gray-500">Risk</div>
            <div><RiskBadge value={tx?.final_risk ?? 0} /></div>
          </div>

          <div className="mt-3">
            <div className="text-gray-500 mb-1">Explanations</div>
            <ul className="list-disc list-inside space-y-1">
              {(tx?.explanations ?? []).map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          </div>

          <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600 whitespace-pre-wrap">
            {JSON.stringify(tx ?? {}, null, 2)}
          </div>
        </div>
      </div>
    </div>
  );
}
