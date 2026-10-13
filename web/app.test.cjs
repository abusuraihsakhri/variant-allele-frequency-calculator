"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { calculateVaf, parseCsv, exportCsv } = require("./app.js");

test("VAF 30/100 and 95% Wilson limits", () => {
  const r = calculateVaf(30, 100);
  assert.equal(r.vaf, 0.3);
  assert.ok(Math.abs(r.ci_95_low - 0.21894885) < 0.00001);
  assert.ok(Math.abs(r.ci_95_high - 0.39584855) < 0.00001);
});
test("zero/all allele observations yield bounded intervals", () => {
  const a = calculateVaf(0, 100), b = calculateVaf(100, 100);
  assert.equal(a.vaf, 0);
  assert.equal(b.vaf, 1);
  assert.ok(a.ci_95_high > 0 && a.ci_95_high < 0.04);
  assert.ok(b.ci_95_low > 0.96 && b.ci_95_low < 1);
});
test("reject non-integers, unsafe numbers and bad depths", () => {
  for (const args of [[-1, 10], [1.5, 10], [11, 10], [0, 0],
    ["NaN", 10], ["Infinity", 10], [true, 10], [1, "9007199254740992"]]) {
    assert.throws(() => calculateVaf(...args));
  }
});
test("quoted CSV, alternate headers and invalid rows", () => {
  const rows = parseCsv("\uFEFFalt_depth,depth,comment\r\n0,100,\"X, Y\"\r\n1,100,ok\r\n3,2,no\r\n");
  assert.equal(rows.length, 3);
  assert.equal(rows[0].vaf, 0);
  assert.equal(rows[1].vaf, 0.01);
  assert.match(rows[2].error, /exceed/);
});
test("CSV errors on malformed and missing columns", () => {
  assert.throws(() => parseCsv("vaf,depth\n1,2\n"), /requires/);
  assert.throws(() => parseCsv("variant_depth,total_depth\n\"12,33"), /unterminated/);
  assert.throws(() => parseCsv("variant_depth,total_depth\n1\n"), /columns/);
});
test("CSV export quotes fields and neutralizes spreadsheet formulas", () => {
  const csv = exportCsv([{ row: 2, error: "=HYPERLINK(\"http://example.com\")" }]);
  assert.ok(csv.includes("'=HYPERLINK"));
  assert.ok(csv.includes('""http://example.com""'));
});
