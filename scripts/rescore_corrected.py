"""Disclosed corrected re-score — RE-ANALYSIS ONLY, no new purchases.

Reads the FROZEN live results (results-live/full-run-2026-11-06.json)
and the FROZEN trap set (traps-frozen-2026-11-06.json) READ-ONLY and
writes a NEW file, results-live/results-corrected-2026-11-08.json.
It NEVER overwrites the original results, and it NEVER re-freezes
or edits the trap file.

What changed vs the strict original (Council findings, 8 Nov 2026):
- F-normalise: the old normalise() only converted value_eth to wei
  when the string contained ".". Truvian t08 answered value_eth
  1e-05 — exactly the expected 10000000000000 wei — which stringified
  to "1e-05" (no dot), passed through, and string-compared unequal.
  The shared normaliser (traptest/normalise.py) now parses Decimal
  values including scientific notation, hex and "100.0", and the
  scorer compares value as Decimal / block as int. Re-scoring the
  SAME frozen raw answers gives Truvian 4/12 (t07, t08, t11, t12),
  not 3/12. Nothing else changes: ranking order is unchanged.
- F-token: t03/t04 score expected_value from the Transfer EVENT
  amount (950000 / 2000000000000000000) while expected from/to come
  from the tx itself; no provider returns a token amount in the
  intent's value_eth field (native tx value, 0 for both). Those traps
  are unwinnable as specified on value. The frozen traps are NOT
  edited. Instead this file keeps BOTH views: the corrected table
  (value still scored, as frozen) AND a value-excluded view scoring
  t03/t04 on status/from/to/block only, with the reason stated.
  No provider passes t03/t04 even value-excluded (status fails for
  both served providers), so the value-excluded view changes no pass
  count — it is shown for methodology transparency, not as a new
  headline.

The output contains:
- "strict_original": the original strict table AND the original
  scores rows preserved verbatim (deep copy), plus strict field
  accuracy — the live record, unchanged.
- "corrected": re-scored rows (same raw answers, fixed normalise +
  canonical scorer), corrected table, corrected ranking, and
  corrected field accuracy.
- "value_excluded_view": t03/t04 scored without value, served rows
  only (unservable rows are never counted as passes — an empty field
  list is not a pass).
- "traps_sha256": sha256 of traps-frozen-2026-11-06.json, proving
  which frozen set was re-scored.

This re-score does NOT change the live results. It is a disclosed
re-analysis of the same frozen raw answers.

Run: python3 scripts/rescore_corrected.py
"""
import copy
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from traptest.leaderboard import Leaderboard  # noqa: E402
from traptest.normalise import normalise  # noqa: E402
from traptest.scoring import score_answer  # noqa: E402
from traptest.traps import Trap  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FROZEN_RESULTS = ROOT / "results-live" / "full-run-2026-11-06.json"
FROZEN_TRAPS = ROOT / "traps-frozen-2026-11-06.json"
OUT = ROOT / "results-live" / "results-corrected-2026-11-08.json"

TOKEN_TRAP_IDS = ("t03-token-transfer", "t04-token-transfer")
METHODOLOGY = (
    "Disclosed corrected re-score of the frozen 6 Nov 2026 run "
    "(12 traps x 5 providers, 60 rows). Same raw answers, re-scored "
    "with the fixed shared normaliser (traptest/normalise.py: Decimal "
    "ETH -> wei including scientific notation '1e-05', hex, '100.0') "
    "and the canonical scorer (traptest/scoring.py: value as Decimal, "
    "block as int). Strict original preserved verbatim under "
    "'strict_original'. F-normalise: Truvian t08 was scored FAIL "
    "though its value_eth 1e-05 equals the expected 10000000000000 "
    "wei; corrected Truvian is 4/12. F-token: t03/t04 score the "
    "Transfer EVENT amount as value, which no provider returns in "
    "value_eth (native tx value); the frozen traps are untouched and "
    "a value-excluded view (status/from/to/block only) is shown "
    "alongside — no provider passes t03/t04 even value-excluded, so "
    "it changes no pass count. This file is a re-analysis; it does "
    "NOT change the live results."
)


def _table(rows, passed_key="passed"):
    table = {}
    for row in rows:
        pid = row["provider_id"]
        entry = table.setdefault(pid, {"passed": 0, "served": 0, "rows": 0,
                                       "total_cost_usd": 0.0})
        entry["rows"] += 1
        if row.get("answer") is not None:
            entry["served"] += 1
        if row.get(passed_key):
            entry["passed"] += 1
        if row.get("cost_usd") is not None:
            entry["total_cost_usd"] = round(
                entry["total_cost_usd"] + float(row["cost_usd"]), 4)
    for entry in table.values():
        served = entry["served"]
        entry["pass_rate_served"] = (round(entry["passed"] / served, 4)
                                     if served else None)
    return table


def _field_accuracy(rows, fields_key="fields"):
    acc = {}
    for row in rows:
        pid = row["provider_id"]
        entry = acc.setdefault(pid, {"correct": 0, "scored": 0})
        for f in row.get(fields_key) or []:
            entry["scored"] += 1
            if f.get("passed"):
                entry["correct"] += 1
    for entry in acc.values():
        entry["accuracy"] = (round(entry["correct"] / entry["scored"], 4)
                             if entry["scored"] else None)
    return acc


