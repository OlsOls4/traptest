"""Consistency tests for the 9 Nov 2026 expansion set (t13-t24).

These tests read the SHIPPED data files (no network, no spend) and
check the invariants the expansion task required: the frozen 12 are
untouched, the new set is 2-per-category with v2 semantics, the
leaderboard data file matches its source results files exactly, and
no cap-skipped row is ever presented as scored evidence.
"""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from traptest.harness import load_traps, sha256_file

ROOT = Path(__file__).resolve().parent.parent
FROZEN12_SHA = "0f84494bc8a6b1773aa74f2f9e3c15b6e7eb42b397c8849bbea3068bd4a1d534"
EXP_SHA = "940a00400477e0aefb38afe1da20fb98cc03b187e7218da252d322fd4699b5ba"


def read_json(path):
    return json.loads((ROOT / path).read_text())


class TestExpansionFreeze(unittest.TestCase):
    def test_frozen12_sha_unchanged(self):
        self.assertEqual(sha256_file(ROOT / "traps-frozen-2026-11-06.json"),
                         FROZEN12_SHA)

    def test_expansion_set_loads_and_is_2_per_category(self):
        doc, traps, sha = load_traps(ROOT / "traps-frozen-2026-11-09.json")
        self.assertEqual(sha, EXP_SHA)
        self.assertEqual(len(traps), 12)
        cats = [t["category"] for t in doc["traps"]]
        for cat in ("token_transfer", "contract_interaction", "reverted_tx",
                    "multi_recipient_tx", "plain_transfer", "unknown_tx"):
            self.assertEqual(cats.count(cat), 2, cat)

    def test_v2_flags_only_on_unknown_traps(self):
        doc, traps, _ = load_traps(ROOT / "traps-frozen-2026-11-09.json")
        strict = [t.trap_id for t in traps if t.strict_unknown]
        self.assertEqual(strict, ["t23-unknown-tx", "t24-unknown-tx"])
        doc12, traps12, _ = load_traps(ROOT / "traps-frozen-2026-11-06.json")
        self.assertEqual([t for t in traps12 if t.strict_unknown], [])

    def test_token_traps_score_native_value_zero(self):
        doc = read_json("traps-frozen-2026-11-09.json")
        toks = [t for t in doc["traps"] if t["category"] == "token_transfer"]
        self.assertEqual(len(toks), 2)
        for t in toks:
            self.assertEqual(t["expected_value"], "0")
            self.assertIn("native", t["value_basis"].lower())


class TestExpansionLeaderboardData(unittest.TestCase):
    def test_results_expansion_matches_sources(self):
        exp = read_json("docs/leaderboard/results-expansion.json")
        self.assertEqual(exp["data_kind"], "LIVE")
        self.assertEqual(exp["traps_sha256"], EXP_SHA)
        rows = exp["scores"]
        self.assertEqual(len(rows), 36)
        self.assertFalse(any(r.get("skipped_cap") for r in rows))
        pairs = [(r["trap_id"], r["provider_id"]) for r in rows]
        self.assertEqual(len(pairs), len(set(pairs)))
        for mid, table in exp["table"].items():
            rs = [r for r in rows if r["provider_id"] == mid]
            self.assertEqual(len(rs), 12, mid)
            self.assertEqual(table["passed"],
                             sum(1 for r in rs if r["passed"]), mid)
            fa = exp["field_accuracy"][mid]
            self.assertEqual(fa["correct"],
                             sum(1 for r in rs for f in r["fields"] if f["passed"]), mid)
            self.assertEqual(fa["scored"],
                             sum(len(r["fields"]) for r in rs), mid)

    def test_combined_24_trap_is_frozen_plus_expansion(self):
        exp = read_json("docs/leaderboard/results-expansion.json")
        frozen = read_json("results-live/results-corrected-2026-11-08.json")
        for mid in ("9002", "8453"):
            c = exp["combined_24_trap"][mid]
            self.assertEqual(
                c["passed"],
                frozen["corrected"]["table"][mid]["passed"] + exp["table"][mid]["passed"])
            self.assertEqual(c["rows"], 24)
            self.assertEqual(
                c["field_correct"],
                frozen["corrected"]["field_accuracy"][mid]["correct"]
                + exp["field_accuracy"][mid]["correct"])

    def test_unservable_and_probed_only(self):
        exp = read_json("docs/leaderboard/results-expansion.json")
        self.assertEqual([u["provider_id"] for u in exp["unservable"]],
                         ["9001", "9007"])
        self.assertEqual([p["provider_id"] for p in exp["probed_only"]],
                         ["7317307", "7307"])
        for p in exp["probed_only"]:
            self.assertTrue(p["passed"])
            self.assertTrue(p["receipt_verified_onchain"])


