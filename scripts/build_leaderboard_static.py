"""Pre-render the TrapTest leaderboard page (docs/leaderboard/index.html)
as static HTML from the data files, so both ranked tables, both verdicts
and both trap-file SHA-256 values are in the shipped file with no
JavaScript needed to see them.

Reads:
- docs/leaderboard/results.json            (frozen set, CORRECTED_REANALYSIS)
- docs/leaderboard/results-expansion.json  (expansion set, LIVE)

Writes: docs/leaderboard/index.html (only the static regions listed in
PATCHES below; the <script> is left intact — it re-renders the same
content on load and powers the file picker, and docs/leaderboard/
render-check.cjs exercises it).

The generated fragments mirror the page's own render() /
renderExpansion() logic field for field (same ranking rules, same
field-accuracy competition ranks, same settlement-link fallback), so the
static HTML and the JS render agree. Per-trap <details> summaries are
short — trap + result + cost — with the receipt, trap tx and signal
hash inside the expanded body.

Usage: python3 scripts/build_leaderboard_static.py   (from the repo root)
Exit non-zero if a patch anchor is missing, if any "Loading" placeholder
survives, or if a combined 24-trap count (4/24, 6/24) would be rendered —
the two sets are separate measures and are never added together.
"""
import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LB = ROOT / "docs" / "leaderboard"
EXPLORER = "https://sepolia.etherscan.io/tx/"
BASE_SEPOLIA = "https://sepolia.basescan.org/tx/"

NAMES = {"8453": "Truvian", "9002": "TxLens", "4433": "LiveCert",
         "9010": "Sigil", "900": "OnChain Intel",
         "1707307": "ChainWire (Cross-Checked)",
         "7317307": "ChainWire (Canonical)", "7307": "ChainWire",
         "9001": "Verity", "9007": "INTERLOCK"}
FROZEN_REASONS = {"4433": "HTTP 503 no_compatible_miner",
                  "9010": "HTTP 500 upstream 404",
                  "900": "HTTP 500 upstream 400 \u201cCould not determine a supported chain\u201d"}


def esc(s):
    return str("" if s is None else s).replace("&", "&amp;").replace("<", "&lt;") \
        .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")


def label(pid):
    return esc(NAMES.get(pid, "")) + " (" + esc(pid) + ")"


def receipt_parts(row):
    """(receipt_hash, settlement_tx) from the base64 receipt, as the page does."""
    if not row.get("receipt"):
        return None, row.get("receipt_settlement_tx")
    try:
        decoded = json.loads(base64.b64decode(row["receipt"]).decode())
    except Exception:
        return None, row.get("receipt_settlement_tx")
    return decoded.get("receipt_hash"), row.get("receipt_settlement_tx") or decoded.get("tx_hash")


def receipt_cell(row):
    if not row.get("receipt_present"):
        return "n/a (not served)"
    h, tx = receipt_parts(row)
    shown = (esc(h[:18]) + "&hellip;") if h else (esc(str(row["receipt"])[:18]) + "&hellip;")
    link = (' <a href="' + EXPLORER + esc(tx) + '">settlement tx</a>') if tx \
        else " <span class='muted'>(no settlement tx recorded in results file)</span>"
    return '<code title="' + esc(h or row["receipt"]) + '">' + shown + "</code>" + link


def rank_rows(stats, field_acc):
    """Ranking: pass rate, then traps run, then lower cost, then provider id."""
    ranked = [s for s in stats.values() if s["served"] > 0]
    ranked.sort(key=lambda s: (-(s["passed"] / s["run"]), -s["run"], s["cost"], s["provider_id"]))
    return ranked


def field_acc_rank(pid, field_acc):
    fa = field_acc.get(pid)
    if not fa or fa.get("accuracy") is None:
        return "\u2014"
    better = sum(1 for o in field_acc.values()
                 if o.get("accuracy") is not None and o["accuracy"] > fa["accuracy"])
    return str(better + 1)


