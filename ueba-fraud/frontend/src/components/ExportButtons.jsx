import React from "react";
import { toCSV, downloadText } from "../utils/csv";

export default function ExportButtons({ rows = [], columns = [], filename = "export.csv" }) {
  const handleCSV = () => {
    if (!rows.length) return;
    const csv = toCSV(rows, columns);
    downloadText(filename, csv);
  };

  const handleJSON = () => {
    if (!rows.length) return;
    const pretty = JSON.stringify(rows, null, 2);
    downloadText(filename.replace(/\.csv$/i, ".json"), pretty);
  };

  return (
    <div style={{ display: "flex", gap: 8 }}>
      <button onClick={handleCSV} disabled={!rows.length}
        style={{ padding: "6px 10px", borderRadius: 6, background: "#2563eb", color: "white" }}>
        Export CSV
      </button>
      <button onClick={handleJSON} disabled={!rows.length}
        style={{ padding: "6px 10px", borderRadius: 6, background: "#475569", color: "white" }}>
        Export JSON
      </button>
    </div>
  );
}