class TestCleanRunIsHeadlineSource(unittest.TestCase):
    """The clean single-file re-run (9 Nov 2026) is the headline
    source; the stitched two-file run is superseded, on disk only."""
    CLEAN_FILE = "results-live/expansion-clean-run-2026-11-09.json"
    CLEAN_RUN_ID = "run-20261109T162426Z-56816b"

    def test_results_expansion_cites_clean_run_only(self):
        exp = read_json("docs/leaderboard/results-expansion.json")
        self.assertEqual(exp["run"], "expansion-clean-2026-11-09")
        self.assertEqual(exp["run_ids"], [self.CLEAN_RUN_ID])
        self.assertEqual(exp["source_file"], f"results-live/{self.CLEAN_FILE.split('/')[-1]}")
        self.assertEqual(exp["superseded_run_ids"],
                         ["run-20261109T132120Z-ff6620", "run-20261109T132354Z-e48a75"])
        self.assertNotIn(self.CLEAN_RUN_ID, exp["superseded_run_ids"])

    def test_scores_match_clean_file_row_for_row(self):
        exp = read_json("docs/leaderboard/results-expansion.json")
        clean = read_json(self.CLEAN_FILE)
        self.assertEqual(clean["run"], self.CLEAN_RUN_ID)
        self.assertEqual(len(exp["scores"]), 36)
        self.assertEqual(len(clean["scores"]), 36)
        exp_rows = {(r["trap_id"], r["provider_id"]): r for r in exp["scores"]}
        for r in clean["scores"]:
            got = exp_rows[(r["trap_id"], r["provider_id"])]
            self.assertEqual(got["passed"], r["passed"])
            self.assertEqual(got["cost_usd"], r["cost_usd"])
            self.assertEqual(got["fields"], r["fields"])
            self.assertTrue(got["receipt_verified_onchain"])
            self.assertEqual(got["scoring_version"], "v2-strict-unknown")

    def test_clean_run_spend_reconciles_exactly(self):
        exp = read_json("docs/leaderboard/results-expansion.json")
        clean = read_json(self.CLEAN_FILE)
        spend = exp["spend_usd"]
        self.assertEqual(spend["clean_run_billed"], 0.36)
        self.assertEqual(spend["clean_run_billed"], clean["total_cost_usd"])
        self.assertEqual(spend["balance_drop_usdc"], clean["balance_drop_usdc"])
        self.assertEqual(round(spend["wallet_before_usdc"] - spend["wallet_after_usdc"], 4),
                         0.36)
        self.assertEqual((spend["wallet_before_usdc"], spend["wallet_after_usdc"]),
                         (28.84, 28.48))

    def test_stitched_files_still_on_disk_untouched(self):
        # Superseded record: present, never rewritten by the builder.
        for name in ("results-live/expansion-run-2026-11-09.json",
                     "results-live/expansion-run-1707307-rest-2026-11-09.json"):
            self.assertTrue((ROOT / name).is_file(), name)
            doc = read_json(name)
            self.assertNotEqual(doc.get("run"), self.CLEAN_RUN_ID)

    def test_frozen_leaderboard_numbers_untouched(self):
        frozen_page = read_json("docs/leaderboard/results.json")
        table = frozen_page["corrected"]["table"]
        self.assertEqual(table["8453"]["passed"], 4)
        self.assertEqual(table["9002"]["passed"], 2)
        fa = frozen_page["corrected"]["field_accuracy"]
        self.assertEqual((fa["8453"]["correct"], fa["8453"]["scored"]), (37, 47))
        self.assertEqual((fa["9002"]["correct"], fa["9002"]["scored"]), (2, 47))


class TestSensitivityStatusExcluded(unittest.TestCase):
    """Status-excluded view: recomputed from the clean file, the
    strict 2/12 tie breaks (Truvian 10/12 vs TxLens 2/12) while the
    displayed order stays ChainWire 1st, Truvian 2nd, TxLens 3rd."""

    def test_sensitivity_matches_clean_file(self):
        exp = read_json("docs/leaderboard/results-expansion.json")
        clean = read_json("results-live/expansion-clean-run-2026-11-09.json")
        sens = exp["sensitivity_status_excluded"]
        for mid in ("1707307", "8453", "9002"):
            rs = [r for r in clean["scores"] if r["provider_id"] == mid]
            excl = sum(1 for r in rs
                       if all(f["passed"] for f in r["fields"] if f["field"] != "status"))
            self.assertEqual(sens[mid]["passed_status_excluded"], excl, mid)
            only_status = sum(1 for r in rs
                              if not r["passed"] and all(
                                  f["passed"] for f in r["fields"] if f["field"] != "status"))
            self.assertEqual(sens[mid]["fails_only_on_status"], only_status, mid)
        self.assertEqual(sens["1707307"]["passed_status_excluded"], 11)
        self.assertEqual(sens["8453"]["passed_status_excluded"], 10)
        self.assertEqual(sens["9002"]["passed_status_excluded"], 2)
        self.assertEqual(sens["8453"]["fails_only_on_status"], 8)

    def test_tie_breaks_but_displayed_order_stable(self):
        exp = read_json("docs/leaderboard/results-expansion.json")
        sens = exp["sensitivity_status_excluded"]
        # Strict pass rate ties Truvian and TxLens at 2/12.
        self.assertEqual(sens["8453"]["strict_rank"], sens["9002"]["strict_rank"])
        # Status-excluded breaks the tie decisively; ChainWire stays 1st.
        self.assertEqual(sens["1707307"]["status_excluded_rank"], 1)
        self.assertEqual(sens["8453"]["status_excluded_rank"], 2)
        self.assertEqual(sens["9002"]["status_excluded_rank"], 3)
        # Field accuracy agrees with the same order.
        self.assertEqual((sens["1707307"]["field_accuracy_rank"],
                         sens["8453"]["field_accuracy_rank"],
                         sens["9002"]["field_accuracy_rank"]), (1, 2, 3))


class TestCombined24DataFileOnly(unittest.TestCase):
    """Combined-24 counts live in the JSON data file and are NOT
    rendered on the leaderboard page."""

    def test_combined_still_in_data_file(self):
        exp = read_json("docs/leaderboard/results-expansion.json")
        self.assertEqual(exp["combined_24_trap"]["8453"]["passed"], 6)
        self.assertEqual(exp["combined_24_trap"]["9002"]["passed"], 4)
        self.assertEqual(exp["combined_24_trap"]["8453"]["rows"], 24)

    def test_combined_not_rendered_on_page(self):
        html = (ROOT / "docs" / "leaderboard" / "index.html").read_text()
        self.assertNotIn('id="combined-24"', html)
        self.assertNotIn("4/24", html)
        self.assertNotIn("6/24", html)


if __name__ == "__main__":
    unittest.main()