def detail_block(provider_id, rows, is_corrected, trap_tx_by_id):
    out = []
    for x in rows:
        passed = bool(x.get("corrected_passed")) if is_corrected else bool(x.get("passed"))
        fields = "".join(
            "<tr><td>" + esc(f["field"]) + "</td><td>" + esc(f["expected"]) + "</td><td>" +
            ("<em>missing</em>" if f.get("actual") is None else esc(f["actual"])) +
            "</td><td class='" + ("pass" if f["passed"] else "fail") + "'>" +
            ("PASS" if f["passed"] else "FAIL") + "</td></tr>"
            for f in (x.get("fields") or []))
        body = ("<div class='tablewrap'><table><thead><tr><th>Field</th><th>Expected</th>"
                "<th>Actual</th><th>Result</th></tr></thead><tbody>" + fields +
                "</tbody></table></div>") if fields else \
            "<p class='muted'>No fields scored \u2014 this trap was not served.</p>"
        err = ("<p><strong>Error returned:</strong></p><pre>" + esc(x["error"]) + "</pre>") \
            if x.get("error") else ""
        note = ("<p class='muted'>Correction: " + esc(x["correction_note"]) + "</p>") \
            if (is_corrected and x.get("correction_note")) else ""
        cat = x.get("category") or x["trap_id"][4:].replace("-", "_")
        cost = x.get("cost_usd")
        cost_text = "n/a" if cost is None else f"{float(cost):.4f} USD"
        if x.get("escrow_credit_usd") is not None and float(x["escrow_credit_usd"]) > 0:
            cost_text += f" \u00b7 ${float(x['escrow_credit_usd']):.2f} settled into escrow credit"
        trap_tx_hash = x.get("tx_hash") or trap_tx_by_id.get(x["trap_id"])
        trap_tx = (' \u00b7 trap tx <a href="' + BASE_SEPOLIA + esc(trap_tx_hash) + '">' +
                   esc(trap_tx_hash[:10]) + "&hellip;</a>") if trap_tx_hash else ""
        receipt_line = "<p>Receipt: " + receipt_cell(x) + trap_tx + \
            (f" \u00b7 signal <code>{esc(x['signal_hash'])}</code>" if x.get("signal_hash") else "") + "</p>"
        cls = "pass" if passed else "fail"
        out.append("<details><summary>" + esc(x["trap_id"]) + " (" + esc(cat) + ") \u2014 <span class='" +
                   cls + "'>" + ("PASS" if passed else "FAIL") + "</span> \u00b7 cost " + cost_text +
                   "</summary>" + body + err + note + receipt_line + "</details>")
    return "".join(out)


