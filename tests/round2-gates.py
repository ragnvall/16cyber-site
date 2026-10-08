#!/usr/bin/env python3
"""Failing-first content gates for PR #1 round-2 fixes.
Run against a given index.html / OWED-FROM-JOEL.md pair:
    python3 tests/round2-gates.py <index.html> <OWED-FROM-JOEL.md>
Exits non-zero and prints each failing check if any assertion fails.
"""
import sys

def check(name, condition, failures):
    if not condition:
        failures.append(name)

def main():
    index_path, owed_path = sys.argv[1], sys.argv[2]
    html = open(index_path, encoding="utf-8").read()
    owed = open(owed_path, encoding="utf-8").read()
    failures = []

    # Finding 1 (MED, index.html:96): A.1.13 quoted word for word + database-of-record sentence.
    check(
        "fair-opportunity-first-sentence-quoted",
        "Contractors will be provided a fair opportunity at the individual order level as appropriate per FAR Part 16.505(b), including the SEWP RFQ tools." in html,
        failures,
    )
    check(
        "fair-opportunity-database-of-record-sentence-present",
        "shall not market, quote or otherwise offer for sale, any IT Solutions not listed under this contract, until the said solutions are included in the SEWP database of record" in html,
        failures,
    )
    check(
        "fair-opportunity-old-paraphrase-gone",
        "using the SEWP RFQ system" not in html,
        failures,
    )

    # Finding 2 (LOW): OWED-FROM-JOEL.md gets a confirm-active-or-start-date item.
    check(
        "owed-confirm-active-or-start-date-item-present",
        "Confirm the contract is active and orderable" in owed or "confirm-active" in owed.lower(),
        failures,
    )

    # Finding 3 (LOW): OWED-FROM-JOEL.md gets policy text / Why 16 Cyber / capability statement doc bullets.
    check(
        "owed-installation-warranty-support-policy-bullet",
        "A.5.1(3b)" in owed and "POLICY" in owed.upper(),
        failures,
    )
    check(
        "owed-why-16-cyber-bullet",
        "Why 16 Cyber" in owed,
        failures,
    )
    check(
        "owed-capability-statement-document-bullet",
        "capability statement" in owed.lower() and "document" in owed.lower(),
        failures,
    )

    # Finding 4 (LOW, index.html:17): CAGE/UEI strip sits inside a landmark.
    header_start = html.find("<header")
    header_end = html.find("</header>")
    id_strip_pos = html.find('class="id-strip"')
    check(
        "id-strip-inside-header-landmark",
        header_start != -1 and header_end != -1 and header_start < id_strip_pos < header_end,
        failures,
    )

    # Finding 5 (LOW, index.html:10): no Google Fonts call; favicon served.
    check(
        "no-google-fonts-network-call",
        "fonts.googleapis.com" not in html and "fonts.gstatic.com" not in html,
        failures,
    )
    check(
        "favicon-link-present",
        'rel="icon"' in html and "favicon.ico" in html,
        failures,
    )

    if failures:
        print("FAIL:", ", ".join(failures))
        return 1
    print("PASS: all round-2 gate checks passed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
