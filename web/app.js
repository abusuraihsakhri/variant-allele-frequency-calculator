"use strict";
function readCount(value, label, positive) {
  const raw = String(value ?? "").trim();
  if (!/^\d+(?:\.0+)?$/.test(raw)) {
    throw new Error(label + " must be a " + (positive ? "positive" : "nonnegative") + " whole-number read count.");
  }
  const n = Number(raw);
  if (!Number.isSafeInteger(n) || (positive ? n <= 0 : n < 0)) {
    throw new Error(label + " is outside the supported whole-number range.");
  }
  return n;
}
function calculateVaf(variantDepth, totalDepth) {
  const alt = readCount(variantDepth, "Variant depth", false);
  const total = readCount(totalDepth, "Total depth", true);
  if (alt > total) throw new Error("Variant depth cannot exceed total depth.");
  const p = alt / total, z = 1.959963984540054;
  const denominator = 1 + z * z / total;
  const center = (p + z * z / (2 * total)) / denominator;
  const half = z / denominator * Math.sqrt(p * (1 - p) / total + z * z / (4 * total * total));
  const category = p < 0.02 ? "VAF below 2%" :
    p < 0.45 ? "VAF 2% to below 45%" :
    p < 0.55 ? "VAF 45% to below 55%" : "VAF 55% or above";
  return { variant_depth: alt, total_depth: total, vaf: p, vaf_percent: p * 100,
    ci_95_low: Math.max(0, center - half), ci_95_high: Math.min(1, center + half), category };
}
function parseCsv(text) {
  if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
  const rows = []; let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (ch === '"') quoted = false;
      else cell += ch;
    } else if (ch === '"' && cell === "") quoted = true;
    else if (ch === ",") { row.push(cell); cell = ""; }
    else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); if (row.some(x => x.trim() !== "")) rows.push(row);
      row = []; cell = "";
    } else if (ch === '"') throw new Error("Malformed CSV quotation mark.");
    else cell += ch;
  }
  if (quoted) throw new Error("Malformed CSV: unterminated quoted field.");
  row.push(cell); if (row.some(x => x.trim() !== "")) rows.push(row);
  if (!rows.length) throw new Error("CSV is empty.");
  const columns = rows.shift().map(x => x.trim().toLowerCase());
  if (new Set(columns).size !== columns.length) throw new Error("CSV has duplicate column names.");
  const a = columns.indexOf("variant_depth") !== -1 ? columns.indexOf("variant_depth") : columns.indexOf("alt_depth");
  const t = columns.indexOf("total_depth") !== -1 ? columns.indexOf("total_depth") : columns.indexOf("depth");
  if (a === -1 || t === -1) throw new Error("CSV requires variant_depth (or alt_depth) and total_depth (or depth).");
  if (rows.length > 10000) throw new Error("CSV exceeds the 10,000-row browser limit.");
  return rows.map((cells, i) => {
    if (cells.length !== columns.length) return { row: i + 2, error: "Incorrect number of CSV columns" };
    try { return { row: i + 2, ...calculateVaf(cells[a], cells[t]) }; }
    catch (error) { return { row: i + 2, variant_depth: cells[a], total_depth: cells[t], error: error.message }; }
  });
}
function csvCell(value) {
  let text = String(value ?? "");
  if (/^\s*[=+@]/.test(text)) text = "'" + text;
  return '"' + text.replace(/"/g, '""') + '"';
}
function exportCsv(rows) {
  const fields = ["row","variant_depth","total_depth","vaf","vaf_percent","ci_95_low","ci_95_high","category","error"];
  return [fields.map(csvCell).join(","), ...rows.map(r => fields.map(k => csvCell(r[k])).join(","))].join("\r\n") + "\r\n";
}
if (typeof module !== "undefined" && module.exports) module.exports = { readCount, calculateVaf, parseCsv, exportCsv };
if (typeof document !== "undefined") {
  const $ = id => document.getElementById(id);
  let exportedRows = [];
  const percentage = p => (p * 100).toFixed(4) + "%";
  function updateSingle() {
    $("form-error").textContent = "";
    try {
      const r = calculateVaf($("alt").value, $("total").value);
      $("result").hidden = false;
      $("vaf-percent").textContent = percentage(r.vaf);
      $("vaf-fraction").textContent = r.vaf.toPrecision(6);
      $("ci").textContent = percentage(r.ci_95_low) + " – " + percentage(r.ci_95_high);
      $("counts").textContent = r.variant_depth.toLocaleString() + " / " + r.total_depth.toLocaleString();
      $("category").textContent = r.category;
    } catch (error) { $("result").hidden = true; $("form-error").textContent = error.message; }
  }
  $("single-form").addEventListener("submit", e => { e.preventDefault(); updateSingle(); });
  $("csv-file").addEventListener("change", async e => {
    const file = e.target.files[0]; if (!file) return;
    $("batch-error").textContent = ""; $("batch-results").hidden = true; exportedRows = [];
    if (file.size > 2 * 1024 * 1024) { $("batch-error").textContent = "File exceeds 2 MiB."; return; }
    try {
      exportedRows = parseCsv(await file.text());
      const valid = exportedRows.filter(r => !r.error).length;
      $("batch-summary").textContent = exportedRows.length + " rows · " + valid + " valid · " + (exportedRows.length - valid) + " invalid";
      const tbody = $("batch-body"); tbody.replaceChildren();
      for (const r of exportedRows.slice(0, 20)) {
        const tr = document.createElement("tr");
        for (const v of [r.row, r.error ? "—" : percentage(r.vaf), r.error || percentage(r.ci_95_low) + " – " + percentage(r.ci_95_high)]) {
          const td = document.createElement("td"); td.textContent = String(v); tr.appendChild(td);
        }
        tbody.appendChild(tr);
      }
      $("batch-results").hidden = false;
    } catch (error) { $("batch-error").textContent = error.message; }
  });
  $("export-btn").addEventListener("click", () => {
    if (!exportedRows.length) return;
    const url = URL.createObjectURL(new Blob([exportCsv(exportedRows)], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = "vaf_results.csv";
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  });
  updateSingle();
}