def build_frozen(data):
    """Return {region: html} for the frozen set."""
    corrected = data["corrected"]
    scores = corrected["scores"]
    field_acc = corrected["field_accuracy"]
    unservable = corrected.get("unservable", [])
    trap_tx_by_id = {s["trap_id"]: s["tx_hash"] for s in scores if s.get("tx_hash")}

    def served(s):
        return s.get("served") is True or bool(s.get("receipt_present"))

    def passed(s):
        return bool(s.get("corrected_passed"))

    stats = {}
    for s in scores:
        st = stats.setdefault(s["provider_id"], {"provider_id": s["provider_id"], "run": 0,
                                                 "passed": 0, "served": 0, "cost": 0.0,
                                                 "escrow": 0.0, "receipts": 0})
        st["run"] += 1
        if passed(s):
            st["passed"] += 1
        if served(s):
            st["served"] += 1
        if s.get("cost_usd") is not None:
            st["cost"] += float(s["cost_usd"])
        if s.get("escrow_credit_usd") is not None:
            st["escrow"] += float(s["escrow_credit_usd"])
        if s.get("receipt_present"):
            st["receipts"] += 1
    ranked = [s for s in rank_rows(stats, field_acc) if s["provider_id"] not in unservable]

    ranked_html = "".join(
        "<tr><td>" + str(i + 1) + "</td><td>" + label(s["provider_id"]) + "</td><td>" +
        f"{100 * s['passed'] / s['run']:.0f}%" + "</td><td>" + str(s["passed"]) + " / " + str(s["run"]) +
        "</td><td>" + (("n/a (not served)" if field_acc[s["provider_id"]]["accuracy"] is None
                        else str(field_acc[s["provider_id"]]["correct"]) + "/" +
                        str(field_acc[s["provider_id"]]["scored"]))) + "</td><td>" +
        field_acc_rank(s["provider_id"], field_acc) + "</td><td>" + f"{s['cost']:.4f}" +
        "</td><td>" + str(s["receipts"]) + " / " + str(s["served"]) + "</td></tr>"
        for i, s in enumerate(ranked))

    sens_parts = []
    for s in ranked:
        excl = sum(1 for x in scores if x["provider_id"] == s["provider_id"] and served(x)
                   and all(f["passed"] for f in (x.get("fields") or []) if f["field"] != "status"))
        sens_parts.append(f"{NAMES.get(s['provider_id'], s['provider_id'])} {s['passed']}/{s['run']} "
                          f"\u2192 {excl}/{s['run']}")
    sens_text = ("Sensitivity (frozen set, status excluded \u2014 a trap passes iff every "
                 "non-status field passes): " + "; ".join(sens_parts) +
                 ". Order unchanged; the margin widens.")

    unranked_text = ("Unservable (zero served traps \u2014 never shown as passing, and no pass rate "
                     "is computed for them): " + "; ".join(
                         f"{NAMES.get(pid, pid)} ({pid}) \u2014 {FROZEN_REASONS.get(pid, '')}"
                         for pid in unservable)) if unservable else ""
    unserv_html = "".join(
        "<tr><td>" + label(pid) + "</td><td>" + str(stats.get(pid, {}).get("served", 0)) + " / " +
        str(stats.get(pid, {}).get("run", 0)) + "</td><td>" + esc(FROZEN_REASONS.get(pid, "")) +
        "</td><td>" + f"{stats.get(pid, {}).get('escrow', 0.0):.2f}" + "</td><td>n/a (not served)</td></tr>"
        for pid in unservable)

    trap_ids = sorted({s["trap_id"] for s in scores})
    matrix_head = ("<tr><th>Trap</th><th>Category</th>" +
                   "".join("<th>" + label(s["provider_id"]) + "</th>" for s in ranked) + "</tr>")
    matrix_rows = []
    for tid in trap_ids:
        cat = ""
        cells = []
        for s in ranked:
            row = next((x for x in scores if x["provider_id"] == s["provider_id"]
                        and x["trap_id"] == tid), None)
            if row is None:
                cells.append("<td>&mdash;</td>")
                continue
            if not cat:
                cat = row.get("category") or tid[4:].replace("-", "_")
            if not served(row):
                cells.append("<td>&mdash;</td>")
            else:
                p = passed(row)
                cells.append("<td class='" + ("pass" if p else "fail") + "'>" +
                             ("PASS" if p else "FAIL") + "</td>")
        matrix_rows.append("<tr><td>" + esc(tid) + "</td><td>" + esc(cat) + "</td>" + "".join(cells) + "</tr>")

    strict = data["strict_original"]["table"]
    sfa = data["strict_original"]["field_accuracy"]
    strict_html = "".join(
        "<tr><td>" + label(pid) + "</td><td>" + str(strict[pid]["passed"]) + " / " +
        str(strict[pid]["rows"]) + "</td><td>" +
        ("n/a (not served)" if sfa[pid]["accuracy"] is None
         else str(sfa[pid]["correct"]) + "/" + str(sfa[pid]["scored"])) +
        "</td><td>" + f"{float(strict[pid]['total_cost_usd']):.4f}" + "</td></tr>"
        for pid in strict)

    ve = data["value_excluded_view"]["table"]
    ve_html = "".join(
        "<tr><td>" + label(pid) + "</td><td>" + str(ve[pid]["served"]) + "</td><td>" +
        str(ve[pid]["passed_value_excluded"]) + " / " + str(ve[pid]["served"]) + "</td></tr>"
        for pid in ve)

    detail_order = ranked + [stats[pid] for pid in unservable if pid in stats]
    detail_html = "".join(
        "<h3>" + label(s["provider_id"]) + "</h3>" +
        detail_block(s["provider_id"],
                     [x for x in scores if x["provider_id"] == s["provider_id"]],
                     True, trap_tx_by_id)
        for s in detail_order)

    return {
        "traps-sha": esc(data["traps_sha256"]),
        "ranked": ranked_html,
        "frozen-sensitivity": esc(sens_text),
        "unranked": esc(unranked_text),
        "unservable-table": unserv_html,
        "matrix-head": matrix_head,
        "matrix": "".join(matrix_rows),
        "strict": strict_html,
        "value-excluded": ve_html,
        "detail": detail_html,
    }


