// Lightweight CSV builder + downloader (Excel-friendly)
export function toCSV(rows, columns) {
  // columns: [{ key: 'user_name', label: 'User' }, ...]
  const esc = (v) => {
    if (v === null || v === undefined) return '';
    const s = String(v);
    // Escape quotes; wrap if contains comma, quote or newline
    const needsWrap = /[",\n]/.test(s);
    const cleaned = s.replace(/"/g, '""');
    return needsWrap ? `"${cleaned}"` : cleaned;
  };

  const header = columns.map(c => esc(c.label ?? c.key)).join(',');
  const lines = rows.map(r =>
    columns.map(c => esc(c.format ? c.format(r[c.key], r) : r[c.key])).join(',')
  );
  return [header, ...lines].join('\r\n');
}

export function downloadText(filename, text) {
  const blob = new Blob([text], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 0);
}
