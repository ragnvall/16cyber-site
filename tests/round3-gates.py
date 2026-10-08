#!/usr/bin/env python3
"""Failing-first content gates for PR #1 round-3 fixes.
Run against the repo root:
    python3 tests/round3-gates.py <index.html> <tests/round2-gates.py> <assets/fonts dir>
Exits non-zero and prints each failing check if any assertion fails.
"""
import sys
import os

def check(name, condition, failures):
    if not condition:
        failures.append(name)

def main():
    index_path, gates2_path, fonts_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    html = open(index_path, encoding="utf-8").read()
    gates2 = open(gates2_path, encoding="utf-8").read()
    failures = []

    VERBATIM = (
        "shall not market, quote or otherwise offer for sale, any IT Solutions "
        "not listed under this contract, until the said solutions are included "
        "in the SEWP database of record, and available to all Government end-users"
    )
    MISQUOTE = (
        "shall not market, quote, or otherwise offer for sale any IT Solutions "
        "not listed under this contract until those items are included in the "
        "SEWP database of record and available to all Government end-users"
    )
    # The round-2 gate only asserts through "database of record" (it does not
    # re-check the trailing "and available..." clause), so the gate-side check
    # uses that same prefix rather than the full VERBATIM sentence.
    VERBATIM_GATE_PREFIX = (
        "shall not market, quote or otherwise offer for sale, any IT Solutions "
        "not listed under this contract, until the said solutions are included "
        "in the SEWP database of record"
    )
    MISQUOTE_GATE_PREFIX = (
        "shall not market, quote, or otherwise offer for sale any IT Solutions "
        "not listed under this contract until those items are included in the "
        "SEWP database of record"
    )

    # Finding 1 (MED, index.html:94 + tests/round2-gates.py:28): verbatim A.1.13
    # database-of-record sentence, word for word, in both the page and the gate.
    check("r3-database-of-record-verbatim-in-page", VERBATIM in html, failures)
    check("r3-database-of-record-misquote-gone-from-page", MISQUOTE not in html, failures)
    check("r3-database-of-record-verbatim-in-gate", VERBATIM_GATE_PREFIX in gates2, failures)
    check("r3-database-of-record-misquote-gone-from-gate", MISQUOTE_GATE_PREFIX not in gates2, failures)
    check("r3-mdash-after-quote-replaced-with-period", "&mdash; so every quote" not in html, failures)

    # Finding 2 (LOW, index.html:94): gloss must not overclaim beyond the clause;
    # either scoped to RFQ or dropped entirely.
    overclaim = "so every quote comes only from items already in the SEWP database"
    check("r3-gloss-overclaim-gone", overclaim not in html, failures)
    if "every quote" in html.lower() and "sewp database" in html.lower():
        check(
            "r3-gloss-scoped-to-rfq-if-present",
            "RFQ" in html or "request for quote" in html,
            failures,
        )

    # Finding 3 (LOW, assets/fonts/): OFL licence text must ship with the fonts.
    ofl_path = os.path.join(fonts_dir, "OFL.txt")
    check("r3-ofl-licence-file-present", os.path.isfile(ofl_path), failures)
    if os.path.isfile(ofl_path):
        ofl_text = open(ofl_path, encoding="utf-8").read()
        check("r3-ofl-licence-mentions-barlow", "Barlow" in ofl_text, failures)
        check(
            "r3-ofl-licence-is-sil-ofl",
            "SIL OPEN FONT LICENSE" in ofl_text.upper(),
            failures,
        )

    if failures:
        print("FAIL:", ", ".join(failures))
        return 1
    print("PASS: all round-3 gate checks passed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