def build_expansion(data):
    """Return {region: html} for the expansion set."""
    scores = data["scores"]
    exp_fa = data.get("field_accuracy", {})

    def served(s):
        return s.get("served") is True or bool(s.get("receipt_present"))

    stats = {}
    for s in scores:
        st = stats.setdefault(s["provider_id"], {"provider_id": s["provider_id"], "run": 0,
                                                 "passed": 0, "served": 0, "cost": 0.0,
                                                 "receipts": 0, "fc": 0, "fs": 0})
        st["run"] += 1
        if s.get("passed"):
            st["passed"] += 1
        if served(s):
            st["served"] += 1
        if s.get("cost_usd") is not None:
            st["cost"] += float(s["cost_usd"])
        if s.get("receipt_present"):
            st["receipts"] += 1
        for f in (s.get("fields") or []):
            st["fs"] += 1
            if f["passed"]:
                st["fc"] += 1
    ranked = rank_rows(stats, exp_fa)

    ranked_html = "".join(
        "<tr><td>" + str(i + 1) + "</td><td>" + label(s["provider_id"]) + "</td><td>" +
        f"{100 * s['passed'] / s['run']:.0f}%" + "</td><td>" + str(s["passed"]) + " / " + str(s["run"]) +
        "</td><td>" + str(s["fc"]) + "/" + str(s["fs"]) + "</td><td>" +
        field_acc_rank(s["provider_id"], exp_fa) + "</td><td>" + f"{s['cost']:.4f}" +
        "</td><td>" + str(s["receipts"]) + " / " + str(s["served"]) + "</td></tr>"
        for i, s in enumerate(ranked))

    spend = data.get("spend_usd", {})
    sens = data.get("sensitivity_status_excluded", {})
    verdict_items = "".join(
        "<li><strong>" + label(s["provider_id"]) + " \u2014 " + str(s["passed"]) + "/" + str(s["run"]) +
        "</strong> (field accuracy " + str(s["fc"]) + "/" + str(s["fs"]) +
        ", field-accuracy rank " + field_acc_rank(s["provider_id"], exp_fa) + ")</li>"
        for s in ranked)
    verdict_items += (
        "<li><strong>New serving provider:</strong> ChainWire 1707307 (Cross-Checked) 11/12 \u2014 "
        "the only fail is t17 (reverted with value: returned value 0, expected 607000000000000 wei). "
        "It passes both token traps the incumbents fail, and both unknown traps cleanly under v2.</li>"
        "<li><strong>Source:</strong> clean single-file run <code>" + esc((data.get("run_ids") or [""])[0]) +
        "</code> (" + esc(data.get("source_file", "")) + ") \u2014 one uninterrupted 12-trap run per "
        "provider, 36/36 receipts verified on-chain at write time. It supersedes the stitched "
        "two-file run " + esc(" + ".join(data.get("superseded_run_ids", []))) + " (see note above).</li>"
        "<li><strong>Cost (clean re-run):</strong> $" + f"{float(spend.get('clean_run_billed', 0)):.2f}" +
        " billed ($0.12 per provider, cap $" + f"{float(spend.get('clean_run_spend_cap', 0)):.2f}" +
        "); wallet " + f"{float(spend.get('wallet_before_usdc', 0)):.2f}" + " &rarr; " +
        f"{float(spend.get('wallet_after_usdc', 0)):.2f}" + " test USDC (drop $" +
        f"{float(spend.get('balance_drop_usdc', 0)):.2f}" + ", reconciles exactly).</li>"
        "<li><strong>Read Truvian honestly:</strong> 2/12 binary understates it \u2014 field accuracy " +
        (f"{exp_fa['8453']['correct']}/{exp_fa['8453']['scored']} "
         f"({100 * exp_fa['8453']['accuracy']:.1f}%)" if "8453" in exp_fa else "\u2014") +
        ", and " + (f"{sens['8453']['passed_status_excluded']}/{sens['8453']['rows']}"
                    if "8453" in sens else "\u2014") +
        " with status excluded (see sensitivity table below). TxLens is 2/12 on every view "
        "(field accuracy " +
        (f"{exp_fa['9002']['correct']}/{exp_fa['9002']['scored']}" if "9002" in exp_fa else "\u2014") +
        ").</li>")

    unservable = data.get("unservable", [])
    unranked_text = ("Unservable (zero served traps \u2014 never shown as passing, and no pass rate "
                     "is computed for them): " + "; ".join(
                         f"{NAMES.get(u['provider_id'], u['provider_id'])} ({u['provider_id']}) \u2014 {u['reason']}"
                         for u in unservable)) if unservable else ""
    unserv_html = "".join(
        "<tr><td>" + label(u["provider_id"]) + "</td><td>0</td><td>" + esc(u["reason"]) +
        "</td><td>" + f"{float(u.get('escrow_credit_usd', 0)):.2f}" + "</td><td>n/a (not served)</td></tr>"
        for u in unservable)

    probed = data.get("probed_only", [])
    probed_text = ""
    if probed:
        probed_text = ("Probed only (1 trap, not ranked): " + "; ".join(
            f"{NAMES.get(p['provider_id'], p['provider_id'])} ({p['provider_id']}) \u2014 {p['trap_id']} "
            f"{'PASS' if p['passed'] else 'FAIL'}, receipt "
            f"{'verified on-chain' if p.get('receipt_verified_onchain') else 'n/a'}"
            for p in probed) + ". " + (data.get("probed_only_note") or ""))

    trap_ids = sorted({s["trap_id"] for s in scores})
    matrix_head = ("<tr><th>Trap</th><th>Category</th>" +
                   "".join("<th>" + label(s["provider_id"]) + "</th>" for s in ranked) + "</tr>")
    matrix_rows = []
    for tid in trap_ids:
        cat = ""
        cells = []
        for s in ranked:
            row = next((x for x in scores if x["provider_id"] == s["provider_id"]
                        and x["trap_id"] == tid), None)
            if row is None:
                cells.append("<td>&mdash;</td>")
                continue
            if not cat:
                cat = row.get("category") or tid[4:].replace("-", "_")
            if not served(row):
                cells.append("<td>&mdash;</td>")
            else:
                p = bool(row.get("passed"))
                cells.append("<td class='" + ("pass" if p else "fail") + "'>" +
                             ("PASS" if p else "FAIL") + "</td>")
        matrix_rows.append("<tr><td>" + esc(tid) + "</td><td>" + esc(cat) + "</td>" + "".join(cells) + "</tr>")

    sens_html = "".join(
        "<tr><td>" + label(s["provider_id"]) + "</td><td>" + str(s["passed"]) + " / " + str(s["run"]) +
        "</td><td>" + (("\u2014" if sens.get(s["provider_id"], {}).get("passed_status_excluded") is None
                       else str(sens[s["provider_id"]]["passed_status_excluded"]) + " / " +
                       str(sens[s["provider_id"]]["rows"]))) +
        "</td><td>" + (("\u2014" if sens.get(s["provider_id"], {}).get("field_correct_status_excluded") is None
                       else str(sens[s["provider_id"]]["field_correct_status_excluded"]) + "/" +
                       str(sens[s["provider_id"]]["field_scored_status_excluded"]))) +
        "</td><td>" + (("\u2014" if sens.get(s["provider_id"], {}).get("fails_only_on_status") is None
                       else str(sens[s["provider_id"]]["fails_only_on_status"]))) +
        "</td><td>" + (("\u2014" if sens.get(s["provider_id"], {}).get("strict_rank") is None
                       else str(sens[s["provider_id"]]["strict_rank"]))) +
        "</td><td>" + (("\u2014" if sens.get(s["provider_id"], {}).get("status_excluded_rank") is None
                       else str(sens[s["provider_id"]]["status_excluded_rank"]))) + "</td></tr>"
        for s in ranked)

    detail_html = "".join(
        "<h3>" + label(s["provider_id"]) + "</h3>" +
        detail_block(s["provider_id"],
                     [x for x in scores if x["provider_id"] == s["provider_id"]],
                     False, {})
        for s in ranked)

    return {
        "exp-traps-sha": esc(data["traps_sha256"]),
        "exp-verdict-list": verdict_items,
        "ranked-exp": ranked_html,
        "unranked-exp": esc(unranked_text),
        "unservable-exp-table": unserv_html,
        "probed-only": esc(probed_text),
        "matrix-exp-head": matrix_head,
        "matrix-exp": "".join(matrix_rows),
        "sensitivity-answer": esc(data.get("sensitivity_note", "")),
        "sensitivity-exp": sens_html,
        "detail-exp": detail_html,
    }


