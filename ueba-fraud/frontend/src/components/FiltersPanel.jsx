export default function FiltersPanel({ minRisk, setMinRisk, onRefresh }) {
  return (
    <div className="flex items-center gap-4 bg-white shadow-sm rounded-lg p-3 mb-4">
      <div className="text-sm">
        <span className="font-medium mr-2">Min risk:</span>
        <span className="mr-2">{Math.round(minRisk * 100)}%</span>
        <input
          type="range"
          min="0"
          max="100"
          value={Math.round(minRisk * 100)}
          onChange={(e) => setMinRisk(Number(e.target.value) / 100)}
        />
      </div>
      <button
        onClick={onRefresh}
        className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        Refresh
      </button>
    </div>
  );
}
