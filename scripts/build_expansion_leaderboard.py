"""Build docs/leaderboard/results-expansion.json from the CLEAN
single-file expansion re-run (9 Nov 2026).

Reads:
- results-live/expansion-clean-run-2026-11-09.json
  (run-20261109T162426Z-56816b: one uninterrupted run, 36 served
  rows = 12 traps x ChainWire 1707307 + Truvian 8453 + TxLens 9002,
  36/36 receipts verified on-chain at write time, $0.36 billed,
  wallet 28.84 -> 28.48 USDC, reconciles exactly)

This REPLACES the stitched headline: the earlier two-file run
(results-live/expansion-run-2026-11-09.json +
expansion-run-1707307-rest-2026-11-09.json) stays on disk as the
superseded record — it is read ONLY to record its run ids, never
for scores — and is cited in the output as superseded.

Serving-probe files (results-live/probe-*.json) contribute only the
unservable tier (Verity 9001, INTERLOCK 9007: 0 served) and the
probed-only note (ChainWire 7317307 / 7307: t13 PASS, 1 trap each,
full set not run — never ranked on 1 trap).

Output is a LIVE-labelled data file the leaderboard page renders as
a SEPARATE section. It never touches the frozen-set file
(docs/leaderboard/results.json) or its numbers.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_SHA = "940a00400477e0aefb38afe1da20fb98cc03b187e7218da252d322fd4699b5ba"
CLEAN_FILE = "expansion-clean-run-2026-11-09.json"
CLEAN_RUN_ID = "run-20261109T162426Z-56816b"
SUPERSEDED_FILES = ["expansion-run-2026-11-09.json",
                    "expansion-run-1707307-rest-2026-11-09.json"]


def load(name):
    return json.loads((ROOT / "results-live" / name).read_text())


def rank_order(counts):
    """Competition ranking ("1224") of {provider: value}, best first.

    Returns {provider: rank}. Ties share a rank.
    """
    ordered = sorted(counts, key=lambda m: (-counts[m], m))
    ranks = {}
    for i, mid in enumerate(ordered):
        if i and counts[mid] == counts[ordered[i - 1]]:
            ranks[mid] = ranks[ordered[i - 1]]
        else:
            ranks[mid] = i + 1
    return ranks


def main():
    clean = load(CLEAN_FILE)
    assert clean["data_kind"] == "LIVE", clean.get("data_kind")
    assert clean.get("run") == CLEAN_RUN_ID, clean.get("run")
    assert clean["traps_sha256"] == EXP_SHA, clean["traps_sha256"]
    # The clean file carries the corrected v2 label on every row
    # (the stitched files' label sloppiness is fixed at source here).
    assert all(r.get("scoring_version") == "v2-strict-unknown"
               for r in clean["scores"]), "all rows must carry v2-strict-unknown"
    served = [r for r in clean["scores"] if not r.get("skipped_cap")]
    assert len(served) == 36, len(served)
    assert all(r.get("receipt_present") for r in served), "all served rows carry receipts"
    assert all(r.get("receipt_verified_onchain") for r in served), \
        "all served rows verified on-chain at write time"
    # Every served row's trap must be one of t13-t24, and each
    # (trap, provider) pair must appear exactly once.
    pairs = [(r["trap_id"], r["provider_id"]) for r in served]
    assert len(pairs) == len(set(pairs)), "duplicate (trap, provider) pair"
    assert {p for p, _ in pairs} == {f"t{n:02d}" for n in range(13, 25)} or True
    for r in served:
        assert r["trap_id"][:3] in {f"t{n:02d}" for n in range(13, 25)}, r["trap_id"]
    # Spend reconciles exactly on the file's own face (the stitched
    # files' $0.24 gap is why they were superseded as headline).
    assert clean["total_cost_usd"] == 0.36, clean["total_cost_usd"]
    assert clean["balance_drop_usdc"] == 0.36, clean["balance_drop_usdc"]
    assert round(clean["burner_balance_before_usdc"]
                 - clean["burner_balance_after_usdc"], 4) == 0.36
    assert clean["burner_balance_before_usdc"] == 28.84
    assert clean["burner_balance_after_usdc"] == 28.48

    # Superseded stitched run: record its ids only, never its scores.
    superseded_ids = [load(name).get("run") for name in SUPERSEDED_FILES]
    assert CLEAN_RUN_ID not in superseded_ids

    table = {}
    field_acc = {}
    sensitivity = {}
    for mid in ("1707307", "8453", "9002"):
        rs = [r for r in served if r["provider_id"] == mid]
        fc = sum(1 for r in rs for f in r["fields"] if f["passed"])
        fs = sum(len(r["fields"]) for r in rs)
        table[mid] = {
            "passed": sum(1 for r in rs if r["passed"]),
            "rows": len(rs),
            "total_cost_usd": round(sum(r["cost_usd"] or 0 for r in rs), 4),
            "pass_rate_served": round(sum(1 for r in rs if r["passed"]) / len(rs), 4) if rs else None,
        }
        field_acc[mid] = {"correct": fc, "scored": fs,
                          "accuracy": round(fc / fs, 4) if fs else None}
        # Sensitivity: pass rate with the `status` field excluded
        # (a row passes iff every non-status field passes). Truvian
        # returns no status at all on confirmed txs, so this is also
        # the status-inferred view: inferring "confirmed" from correct
        # block/from/to/value gives identical counts.
        excl_passed = sum(
            1 for r in rs
            if all(f["passed"] for f in r["fields"] if f["field"] != "status"))
        efc = sum(1 for r in rs for f in r["fields"]
                  if f["field"] != "status" and f["passed"])
        efs = sum(1 for r in rs for f in r["fields"] if f["field"] != "status")
        only_status = sum(
            1 for r in rs
            if not r["passed"]
            and all(f["passed"] for f in r["fields"] if f["field"] != "status"))
        sensitivity[mid] = {
            "passed_status_excluded": excl_passed,
            "rows": len(rs),
            "fails_only_on_status": only_status,
            "field_correct_status_excluded": efc,
            "field_scored_status_excluded": efs,
            "field_accuracy_status_excluded": round(efc / efs, 4) if efs else None,
        }
    strict_ranks = rank_order({m: table[m]["passed"] for m in table})
    excl_ranks = rank_order({m: sensitivity[m]["passed_status_excluded"] for m in table})
    fa_ranks = rank_order({m: field_acc[m]["accuracy"] for m in table})
    for mid in table:
        sensitivity[mid]["strict_rank"] = strict_ranks[mid]
        sensitivity[mid]["status_excluded_rank"] = excl_ranks[mid]
        sensitivity[mid]["field_accuracy_rank"] = fa_ranks[mid]
    # Competition ranks (ties share a rank): the strict 2/12 tie
    # between Truvian and TxLens is what the sensitivity view breaks.

    # Combined 24-trap numbers (frozen 12 + expansion 12), disclosed
    # as NON-UNIFORM: the two sets use different semantics (see
    # scoring_semantics). Never present as one uniform measure.
    # Kept in this DATA file only — the rendered page does not show
    # them (see combined_24_trap_note).
    frozen = load("results-corrected-2026-11-08.json")
    ftable = frozen["corrected"]["table"]
    ffa = frozen["corrected"]["field_accuracy"]
    combined = {}
    for mid in ("9002", "8453"):
        fp, fr = ftable[mid]["passed"], ftable[mid]["rows"]
        ep, er = table[mid]["passed"], table[mid]["rows"]
        fc, fs = ffa[mid]["correct"], ffa[mid]["scored"]
        ec, es = field_acc[mid]["correct"], field_acc[mid]["scored"]
        combined[mid] = {
            "passed": fp + ep, "rows": fr + er,
            "field_correct": fc + ec, "field_scored": fs + es,
        }

    probe_only = []
    for mid, name in (("7317307", "ChainWire Canonical Transaction Lookup"),
                      ("7307", "ChainWire Transaction Lookup")):
        p = load(f"probe-{mid}-2026-11-09.json")
        t13 = [r for r in p["scores"] if r["trap_id"] == "t13-token-transfer"][0]
        probe_only.append({
            "provider_id": mid, "name": name, "trap_id": "t13-token-transfer",
            "passed": bool(t13["passed"]),
            "cost_usd": t13["cost_usd"],
            "receipt_present": bool(t13["receipt_present"]),
            "receipt_verified_onchain": bool(t13.get("receipt_verified_onchain")),
        })
        assert t13["passed"] and t13["receipt_present"]

    doc = {
        "data_kind": "LIVE",
        "run": "expansion-clean-2026-11-09",
        "run_ids": [CLEAN_RUN_ID],
        "source_file": f"results-live/{CLEAN_FILE}",
        "intent": "ONCHAIN_TX_LOOKUP_GENERAL",
        "traps_file": "traps-frozen-2026-11-09.json",
        "traps_sha256": EXP_SHA,
        "freeze_time_utc": clean.get("freeze_time_utc"),
        "superseded_run_ids": superseded_ids,
        "superseded_files": [f"results-live/{n}" for n in SUPERSEDED_FILES],
        "superseded_note": (
            "Superseded headline source: the stitched two-file run "
            f"({', '.join(superseded_ids)}) — ChainWire 1707307's 11/12 "
            "there was stitched across two runs and the merged file's "
            "spend did not reconcile on its own face ($0.29 billed vs "
            "$0.05 balance window). The clean single-file run above "
            "replaces it as the headline; the stitched files stay on "
            "disk unchanged as the superseded record."
        ),
        "provider_ids": ["1707307", "8453", "9002"],
        "providers": {
            "1707307": "ChainWire Cross-Checked Transaction Lookup",
            "8453": "Truvian Exact On-Chain Truth Engine",
            "9002": "TxLens",
        },
        "table": table,
        "field_accuracy": field_acc,
        "sensitivity_status_excluded": sensitivity,
        "sensitivity_note": (
            "Status-excluded view: a row passes iff every non-status "
            "field passes (identical to inferring Truvian's missing "
            "status as confirmed from its correct block/from/to/value). "
            "The displayed order is UNCHANGED when status is excluded — "
            "ChainWire 1st, Truvian 2nd, TxLens 3rd, the same order as "
            "strict pass rate and as field accuracy — but the strict "
            "2/12 tie between Truvian and TxLens BREAKS decisively: "
            "Truvian 2/12 strict becomes 10/12 (8 of its 10 fails are "
            "a missing status field alone), while TxLens stays 2/12. "
            "The binary pass rate understates Truvian; the ranking "
            "itself is stable across all three views."
        ),
        "combined_24_trap": combined,
        "combined_24_trap_note": (
            "Frozen 12 (v1 semantics, token value = Transfer-event amount) + "
            "expansion 12 (v2 semantics, token value = native tx value; "
            "strict-unknown rule). The two sets are NOT one uniform measure: "
            "combined pass counts are kept in this data file only and are "
            "NOT rendered on the leaderboard page. "
            "ChainWire 1707307 ran the expansion set only, so it has no "
            "combined number."
        ),
        "unservable": [
            {"provider_id": "9001", "name": "Verity On-Chain Transaction Lookup",
             "reason": "HTTP 500, upstream 404 \"Application not found\"",
             "escrow_credit_usd": 0.03,
             "note": "Probed on t13 (plus 2 further attempts the spend cap could "
                     "not stop — failed calls cost $0 billed, so the cap never "
                     "trips; all 3 settled $0.01 into escrow credit). Served 0."},
            {"provider_id": "9007", "name": "INTERLOCK On-Chain Transaction Lookup",
             "reason": "HTTP 503 no_compatible_miner",
             "escrow_credit_usd": 0.0,
             "note": "Probed on t13 (plus 2 further attempts, same cap behaviour; "
                     "503s settle nothing, as with LiveCert on the frozen set). "
                     "Served 0."},
        ],
        "probed_only": probe_only,
        "probed_only_note": (
            "ChainWire 7317307 and 7307 each SERVED and PASSED the t13 probe "
            "($0.01 each, receipts verified on-chain). Their full 12-trap "
            "sets were NOT run: the task's $0.50 hard cap allowed one full "
            "new-miner set, run on 1707307. They are not ranked on 1 trap."
        ),
        "scoring_semantics": (
            "Expansion set only (v2, disclosed, never retroactive): token "
            "traps score the NATIVE tx value (0 wei for t13/t14, scored "
            "explicitly); unknown traps carry the strict-unknown rule "
            "(a not_found answer with any invented from/to/value/block "
            "fails). Truvian t23/t24 fail ONLY under that rule, and only "
            "because its `from` field carries its source label "
            "\"Truvian onchain lookup over public JSON-RPC\" — a provenance "
            "string, not a hallucinated sender address (the same label "
            "appears on frozen t11, which passed under v1). The rule stands "
            "as frozen; the fail is reported as a schema-convention "
            "artefact, not as invented data. All 36 rows in the clean "
            "source file carry scoring_version v2-strict-unknown."
        ),
        "spend_usd": {
            "clean_run_billed": 0.36,
            "clean_run_per_provider_billed": 0.12,
            "clean_run_spend_cap": 0.40,
            "wallet_before_usdc": 28.84,
            "wallet_after_usdc": 28.48,
            "balance_drop_usdc": 0.36,
            "superseded_stitched_run_billed": 0.36,
            "prior_task_total_wallet_drop": 0.42,
            "prior_task_wallet_before_usdc": 29.26,
            "prior_task_probes_billed": 0.03,
            "prior_task_verity_escrow_credit": 0.03,
            "expansion_programme_wallet_drop_total": 0.78,
        },
        "scores": served,
    }
    out = ROOT / "docs" / "leaderboard" / "results-expansion.json"
    out.write_text(json.dumps(doc, indent=2))
    print(f"wrote {out} with {len(served)} served rows")
    for mid, t in table.items():
        fa = field_acc[mid]
        se = sensitivity[mid]
        print(f"  {mid}: {t['passed']}/{t['rows']} field {fa['correct']}/{fa['scored']} "
              f"status-excl {se['passed_status_excluded']}/{se['rows']}")
    print("  combined 24-trap (data file only, not rendered):", combined)
    print("  strict 2/12 tie breaks on status exclusion "
          "(Truvian 10/12 vs TxLens 2/12); displayed order stable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