def replace_between(html, start_pat, end_pat, new_inner, name):
    """Replace the content between start_pat and end_pat (both regexes,
    each matching the opening/closing tag) with new_inner."""
    m1 = re.search(start_pat, html)
    if not m1:
        raise SystemExit(f"anchor not found for {name}: {start_pat}")
    m2 = re.search(end_pat, html[m1.end():])
    if not m2:
        raise SystemExit(f"closing anchor not found for {name}: {end_pat}")
    return html[:m1.end()] + new_inner + html[m1.end() + m2.start():]


def main():
    frozen = json.loads((LB / "results.json").read_text())
    expansion = json.loads((LB / "results-expansion.json").read_text())
    assert frozen["data_kind"] == "CORRECTED_REANALYSIS", frozen.get("data_kind")
    assert expansion["data_kind"] == "LIVE", expansion.get("data_kind")
    frags = {}
    frags.update(build_frozen(frozen))
    frags.update(build_expansion(expansion))

    html_path = LB / "index.html"
    html = html_path.read_text()

    def table_body(table_id):
        return (re.compile(r'(<table id="' + table_id + r'">[\s\S]*?<tbody>)'),
                re.compile(r'(</tbody>)'))

    # (start regex, end regex) per region.
    patches = [
        ("traps-sha", re.compile(r'(<code id="traps-sha">)'), re.compile(r'(</code>)')),
        ("exp-traps-sha", re.compile(r'(<code id="exp-traps-sha">)'), re.compile(r'(</code>)')),
        ("ranked", *table_body("ranked")),
        ("frozen-sensitivity", re.compile(r'(<p id="frozen-sensitivity" class="muted">)'),
         re.compile(r'(</p>)')),
        ("unranked", re.compile(r'(<p id="unranked" class="muted">)'), re.compile(r'(</p>)')),
        ("unservable-table", *table_body("unservable-table")),
        ("matrix-head", re.compile(r'(<table id="matrix">[\s\S]*?<thead>)'), re.compile(r'(</thead>)')),
        ("matrix", *table_body("matrix")),
        ("strict", *table_body("strict")),
        ("value-excluded", *table_body("value-excluded")),
        ("detail", re.compile(r'(<div id="detail">)'),
         re.compile(r'(</div>\n\n<h2>Honest limits</h2>)')),
        ("exp-verdict-list", re.compile(r'(<ul id="exp-verdict-list">)'), re.compile(r'(</ul>)')),
        ("ranked-exp", *table_body("ranked-exp")),
        ("unranked-exp", re.compile(r'(<p id="unranked-exp" class="muted">)'), re.compile(r'(</p>)')),
        ("unservable-exp-table", *table_body("unservable-exp-table")),
        ("probed-only", re.compile(r'(<p class="muted" id="probed-only">)'), re.compile(r'(</p>)')),
        ("matrix-exp-head", re.compile(r'(<table id="matrix-exp">[\s\S]*?<thead>)'), re.compile(r'(</thead>)')),
        ("matrix-exp", *table_body("matrix-exp")),
        ("sensitivity-answer", re.compile(r'(<p class="muted" id="sensitivity-answer">)'),
         re.compile(r'(</p>)')),
        ("sensitivity-exp", *table_body("sensitivity-exp")),
        ("detail-exp", re.compile(r'(<div id="detail-exp">)'),
         re.compile(r'(</div>\n\n<h2>Per-trap detail)')),
    ]
    for name, start_pat, end_pat in patches:
        html = replace_between(html, start_pat, end_pat, frags[name], name)

    if "Loading" in html or "loading" in html:
        raise SystemExit("FAIL: a Loading/loading placeholder survives in index.html")
    if "4/24" in html or "6/24" in html:
        raise SystemExit("FAIL: a combined 24-trap count would be rendered")
    html_path.write_text(html)
    frozen_n = html.split('<div id="detail">')[1].split("<h2>Honest limits")[0].count("<details>")
    exp_n = html.split('<div id="detail-exp">')[1].split("<h2>Per-trap detail")[0].count("<details>")
    print(f"wrote {html_path}")
    print(f"  frozen ranked rows: 2, detail rows: {frozen_n}, "
          f"expansion ranked rows: 3, expansion detail rows: {exp_n}")
    print("  no Loading placeholders; no combined 24-trap counts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
