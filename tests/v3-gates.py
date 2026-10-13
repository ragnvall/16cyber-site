#!/usr/bin/env python3
"""Spec gates for v3: the page has the same sections as NASA's example holder website, in 16 Cyber's style (owner 10-13).
Run from the repo root:
    python3 tests/v3-gates.py <index.html> <preview.html>
styles.css is read from the same folder as index.html.
Exits non-zero and prints each failing check if any assertion fails.
Standard library only.
"""
import os
import re
import sys
from html.parser import HTMLParser

# The 22 ids from the design book's "All variables" table (amendment 10-13 "NASA shape": sewp_holder_page added;
# pm_name, dpm_name and brands_confirmed are FILLED from Joel's and Daniel's emails of 10-13).
BOOK_IDS = [
    "contract_number", "award_date", "period_of_performance",
    "pm_name", "dpm_name", "sewp_phone_number",
    "surcharge_pct", "sewp_holder_page",
    "naics_codes", "office_address", "small_business_status", "certifications", "jv_member_names",
    "brands_confirmed", "capabilities_a1_a6", "past_performance",
    "ordering_guide_pdf", "guide_version_date", "support_policy_text", "capability_statement_design",
    "about_us_text", "differentiators",
]
ALWAYS_ON = set()
# NASA shape (owner 10-13): the home page carries only what NASA's example page carries, plus the vendors.
# Everything else stays in the book for the future pages (ordering guide, capability statement, about us).
OFF_HOME = {"award_date", "naics_codes", "office_address", "small_business_status", "certifications", "jv_member_names",
            "capabilities_a1_a6", "past_performance", "capability_statement_design", "about_us_text", "differentiators"}
# Khai Huynh's email 10-13 (in writing): contract number, period of performance, surcharge, phone.
FILLED = {"brands_confirmed", "pm_name", "dpm_name", "contract_number", "period_of_performance", "surcharge_pct", "sewp_phone_number"}
HOME_IDS = [i for i in BOOK_IDS if i not in OFF_HOME and i not in FILLED]
FACT_ROWS = ["Contract number", "Category", "Contract type", "Period of performance", "SEWP surcharge",
             "UEI", "CAGE code", "SEWP contract holder page"]
EMAIL = "sewp@16cyber.com"
CLAUSE_1 = ("Contractors will be provided a fair opportunity at the individual order level "
            "as appropriate per FAR Part 16.505(b), including the SEWP RFQ tools.")
CLAUSE_2 = ("shall not market, quote or otherwise offer for sale, any IT Solutions not listed "
            "under this contract, until the said solutions are included in the SEWP database "
            "of record, and available to all Government end-users")
FORM_NOTE = "This form is not connected yet. Until it is, email sewp@16cyber.com."
BANNER = ("Preview, not the live site. Purple items in [brackets] are the facts still needed; "
          "the live page leaves them out until they are in writing.")
ALLOWED_HOSTS = {"sewp.nasa.gov", "www.sewp.nasa.gov", "16cyber.com", "www.16cyber.com",
                 "storagehawk.com", "www.storagehawk.com", "inodeink.com", "www.inodeink.com"}
FOOTER_LINKS = {"https://www.sewp.nasa.gov/": "NASA SEWP", "https://www.storagehawk.com/": "StorageHawk", "https://inodeink.com/": "INODE Ink"}
SECTIONS = ["top", "about-sewp", "fair-opportunity", "contract-facts", "contacts", "ordering-guide", "vendors"]  # owner 10-13: one How to contact section
NAV = ["#contract-facts", "#contacts", "#fair-opportunity", "#vendors"]
SEWP_HELP = ("help@sewp.nasa.gov", "(301) 286-1478", "7:30")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr", "path", "circle", "rect", "line", "polyline", "polygon", "ellipse"}
ORANGE = re.compile(r"#ff6600\b|#f60\b|var\(--orange\)|rgba?\(\s*255\s*,\s*102\s*,\s*0\b", re.I)


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children, self.text = [], []

    def all_text(self):
        out = list(self.text)
        for c in self.children:
            out.append(c.all_text())
        return "".join(out)

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()

    def has_ancestor(self, pred):
        p = self.parent
        while p is not None:
            if pred(p):
                return True
            p = p.parent
        return False


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", [], None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.text.append(data)


