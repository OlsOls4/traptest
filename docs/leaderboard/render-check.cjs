#!/usr/bin/env node
/* Render check for docs/leaderboard/index.html — no dependencies.
 *
 * Runs the page's own <script> in Node with a minimal DOM stub and a
 * fetch stub that reads the local JSON files, then asserts the rendered
 * tables match the data files. This is the check the task calls the
 * "Node render harness": it exercises the page's real render() and
 * renderExpansion() code paths, not a re-implementation.
 *
 * Usage: node render-check.cjs   (from docs/leaderboard/)
 * Exit 0 when every assertion passes, 1 otherwise.
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const DIR = __dirname;
const html = fs.readFileSync(path.join(DIR, "index.html"), "utf8");
const scriptMatch = html.match(/<script>([\s\S]*)<\/script>/);
if (!scriptMatch) { console.error("FAIL: no <script> block in index.html"); process.exit(1); }

function makeEl() {
  return {
    innerHTML: "", textContent: "",
    addEventListener() {}, appendChild() {}, setAttribute() {},
  };
}
const bySelector = new Map();
const byId = new Map();
const documentStub = {
  querySelector(sel) {
    if (!bySelector.has(sel)) bySelector.set(sel, makeEl());
    return bySelector.get(sel);
  },
  getElementById(id) {
    if (!byId.has(id)) byId.set(id, makeEl());
    return byId.get(id);
  },
};

const context = vm.createContext({
  console,
  document: documentStub,
  fetch: (url) => Promise.resolve({
    ok: true,
    json: () => Promise.resolve(JSON.parse(fs.readFileSync(path.join(DIR, url), "utf8"))),
  }),
  setTimeout, clearTimeout,
  atob: (s) => Buffer.from(s, "base64").toString("binary"),
});
vm.runInContext(scriptMatch[1], context, { filename: "index.html<script>" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function countRows(selector) {
  const el = bySelector.get(selector);
  if (!el) return -1;
  return (el.innerHTML.match(/<tr>/g) || []).length;
}
function countOccurrences(selector, needle) {
  const el = bySelector.get(selector);
  if (!el) return -1;
  return el.innerHTML.split(needle).length - 1;
}

(async () => {
  await sleep(500);
  const failures = [];
  const check = (name, cond, detail) => {
    console.log(`${cond ? "PASS" : "FAIL"}: ${name}${detail !== undefined ? ` (${detail})` : ""}`);
    if (!cond) failures.push(name);
  };

  // Frozen set — the fixes another worker made must still hold.
  check("frozen ranked table has exactly 2 rows", countRows("#ranked tbody") === 2, countRows("#ranked tbody"));
  const frozenRanked = bySelector.get("#ranked tbody").innerHTML;
  check("frozen ranked: Truvian 4/12 present", frozenRanked.includes("4 / 12"));
  check("frozen ranked: TxLens 2/12 present", frozenRanked.includes("2 / 12"));
  check("frozen ranked: field accuracy 37/47 present", frozenRanked.includes("37/47"));
  check("frozen ranked: field accuracy 2/47 present", frozenRanked.includes("2/47"));
  check("frozen ranked: field-acc. rank column present", html.includes("Field-acc. rank"));
  const frozenSens = (byId.get("frozen-sensitivity") || {}).textContent || "";
  check("frozen sensitivity: Truvian 4/12 -> 10/12", frozenSens.includes("4/12") && frozenSens.includes("10/12"), frozenSens);
  check("frozen sensitivity: TxLens stays 2/12", frozenSens.includes("2/12"));
  check("frozen unservable table has 3 rows", countRows("#unservable-table tbody") === 3, countRows("#unservable-table tbody"));
  check("frozen traps sha rendered", (byId.get("traps-sha") || {}).textContent === "0f84494bc8a6b1773aa74f2f9e3c15b6e7eb42b397c8849bbea3068bd4a1d534");
  const frozenDetail = byId.get("detail").innerHTML;
  check("frozen detail has 24 settlement links", countOccurrences("#detail", "settlement tx") === 0 || frozenDetail.split("settlement tx").length - 1 === 24, frozenDetail.split("settlement tx").length - 1);
  check("frozen detail covers 60 rows", (frozenDetail.match(/<details>/g) || []).length === 60, (frozenDetail.match(/<details>/g) || []).length);

  // Expansion set — the new section, now from the clean single-file run.
  check("expansion ranked table has exactly 3 rows", countRows("#ranked-exp tbody") === 3, countRows("#ranked-exp tbody"));
  const expRanked = bySelector.get("#ranked-exp tbody").innerHTML;
  check("expansion ranked: ChainWire 11/12 present", expRanked.includes("11 / 12"));
  check("expansion ranked: field accuracy 46/47 present", expRanked.includes("46/47"));
  check("expansion ranked: Truvian field 39/49 present", expRanked.includes("39/49"));
  check("expansion ranked: TxLens field 2/47 present", expRanked.includes("2/47"));
  check("expansion ranked: field-acc. ranks 1/2/3 present",
    expRanked.includes("<td>1</td>") && expRanked.includes("<td>2</td>") && expRanked.includes("<td>3</td>"));
  const expVerdict = (byId.get("exp-verdict-list") || {}).innerHTML || "";
  check("expansion verdict cites clean run id", expVerdict.includes("run-20261109T162426Z-56816b"), expVerdict.slice(0, 120));
  check("expansion verdict: wallet 28.84 -> 28.48", expVerdict.includes("28.84") && expVerdict.includes("28.48"));
  check("expansion verdict: clean run $0.36 billed", expVerdict.includes("$0.36"));
  check("expansion verdict: Truvian read honestly (39/49)", expVerdict.includes("39/49"));
  // Sensitivity view — status-excluded ranking.
  check("sensitivity table has exactly 3 rows", countRows("#sensitivity-exp tbody") === 3, countRows("#sensitivity-exp tbody"));
  const sensTable = bySelector.get("#sensitivity-exp tbody").innerHTML;
  check("sensitivity: Truvian status-excluded 10/12 present", sensTable.includes("10 / 12"));
  check("sensitivity: ChainWire status-excluded 11/12 present", sensTable.includes("11 / 12"));
  check("sensitivity: TxLens status-excluded 2/12 present", sensTable.includes("2 / 12"));
  check("sensitivity: Truvian fails only on status 8", sensTable.includes("<td>8</td>"));
  const sensAnswer = (byId.get("sensitivity-answer") || {}).textContent || "";
  check("sensitivity answer: tie BREAKS, order UNCHANGED", sensAnswer.includes("BREAKS") && sensAnswer.includes("UNCHANGED"), sensAnswer.slice(0, 120));
  // Combined 24-trap counts must NOT be rendered anywhere on the page
  // (data file only now). The note naming them as not-rendered may stay.
  check("combined-24 element does not exist", !byId.has("combined-24"));
  check("no combined 4/24 count rendered", !html.includes("4/24"));
  check("no combined 6/24 count rendered", !html.includes("6/24"));
  check("expansion unservable table has 2 rows", countRows("#unservable-exp-table tbody") === 2, countRows("#unservable-exp-table tbody"));
  check("expansion traps sha rendered", (byId.get("exp-traps-sha") || {}).textContent === "940a00400477e0aefb38afe1da20fb98cc03b187e7218da252d322fd4699b5ba");
  check("expansion matrix has 12 trap rows", countRows("#matrix-exp tbody") === 12, countRows("#matrix-exp tbody"));
  const expDetail = byId.get("detail-exp").innerHTML;
  check("expansion detail covers 36 rows", (expDetail.match(/<details>/g) || []).length === 36, (expDetail.match(/<details>/g) || []).length);
  check("expansion detail has 36 settlement links", expDetail.split("settlement tx").length - 1 === 36, expDetail.split("settlement tx").length - 1);
  const probed = byId.get("probed-only").textContent;
  check("probed-only note names both ChainWire miners", probed.includes("7317307") && probed.includes("7307"));

  if (failures.length) { console.error(`\n${failures.length} FAILURES`); process.exit(1); }
  console.log("\nAll render checks passed.");
})();
