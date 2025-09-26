// src/components/RiskBadge.jsx
export default function RiskBadge({ value = 0 }) {
  const pct = Math.round((value ?? 0) * 100);
  let cls =
    "inline-flex items-center justify-center rounded-full px-2.5 py-0.5 text-xs font-semibold";
  if (pct < 30) cls += " bg-green-100 text-green-700";
  else if (pct < 70) cls += " bg-yellow-100 text-yellow-800";
  else cls += " bg-red-100 text-red-700";
  return <span className={cls}>{pct}%</span>;
}