def parse(html):
    t = Tree()
    t.feed(html)
    return t.root


def text_outside_vars(node):
    if "data-var" in node.attrs:
        return ""
    return "".join(node.text) + "".join(text_outside_vars(c) for c in node.children)


def find(root, pred):
    return [n for n in root.walk() if pred(n)]


def check(name, cond, failures):
    if not cond:
        failures.append(name)


def css_color_decls(css):
    """Yield (property, value) for every declaration in the stylesheet."""
    body = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for block in re.findall(r"\{([^{}]*)\}", body):
        for decl in block.split(";"):
            if ":" in decl:
                prop, val = decl.split(":", 1)
                yield prop.strip().lower(), val.strip()


def script_problems(src):
    """The page may carry exactly one script (owner amendment 10-12): inline,
    no src, no network calls, under 40 lines."""
    scripts = re.findall(r"<script\b([^>]*)>(.*?)</script>", src, re.S | re.I)
    if len(scripts) != 1 or len(re.findall(r"<script\b", src, re.I)) != 1:
        return "expected exactly one <script>, found %d" % len(re.findall(r"<script\b", src, re.I))
    attrs, body = scripts[0]
    if re.search(r"\bsrc\s*=", attrs, re.I):
        return "script has a src"
    if re.search(r"\bfetch\s*\(|XMLHttpRequest|\bimport\b|sendBeacon|WebSocket|EventSource", body):
        return "script makes a network call"
    if len(body.strip().splitlines()) >= 40:
        return "script is 40 lines or more"
    return ""



