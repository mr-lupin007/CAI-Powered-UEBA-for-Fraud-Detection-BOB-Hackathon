// src/components/RiskChart.jsx
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

export default function RiskChart({ data = [] }) {
  // expects [{tsLabel, riskPct}]
  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
      <div className="px-4 py-3 border-b border-gray-100 font-semibold">
        Risk trend
      </div>
      <div className="h-[260px] p-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="tsLabel" minTickGap={24} />
            <YAxis unit="%" domain={[0, 100]} />
            <Tooltip formatter={(v) => [`${v}%`, "risk"]} />
            <Line
              type="monotone"
              dataKey="riskPct"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