def _ranking(rows, passed_key="passed"):
    """Ranking order (served providers only) + unservable tier."""
    lb = Leaderboard()
    by_provider = {}
    for row in rows:
        by_provider.setdefault(row["provider_id"], []).append(row)
    for pid, prows in by_provider.items():
        if all(r.get("answer") is None for r in prows):
            lb.mark_unservable(pid)
    # Feed served scores through score objects rebuilt from rows.
    for row in rows:
        if row.get("answer") is None:
            continue
        # Rebuild a minimal Score-equivalent via the corrected fields.
        from traptest.scoring import Score, FieldResult
        fields = tuple(FieldResult(f["field"], str(f["expected"]),
                                   None if f.get("actual") is None else str(f["actual"]),
                                   bool(f["passed"]))
                       for f in row.get("fields") or [])
        lb.add(Score(row["trap_id"], row["provider_id"],
                     bool(row.get(passed_key)), fields,
                     cost_usd=row.get("cost_usd"),
                     receipt_present=bool(row.get("receipt_present"))))
    return ([s.provider_id for s in lb.ranked()],
            lb.unservable_providers())


def main(argv=None):
    """Re-score the frozen live rows with the fixed normaliser/scorer.

    The expected values (row count, Truvian/TxLens corrected pass
    counts, unservable provider list) are CLI arguments defaulting to
    the verified 6 Nov 2026 figures — they are verification asserts,
    not inputs to the re-score. Pass different values only when
    re-verifying against a different frozen file.
    """
    import argparse
    parser = argparse.ArgumentParser(
        description="Disclosed corrected re-score (read-only re-analysis; "
                    "never overwrites the frozen live results)")
    parser.add_argument("--expected-rows", type=int, default=60,
                        help="frozen rows expected (default: 60)")
    parser.add_argument("--expected-truvian", type=int, default=4,
                        help="Truvian (8453) corrected passes (default: 4)")
    parser.add_argument("--expected-txlens", type=int, default=2,
                        help="TxLens (9002) corrected passes (default: 2)")
    parser.add_argument("--expected-unservable", default="4433,900,9010",
                        help="comma-separated unservable provider ids "
                             "(default: 4433,900,9010)")
    parser.add_argument("--out", default=str(OUT),
                        help="output path (default: the frozen corrected "
                             "results file; never the original results file)")
    args = parser.parse_args(argv)
    out = Path(args.out)
    assert out.resolve() != FROZEN_RESULTS.resolve(), "refusing to overwrite the original"
    expected_unservable = [p.strip() for p in args.expected_unservable.split(",") if p.strip()]
    traps_sha256 = hashlib.sha256(FROZEN_TRAPS.read_bytes()).hexdigest()
    frozen = json.loads(FROZEN_TRAPS.read_text())
    original = json.loads(FROZEN_RESULTS.read_text())
    rows = original["scores"]
    assert len(rows) == args.expected_rows, f"expected {args.expected_rows} frozen rows, got {len(rows)}"
    traps = {}
    for t in frozen["traps"]:
        traps[t["trap_id"]] = Trap(
            trap_id=t["trap_id"], intent=t["intent"], tx_hash=t["tx_hash"],
            expected_status=t["expected_status"], expected_from=t["expected_from"],
            expected_to=t["expected_to"], expected_value=t["expected_value"],
            expected_block=t["expected_block"])

    strict_table = _table(rows)
    strict_ranking, strict_unservable = _ranking(rows)
    strict_accuracy = _field_accuracy(rows)

    corrected_rows = []
    value_excluded_rows = []
    for row in rows:
        trap = traps[row["trap_id"]]
        if row.get("answer") is None:
            # Unservable: no answer was served. Never scored, never a pass.
            corrected_rows.append({**copy.deepcopy(row),
                                   "served": False,
                                   "strict_passed": bool(row.get("passed")),
                                   "corrected_passed": False,
                                   "correction_note": "unservable — no answer served; not scored"})
            continue
        norm, notes = normalise(row["answer"])
        score = score_answer(trap, row["provider_id"], norm,
                             cost_usd=row.get("cost_usd"),
                             signal_hash=row.get("signal_hash"),
                             receipt_present=bool(row.get("receipt_present")))
        fields = [{"field": f.field, "expected": f.expected,
                   "actual": f.actual, "passed": f.passed}
                  for f in score.fields]
        note = None
        if bool(row.get("passed")) != score.passed:
            changed = [f["field"] for f in fields
                       if f["passed"] and not any(
                           of.get("field") == f["field"] and of.get("passed")
                           for of in row.get("fields") or [])]
            note = (f"pass changed under fixed normaliser/scorer "
                    f"(newly passing fields: {changed}); raw answer unchanged")
        corrected_rows.append({**copy.deepcopy(row),
                               "served": True,
                               "strict_passed": bool(row.get("passed")),
                               "passed": score.passed,
                               "corrected_passed": score.passed,
                               "normalised_answer": norm,
                               "normalisation_notes": notes,
                               "fields": fields,
                               "correction_note": note})
        if row["trap_id"] in TOKEN_TRAP_IDS:
            excl_trap = replace(trap, expected_value=None)
            excl = score_answer(excl_trap, row["provider_id"], norm,
                                cost_usd=row.get("cost_usd"),
                                signal_hash=row.get("signal_hash"),
                                receipt_present=bool(row.get("receipt_present")))
            value_excluded_rows.append({
                "trap_id": row["trap_id"],
                "provider_id": row["provider_id"],
                "served": True,
                "value_excluded": True,
                "passed_value_excluded": excl.passed,
                "passed_corrected_with_value": score.passed,
                "fields": [{"field": f.field, "expected": f.expected,
                            "actual": f.actual, "passed": f.passed}
                           for f in excl.fields],
                "note": ("value excluded: expected_value is the Transfer "
                         "EVENT amount, which no provider returns in "
                         "value_eth (native tx value)")})

    corrected_table = _table(corrected_rows, passed_key="corrected_passed")
    corrected_ranking, corrected_unservable = _ranking(
        corrected_rows, passed_key="corrected_passed")
    corrected_accuracy = _field_accuracy(corrected_rows)

    # Value-excluded table: served t03/t04 rows only.
    excl_table = {}
    for r in value_excluded_rows:
        entry = excl_table.setdefault(r["provider_id"],
                                      {"served": 0, "passed_value_excluded": 0})
        entry["served"] += 1
        if r["passed_value_excluded"]:
            entry["passed_value_excluded"] += 1
    for pid in {r["provider_id"] for r in rows}:
        if pid not in excl_table:
            excl_table[pid] = {"served": 0, "passed_value_excluded": 0,
                               "note": "no served t03/t04 rows (unservable)"}

    doc = {
        "data_kind": "CORRECTED_REANALYSIS",
        "generated": "2026-11-08",
        "source_results_file": "results-live/full-run-2026-11-06.json",
        "source_traps_file": "traps-frozen-2026-11-06.json",
        "traps_sha256": traps_sha256,
        "methodology": METHODOLOGY,
        "disclaimer": ("This file is a disclosed re-analysis of the same "
                       "frozen raw answers. It does NOT change the live "
                       "results in full-run-2026-11-06.json, which remain "
                       "the strict original."),
        "strict_original": {
            "table": strict_table,
            "ranking_served": strict_ranking,
            "unservable": strict_unservable,
            "field_accuracy": strict_accuracy,
            "scores": copy.deepcopy(rows),
        },
        "corrected": {
            "table": corrected_table,
            "ranking_served": corrected_ranking,
            "unservable": corrected_unservable,
            "field_accuracy": corrected_accuracy,
            "scores": corrected_rows,
        },
        "field_accuracy_corrected": corrected_accuracy,
        "value_excluded_view": {
            "methodology": ("t03/t04 scored on status/from/to/block only, "
                            "value excluded. Reason: expected_value is the "
                            "Transfer EVENT amount (950000 / "
                            "2000000000000000000); no provider returns a "
                            "token amount in the intent's value_eth field "
                            "(native tx value, 0 for both txs), so the "
                            "traps are unwinnable as specified on value. "
                            "Frozen traps NOT edited; this view is shown "
                            "alongside the corrected table, not instead "
                            "of it. Served rows only — unservable "
                            "providers have no rows here and are never "
                            "counted as passing."),
            "table": excl_table,
            "rows": value_excluded_rows,
        },
    }
    out.write_text(json.dumps(doc, indent=2))

    # Verification (asserts fail the run rather than writing a bad file).
    assert corrected_table["8453"]["passed"] == args.expected_truvian, corrected_table["8453"]
    assert corrected_table["9002"]["passed"] == args.expected_txlens, corrected_table["9002"]
    assert strict_table["8453"]["passed"] == 3, strict_table["8453"]
    assert strict_table["9002"]["passed"] == 2
    assert corrected_ranking == strict_ranking, (corrected_ranking, strict_ranking)
    assert len(corrected_rows) == args.expected_rows and len(doc["strict_original"]["scores"]) == args.expected_rows
    assert corrected_unservable == expected_unservable, corrected_unservable
    print(f"wrote {out}")
    print(f"strict:    Truvian {strict_table['8453']['passed']}/12, "
          f"TxLens {strict_table['9002']['passed']}/12, "
          f"ranking {strict_ranking}, unservable {strict_unservable}")
    print(f"corrected: Truvian {corrected_table['8453']['passed']}/12, "
          f"TxLens {corrected_table['9002']['passed']}/12, "
          f"ranking {corrected_ranking}, unservable {corrected_unservable}")
    print("field accuracy (corrected): "
          + str({k: str(v['correct']) + "/" + str(v['scored'])
                 for k, v in corrected_accuracy.items()}))
    print("value-excluded t03/t04: "
          + str({k: v['passed_value_excluded'] for k, v in excl_table.items()})
          + " (no pass-count change)")
    print(f"traps sha256: {traps_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