def main():
    index_path, preview_path = sys.argv[1], sys.argv[2]
    css_path = os.path.join(os.path.dirname(os.path.abspath(index_path)), "styles.css")
    html = open(index_path, encoding="utf-8").read()
    css = open(css_path, encoding="utf-8").read() if os.path.isfile(css_path) else ""
    preview = open(preview_path, encoding="utf-8").read() if os.path.isfile(preview_path) else ""
    failures = []
    root = parse(html)
    vars_ = find(root, lambda n: "data-var" in n.attrs)
    ids = {n.attrs["data-var"] for n in vars_}
    page_text = " ".join(text_outside_vars(root).split())
    sec = {s.attrs.get("id"): s for s in find(root, lambda n: n.tag == "section")}
    def stext(i): return " ".join(text_outside_vars(sec[i]).split()) if i in sec else ""

    # 1. Variables: the book's ids, the home set present and hidden, nothing unknown, bracketed labels.
    check("book-has-22-ids", len(BOOK_IDS) == 22 and len(HOME_IDS) == 4, failures)
    missing = [i for i in HOME_IDS if i not in ids]
    check("all-4-home-ids-present (missing: %s)" % ", ".join(missing), not missing, failures)
    unknown = sorted(ids - set(HOME_IDS))
    check("no-unknown-data-var-ids (%s)" % ", ".join(unknown), not unknown, failures)
    shown = [n.attrs["data-var"] for n in vars_ if "hidden" not in n.attrs]
    check("every-variable-hidden-on-live (shown: %s)" % ", ".join(shown), not shown, failures)
    check("css-hidden-attribute-forced", re.search(r"\[hidden\]\s*\{[^}]*display\s*:\s*none\s*!important", css) is not None, failures)
    unbracketed = [n.attrs["data-var"] for n in vars_ if not re.search(r"\[[^\]]+\]", n.all_text())]
    check("every-variable-carries-a-bracketed-label (%s)" % ", ".join(unbracketed), not unbracketed, failures)
    check("no-filled-ids-as-variables", not (ids & FILLED), failures)
    on_cells = [n.attrs["data-var"] for n in vars_ if n.tag in ("dt", "dd")]
    check("hidden-rows-hide-as-a-unit (variable on a cell: %s)" % ", ".join(on_cells), not on_cells, failures)

    # 2. Preview: nothing hidden, chips, banner, fully inlined.
    if not preview:
        failures.append("preview-file-missing")
    else:
        proot = parse(preview)
        pvars = find(proot, lambda n: "data-var" in n.attrs)
        check("preview-has-all-4-home-ids", all(i in {n.attrs["data-var"] for n in pvars} for i in HOME_IDS), failures)
        still = [n.attrs["data-var"] for n in pvars if "hidden" in n.attrs]
        check("preview-no-variable-hidden (%s)" % ", ".join(still), not still, failures)
        check("preview-chip-style", all(s.lower() in preview.lower() for s in ("#EFE7FF", "#3B1D8F", "#C9B8F5")), failures)
        check("preview-banner", BANNER in " ".join(parse(preview).all_text().split()), failures)
        bad = sorted({m for m in re.findall(r"https?://([^/\"'\s>]+)", preview) if m.lower() not in ALLOWED_HOSTS})
        check("preview-no-outside-http (%s)" % ", ".join(bad), not bad, failures)
        check("preview-css-inlined", re.search(r"<link[^>]+stylesheet", preview, re.I) is None and "<style" in preview, failures)
        check("preview-under-1.5MB", len(preview.encode("utf-8")) < 1.5 * 1024 * 1024, failures)
        check("preview-no-script", re.search(r"<script\b", preview, re.I) is None, failures)
        check("purple-only-in-preview", not any(s in (html + css).upper() for s in ("#EFE7FF", "#3B1D8F", "#C9B8F5")), failures)

    # 3. The sections, in NASA's order, each labelled with one h2 (the top has the h1).
    order = [s.attrs.get("id") for s in find(root, lambda n: n.tag == "section")]
    check("sections-in-nasa-order (%s)" % order, order == SECTIONS, failures)
    for i in SECTIONS:
        s = sec.get(i)
        check("section-%s-present" % i, s is not None, failures)
        if s is None: continue
        h2 = [n for n in s.walk() if n.tag == "h2"]; h1 = [n for n in s.walk() if n.tag == "h1"]
        check("section-%s-one-heading" % i, (len(h2) == 1 and not h1) or (i == "top" and len(h1) == 1 and not h2), failures)
        check("section-%s-labelled" % i, "aria-labelledby" in s.attrs, failures)
    check("exactly-one-h1", len(find(root, lambda n: n.tag == "h1")) == 1, failures)
    levels = [int(n.tag[1]) for n in root.walk() if re.fullmatch(r"h[1-6]", n.tag)]
    check("no-heading-level-skips", levels[:1] == [1] and not [b for a, b in zip(levels, levels[1:]) if b > a + 1], failures)
    for gone in ("How to buy", "What we supply", "Request a quote", "Get a quote"):
        check("gone: " + gone, gone not in page_text, failures)

    # 4. The top: the holder line and the contract number, nothing else (no sentence, no email, no ids).
    top = stext("top")
    check("top-says-holder", "NASA SEWP VI, Category A contract holder" in top, failures)
    check("top-shows-contract-number", "80TECH26D0796" in top, failures)
    check("top-nothing-else", "top" in sec and EMAIL not in top and "9W5N7" not in top and "MZPNX5XEM9N5" not in top
          and len(top) < 140, failures)

    # 5. About SEWP: plain words, no fee number outside a variable, says "soup".
    about = stext("about-sewp")
    check("about-sewp-explains", "SEWP" in about and "soup" in about.lower() and "federal" in about.lower(), failures)
    check("0.34-only-in-contract-information", page_text.count("0.34") == 1 and "0.34%" in stext("contract-facts"), failures)

    # 6. Fair opportunity: the one plain line and the clause, verbatim (round2/round3 gates pin the wording).
    fo = stext("fair-opportunity")
    check("fair-opportunity-clause-present", CLAUSE_1 in fo and CLAUSE_2 in fo, failures)
    check("fair-opportunity-plain-line", "fair chance" in fo.lower() or "fair opportunity" in fo.lower(), failures)

    # 7. How to contact: ONE section (owner 10-13) with 16 Cyber first, then NASA's own help desk as text, SEWP site linked.
    cs = stext("contacts")
    check("contacts-heading-is-how-to-contact", any(n.tag == "h2" and " ".join(n.all_text().split()) == "How to contact" for n in sec["contacts"].walk()) if "contacts" in sec else False, failures)
    check("contacts-two-groups-16cyber-then-nasa", [" ".join(n.all_text().split()) for n in sec["contacts"].walk() if n.tag == "h3"] == ["16 Cyber", "NASA SEWP"] if "contacts" in sec else False, failures)
    check("contacts-has-nasa-help-desk", all(x in cs for x in SEWP_HELP), failures)
    check("contacts-links-sewp-site", any(n.tag == "a" and n.attrs.get("href", "").startswith("https://www.sewp.nasa.gov") for n in sec["contacts"].walk()) if "contacts" in sec else False, failures)

    # 8. Contract information: exactly NASA's rows plus CAGE, in order; hidden rows hide as a unit.
    facts_dl = find(root, lambda n: n.tag == "dl" and "facts" in n.attrs.get("class", "").split())
    rows = [" ".join(n.all_text().split()) for d in facts_dl for n in d.walk() if n.tag == "dt"]
    check("facts-rows-in-order (%s)" % rows, rows == FACT_ROWS, failures)
    cf = stext("contract-facts")
    check("facts-category-and-type", "Category A" in cf and "GWAC" in cf, failures)
    check("facts-cage-uei", "9W5N7" in cf and "MZPNX5XEM9N5" in cf, failures)
    check("facts-slot-sewp_holder_page", any(n.attrs.get("data-var") == "sewp_holder_page" for d in facts_dl for n in d.walk()), failures)
    for fact in ("80TECH26D0796", "November 1, 2026 to October 31, 2036", "0.34%"):
        check("facts-show-" + fact, fact in cf, failures)

    # 9. Contacts: PM and DPM by name (Joel's email 10-13), ONE email on the whole page, the phone slot, the problem-order line.
    ct = stext("contacts")
    check("contacts-pm-dpm-named", "Program Manager" in ct and "Khai Huynh" in ct and "Deputy Program Manager" in ct and "Jessica Hagood" in ct, failures)
    check("contacts-email-here", EMAIL in ct, failures)
    check("email-exactly-once-on-page (%d)" % page_text.count(EMAIL), page_text.count(EMAIL) == 1, failures)
    check("contacts-phone-shown", "888-714-6633" in ct and "7397" in ct, failures)
    check("contacts-problem-order-line", "problem with an order" in ct.lower() and "same email" in ct.lower(), failures)
    check("phone-exactly-once-on-page (%d)" % page_text.count("888-714-6633"), page_text.count("888-714-6633") == 1, failures)
    check("no-mailto-anywhere", "mailto:" not in html.lower(), failures)

    # 10. Ordering guide: the download slot and the support policy slot, hidden until the files exist.
    og = sec.get("ordering-guide")
    check("ordering-guide-slots", og is not None and all(any(n.attrs.get("data-var") == v for n in og.walk())
          for v in ("ordering_guide_pdf", "support_policy_text")), failures)
    check("ordering-guide-nothing-visible-but-the-heading-and-one-line", og is not None and len(stext("ordering-guide")) < 220, failures)

    # 11. Vendors: the filled list, visible, names without brackets, no authorization claim.
    vb = find(root, lambda n: "brands-block" in n.attrs.get("class", "").split())
    check("one-vendor-list", len(vb) == 1 and vb[0].has_ancestor(lambda p: p.attrs.get("id") == "vendors"), failures)
    names = [" ".join(n.all_text().split()) for b in vb for n in b.walk() if n.tag == "li"]
    check("vendor-names-present-no-brackets (%d)" % len(names), len(names) >= 60 and all(v and "[" not in v for v in names), failures)
    check("vendor-list-no-authorized-claim", "authorized" not in stext("vendors").lower(), failures)

    # 12. Nav and anchors, header height, jump targets.
    nav = find(root, lambda n: n.tag == "nav")
    check("nav-four-links", nav and [n.attrs.get("href") for n in nav[0].walk() if n.tag == "a"] == NAV, failures)
    ids_on_page = {n.attrs["id"] for n in root.walk() if "id" in n.attrs}
    anchors = [n.attrs["href"][1:] for n in root.walk() if n.tag == "a" and n.attrs.get("href", "").startswith("#")]
    dangling = sorted({a for a in anchors if a not in ids_on_page})
    check("anchors-resolve (%s)" % ", ".join(dangling), not dangling, failures)
    margin_sels = set()
    for sel_group, block in re.findall(r"([^{}]+)\{([^{}]*)\}", re.sub(r"/\*.*?\*/", "", css, flags=re.S)):
        if re.search(r"scroll-margin-top\s*:\s*var\(--header-h\)", block):
            margin_sels |= {" ".join(x.split()) for x in sel_group.split(",")}
    covered = lambda n: ("#" + n.attrs["id"]) in margin_sels or (
        "main section[id]" in margin_sels and n.tag == "section" and n.has_ancestor(lambda p: p.tag == "main"))
    targets = {n.attrs["id"]: n for n in root.walk() if "id" in n.attrs and n.attrs["id"] in set(anchors)}
    uncovered = sorted(i for i, n in targets.items() if not covered(n))
    check("jump-targets-clear-header (%s)" % ", ".join(uncovered), not uncovered and "main" in targets, failures)
    check("header-height-set-per-breakpoint", len(re.findall(r"--header-h\s*:\s*\d+px", css)) >= 3, failures)

    # 13. Footer: the three links, identifiers, the 508 line, and NO email (it lives in Contacts).
    footer = find(root, lambda n: n.tag == "footer")
    ft = " ".join(text_outside_vars(footer[0]).split()) if footer else ""
    flinks = {n.attrs.get("href"): " ".join(n.all_text().split()) for f in footer for n in f.walk()
              if n.tag == "a" and n.attrs.get("href", "").startswith("https://")}
    check("footer-links-to-sewp-and-members (%s)" % sorted(set(FOOTER_LINKS) - set(flinks)),
          all(h in flinks and flinks[h] == t for h, t in FOOTER_LINKS.items()), failures)
    check("footer-identifiers", "NASA SEWP VI, Category A" in ft and "MZPNX5XEM9N5" in ft and "9W5N7" in ft, failures)
    check("footer-508-line", "This site is built to meet Section 508 / WCAG 2.1 AA." in ft, failures)
    check("footer-no-email", EMAIL not in ft, failures)
    # Outbound links live in the footer, in How to contact SEWP, and in the Contract information card (the holder page on sewp.nasa.gov).
    outside = [n for n in root.walk() if n.tag == "a" and n.attrs.get("href", "").startswith("http")
               and not n.has_ancestor(lambda p: p.tag == "footer" or p.attrs.get("id") in ("contacts", "contract-facts"))]
    check("outbound-links-only-in-footer-contacts-and-facts (%d)" % len(outside), not outside, failures)
    check("outbound-links-only-to-allowed-hosts", all(re.sub(r"^https?://([^/]+).*$", r"\1", n.attrs["href"]).lower() in ALLOWED_HOSTS
          for n in root.walk() if n.tag == "a" and n.attrs.get("href", "").startswith("http")), failures)
    check("outbound-links-noopener", all(n.attrs.get("rel", "") == "noopener" for n in root.walk()
          if n.tag == "a" and n.attrs.get("href", "").startswith("https://")), failures)

    # 14. Static, honest, accessible: no script, no form, no handlers, orange never text, fixed facts present once.
    check("no-script-on-page", re.search(r"<script\b", html, re.I) is None, failures)
    check("no-form-or-controls", not find(root, lambda n: n.tag in ("form", "input", "textarea", "select", "button")), failures)
    check("no-on-handlers", not any(k.startswith("on") for n in root.walk() for k in n.attrs), failures)
    check("no-javascript-urls", "javascript:" not in html.lower(), failures)
    bad_css = [p + ":" + v for p, v in css_color_decls(css) if p in ("color", "-webkit-text-fill-color") and ORANGE.search(v)]
    check("orange-never-text-color-in-css (%s)" % "; ".join(bad_css), not bad_css, failures)
    check("orange-defined-in-css", ORANGE.search(css) is not None, failures)
    for fact in ("9W5N7", "MZPNX5XEM9N5", "SEWP VI runs November 1, 2026 to October 31, 2036.", "80TECH26D0796",
                 "This site is built to meet Section 508 / WCAG 2.1 AA."):
        check("fact-on-live: " + fact[:40], fact in page_text, failures)
    title = find(root, lambda n: n.tag == "title")
    metas = [n.attrs.get("content", "") for n in root.walk() if n.tag == "meta" and n.attrs.get("name") == "description"]
    check("title-is-16-cyber", bool(title) and " ".join(title[0].all_text().split()) == "16 Cyber", failures)
    check("meta-description-present", bool(metas) and len(metas[0]) > 20, failures)

    if failures:
        print("FAIL (%d):" % len(failures))
        for f in failures:
            print("  - " + f)
        sys.exit(1)
    print("PASS: all v3 gate checks passed")


if __name__ == "__main__":
    main()
