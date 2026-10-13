#!/usr/bin/env python3
"""Spec gates for v2 (design book screens 1-6 and 10, plus the preview).
Run from the repo root:
    python3 tests/v2-gates.py <index.html> <preview.html>
styles.css is read from the same folder as index.html.
Exits non-zero and prints each failing check if any assertion fails.
Standard library only.
"""
import os
import re
import sys
from html.parser import HTMLParser

# The 21 ids from the design book's "All variables" table (amendments 10-13: the four products_* ids left with the
# tiles; inbox_owner and quote_reply_time left with the quote form when the owner made the page fully static).
BOOK_IDS = [
    "contract_number", "award_date", "period_of_performance",
    "pm_name", "dpm_name", "sewp_phone_number",
    "surcharge_pct",
    "naics_codes", "office_address", "small_business_status", "certifications", "jv_member_names",
    "brands_confirmed", "capabilities_a1_a6", "past_performance",
    "ordering_guide_pdf", "guide_version_date", "support_policy_text", "capability_statement_design",
    "about_us_text", "differentiators",
]
ALWAYS_ON = set()  # form_endpoint left with the form (static cut, 10-13)
# Owner change 3 (10-12): these three wait for the capability statement and
# ordering guide; they stay in OWED-FROM-JOEL.md but leave the home page.
OFF_HOME = {"small_business_status", "certifications", "surcharge_pct"}
# FILLED (amendment 10-13): a variable whose fact arrived in writing drops data-var and hidden and shows
# the fact; the id stays in the book as a record. brands_confirmed: Daniel Furth's vendor list, email 10-13.
FILLED = {"brands_confirmed"}
HOME_IDS = [i for i in BOOK_IDS if i not in OFF_HOME and i not in FILLED]
FACT_ROWS = ["Contract number", "Category", "Period of performance", "CAGE code", "UEI",
             "Program Manager and Deputy", "Ordering guide"]
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
                 "storagehawk.com", "www.storagehawk.com", "inodeink.com", "www.inodeink.com"}  # member companies (NASA A.5.1 item 4, 10-13)
FOOTER_LINKS = {"https://www.sewp.nasa.gov/": "NASA SEWP", "https://www.storagehawk.com/": "StorageHawk", "https://inodeink.com/": "INODE Ink"}
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

    # 1. Every book variable is in index.html as data-var.
    ids = {n.attrs["data-var"] for n in vars_}
    check("book-has-21-ids", len(BOOK_IDS) == 21 and len(HOME_IDS) == 17, failures)
    # Amendment 10-13 (owner, Daniel Furth's advice): one vendor list, no four product tiles.
    check("no-products-ids (%s)" % ", ".join(sorted(i for i in ids if i.startswith("products_"))),
          not any(i.startswith("products_") for i in ids), failures)
    check("no-area-tiles", not find(root, lambda n: {"areas", "area"} & set(n.attrs.get("class", "").split())), failures)
    supply = find(root, lambda n: n.tag == "section" and n.attrs.get("id") == "what-we-supply")
    vendors = [n for n in supply[0].walk() if "brands-block" in n.attrs.get("class", "").split()] if supply else []
    check("one-vendor-list-in-what-we-supply (%d)" % len(vendors), len(vendors) == 1, failures)
    check("vendor-list-heading-is-Vendors",
          bool(vendors) and any(n.tag == "h3" and " ".join(n.all_text().split()) == "Vendors" for n in vendors[0].walk()), failures)
    # Filled 10-13: the list is a fact now, visible on live, no data-var, no hidden, no bracketed placeholder.
    check("vendor-list-is-filled-and-visible",
          bool(vendors) and "data-var" not in vendors[0].attrs and "hidden" not in vendors[0].attrs
          and not any("data-var" in n.attrs or "hidden" in n.attrs for n in vendors[0].walk()), failures)
    vendor_names = [" ".join(n.all_text().split()) for n in vendors[0].walk() if n.tag == "li"] if vendors else []
    check("vendor-list-has-names-no-brackets (%d)" % len(vendor_names),
          len(vendor_names) >= 1 and all(v and "[" not in v and "]" not in v for v in vendor_names), failures)
    check("vendor-list-names-unique", len(vendor_names) == len(set(v.lower() for v in vendor_names)), failures)
    check("vendor-list-no-authorized-claim", "authorized" not in " ".join(text_outside_vars(vendors[0]).split()).lower() if vendors else False, failures)
    check("no-brands-confirmed-variable-left", "brands_confirmed" not in ids, failures)
    supply_text = " ".join(text_outside_vars(supply[0]).split()).lower() if supply else ""
    check("supply-intro-names-four-areas-in-one-sentence",
          "hardware, software, cloud and cybersecurity products" in supply_text, failures)
    check("supply-no-separate-services-paragraph", "also services that come with a product" not in supply_text, failures)
    missing = [i for i in HOME_IDS if i not in ids]
    check("all-17-home-ids-present (missing: %s)" % ", ".join(missing), not missing, failures)
    unknown = sorted(ids - set(HOME_IDS) - ALWAYS_ON)
    check("no-unknown-data-var-ids (%s)" % ", ".join(unknown), not unknown, failures)

    # 2. Live page: every variable OFF (static cut 10-13: the form and its always-on note are gone).
    shown = [n.attrs["data-var"] for n in vars_ if n.attrs["data-var"] not in ALWAYS_ON and "hidden" not in n.attrs]
    check("every-variable-hidden-on-live (shown: %s)" % ", ".join(shown), not shown, failures)
    check("no-form-endpoint-variable", not [n for n in vars_ if n.attrs["data-var"] == "form_endpoint"], failures)
    check("no-form-note-text", FORM_NOTE not in html, failures)
    # The hidden attribute must win over any display rule (structural, not per-class).
    check("css-hidden-attribute-forced",
          re.search(r"\[hidden\]\s*\{[^}]*display\s*:\s*none\s*!important", css) is not None, failures)
    # Each variable shows its bracketed label (from the book), never a sample value.
    unbracketed = [n.attrs["data-var"] for n in vars_
                   if n.attrs["data-var"] not in ALWAYS_ON and not re.search(r"\[[^\]]+\]", n.all_text())]
    check("every-variable-carries-a-bracketed-label (%s)" % ", ".join(unbracketed), not unbracketed, failures)
    check("contract-number-label-verbatim", "[Contract number]" in html, failures)

    # 3. Preview: nothing hidden, chip style present, banner present.
    if not preview:
        failures.append("preview-file-missing")
    else:
        proot = parse(preview)
        pvars = find(proot, lambda n: "data-var" in n.attrs)
        check("preview-has-all-17-home-ids", all(i in {n.attrs["data-var"] for n in pvars} for i in HOME_IDS), failures)
        check("preview-has-no-off-home-ids", not ({n.attrs["data-var"] for n in pvars} & OFF_HOME), failures)
        still = [n.attrs["data-var"] for n in pvars if "hidden" in n.attrs]
        check("preview-no-variable-hidden (%s)" % ", ".join(still), not still, failures)
        check("preview-chip-style", all(s.lower() in preview.lower() for s in ("#EFE7FF", "#3B1D8F", "#C9B8F5")), failures)
        check("preview-banner", BANNER in " ".join(parse(preview).all_text().split()), failures)
        hosts = {h.lower() for h in re.findall(r"https?://([^/\s\"'<>)]+)", preview)}
        bad = sorted(hosts - ALLOWED_HOSTS)
        check("preview-no-outside-http (%s)" % ", ".join(bad), not bad, failures)
        check("preview-no-protocol-relative", re.search(r"(src|href)\s*=\s*[\"']//", preview) is None, failures)
        check("preview-css-inlined", re.search(r"<link[^>]+stylesheet", preview, re.I) is None and "<style" in preview, failures)
        nondata = [u for u in re.findall(r"url\(\s*['\"]?([^'\")]+)", preview) if not u.startswith("data:")]
        check("preview-every-url-is-data (%s)" % ", ".join(nondata[:3]), not nondata, failures)
        srcs = [n.attrs.get("src", "") for n in find(proot, lambda n: n.tag == "img")]
        check("preview-images-inlined", srcs and all(s.startswith("data:") for s in srcs), failures)
        icons = [n.attrs.get("href", "") for n in find(proot, lambda n: n.tag == "link" and "icon" in n.attrs.get("rel", ""))]
        check("preview-favicons-inlined", icons and all(h.startswith("data:") for h in icons), failures)
        check("preview-under-1.5MB", len(preview.encode("utf-8")) < 1.5 * 1024 * 1024, failures)
        check("preview-no-script", re.search(r"<script\b", preview, re.I) is None, failures)
        # Purple is a preview-only colour.
        check("purple-only-in-preview", not any(s in (html + css).upper() for s in ("#EFE7FF", "#3B1D8F", "#C9B8F5")), failures)

    # 4. No mailto anywhere; the address is text in the top, form and footer areas.
    for label, src in (("index", html), ("css", css), ("preview", preview)):
        check("no-mailto-in-" + label, "mailto:" not in src.lower(), failures)
    hero = find(root, lambda n: n.attrs.get("id") == "top")
    header = find(root, lambda n: n.tag == "header")
    top_text = "".join(n.all_text() for n in header + hero)
    check("email-in-header-area", EMAIL in top_text, failures)
    # Owner change 6 (10-12): the ordering guide appears once, not in the hero;
    # it stays on the contract facts card and in the footer.
    hero_vars = [n.attrs.get("data-var") for h in hero for n in h.walk() if "data-var" in n.attrs]
    check("no-ordering-guide-in-hero", "ordering_guide_pdf" not in hero_vars
          and "ordering guide" not in " ".join(h.all_text() for h in hero).lower(), failures)
    check("no-button-in-hero", not [n for h in hero for n in h.walk()
                                    if "btn" in n.attrs.get("class", "").split() or n.tag == "button"], failures)
    og_places = {("facts" if n.has_ancestor(lambda p: "facts" in p.attrs.get("class", "").split()) else
                  "footer" if n.has_ancestor(lambda p: p.tag == "footer") else "other")
                 for n in vars_ if n.attrs["data-var"] == "ordering_guide_pdf"}
    check("ordering-guide-only-on-card-and-footer (%s)" % sorted(og_places), og_places == {"facts", "footer"}, failures)
    # Static cut (owner via Joel, 10-13): no quote section, no form, nothing interactive.
    check("no-quote-section", not find(root, lambda n: n.attrs.get("id") == "quote"), failures)
    howto = find(root, lambda n: n.attrs.get("id") == "how-to-buy")
    howto_text = " ".join(text_outside_vars(howto[0]).split()).lower() if howto else ""
    check("problem-order-contact-line-in-how-to-buy",
          "problem with an order" in howto_text and EMAIL in howto_text, failures)
    footer = find(root, lambda n: n.tag == "footer")
    check("email-in-footer", footer and EMAIL in text_outside_vars(footer[0]), failures)
    # NASA A.5.1 item 4 (10-13): links to the member companies' home pages and the SEWP home page, in the footer, visible, plain text labels.
    flinks = {n.attrs.get("href"): " ".join(n.all_text().split()) for f in footer for n in f.walk()
              if n.tag == "a" and n.attrs.get("href", "").startswith("https://") and "hidden" not in n.attrs
              and not n.has_ancestor(lambda p: "hidden" in p.attrs)}
    check("footer-links-to-sewp-and-members (%s)" % sorted(set(FOOTER_LINKS) - set(flinks)),
          all(h in flinks and flinks[h] == t for h, t in FOOTER_LINKS.items()), failures)
    check("footer-links-open-safely", all(n.attrs.get("rel", "") == "noopener" for f in footer for n in f.walk()
          if n.tag == "a" and n.attrs.get("href", "").startswith("https://")), failures)
    check("no-outside-links-elsewhere", not [n for n in root.walk() if n.tag == "a" and n.attrs.get("href", "").startswith("http")
          and not n.has_ancestor(lambda p: p.tag == "footer")], failures)

    # 5. The 0.34% fee only inside a variable.
    check("no-0.34-outside-variable", "0.34" not in text_outside_vars(root), failures)
    check("no-0.34-in-attributes", "0.34" not in "".join(
        v or "" for n in root.walk() for k, v in n.attrs.items()), failures)

    # 6. Orange never for text: not in any colour-of-text declaration, in CSS or inline styles.
    text_props = {"color", "-webkit-text-fill-color", "text-decoration-color", "caret-color", "-webkit-text-stroke-color"}
    bad_css = [p + ":" + v for p, v in css_color_decls(css) if p in text_props and ORANGE.search(v)]
    check("orange-never-text-color-in-css (%s)" % "; ".join(bad_css), not bad_css, failures)
    inline_bad = [s for s in re.findall(r"style=\"([^\"]*)\"", html)
                  if any(p in text_props and ORANGE.search(v) for p, v in css_color_decls("{" + s + "}"))]
    check("orange-never-text-color-inline", not inline_bad, failures)
    svg_text_orange = [n for n in root.walk() if n.tag in ("text", "tspan") and ORANGE.search(n.attrs.get("fill", ""))]
    check("orange-never-svg-text", not svg_text_orange, failures)
    check("orange-defined-in-css", ORANGE.search(css) is not None, failures)

    # 7. Contract clause A.1.13 verbatim.
    flat = " ".join(root.all_text().split())
    check("a113-sentence-1-verbatim", CLAUSE_1 in flat and CLAUSE_1 in html, failures)
    check("a113-sentence-2-verbatim", CLAUSE_2 in flat and CLAUSE_2 in html, failures)

    # 8. Heading outline: one h1, each section exactly one h2, no skipped levels.
    h1s = find(root, lambda n: n.tag == "h1")
    check("exactly-one-h1", len(h1s) == 1, failures)
    sections = find(root, lambda n: n.tag == "section")
    # Book screens 1, 2, 3, 4 and 6 in the drawn order. Screen 5 (Contact) was
    # removed by the owner on 10-12: the footer already carries the contacts.
    check("sections-in-order (%s)" % [s.attrs.get("id") for s in sections],
          [s.attrs.get("id") for s in sections] == ["top", "how-to-buy", "contract-facts", "what-we-supply"],
          failures)
    for s in sections:
        h2 = [n for n in s.walk() if n.tag == "h2"]
        h1 = [n for n in s.walk() if n.tag == "h1"]
        check("section-%s-one-h2-or-the-h1" % s.attrs.get("id", "?"),
              (len(h2) == 1 and not h1) or (len(h1) == 1 and not h2), failures)
        check("section-%s-labelled" % s.attrs.get("id", "?"), "aria-labelledby" in s.attrs, failures)
    levels = [int(n.tag[1]) for n in root.walk() if re.fullmatch(r"h[1-6]", n.tag)]
    skips = [b for a, b in zip(levels, levels[1:]) if b > a + 1]
    check("no-heading-level-skips", levels[:1] == [1] and not skips, failures)

    # 9. No JavaScript at all (static cut 10-13 restores plan decision 1), no event handlers.
    check("no-script-on-page", re.search(r"<script\b", html, re.I) is None, failures)
    check("no-header-hidden-css", "header--hidden" not in css, failures)
    quote_btns = [n for n in root.walk() if " ".join(n.all_text().split()) == "Get a quote"
                  and not any(" ".join(c.all_text().split()) == "Get a quote" for c in n.children)]
    check("no-get-a-quote-button (%d)" % len(quote_btns), len(quote_btns) == 0, failures)
    check("no-on-handlers", not any(k.startswith("on") for n in root.walk() for k in n.attrs), failures)
    check("no-javascript-urls", "javascript:" not in html.lower(), failures)

    # 10. Every same-page anchor resolves; nav and quote button go to real sections.
    ids_on_page = {n.attrs["id"] for n in root.walk() if "id" in n.attrs}
    anchors = [n.attrs["href"][1:] for n in root.walk() if n.tag == "a" and n.attrs.get("href", "").startswith("#")]
    dangling = sorted({a for a in anchors if a not in ids_on_page})
    check("anchors-resolve (%s)" % ", ".join(dangling), not dangling, failures)
    for target in ("how-to-buy", "contract-facts", "what-we-supply"):
        check("nav-target-" + target, target in anchors and target in ids_on_page, failures)
    # Every in-page jump target clears the sticky header (skip link included).
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
    nav = find(root, lambda n: n.tag == "nav")
    check("nav-three-links", nav and [n.attrs.get("href") for n in nav[0].walk() if n.tag == "a"]
          == ["#how-to-buy", "#contract-facts", "#what-we-supply"], failures)
    check("no-contact-section", "contact" not in ids_on_page, failures)
    check("no-quote-link-anywhere", not [n for n in root.walk() if n.tag == "a" and n.attrs.get("href") == "#quote"], failures)

    # 11. No form, no form styling left behind (static cut 10-13).
    forms = find(root, lambda n: n.tag == "form")
    check("no-form", len(forms) == 0, failures)
    check("no-form-controls", not find(root, lambda n: n.tag in ("input", "textarea", "select", "button")), failures)
    dead = [sel for sel in (".quote-card", ".quote-sub", ".field", ".form-foot", ".form-note", ".quote-alt", ".hp")
            if re.search(re.escape(sel) + r"(?![\w-])", re.sub(r"/\*.*?\*/", "", css, flags=re.S))]
    check("no-form-css-left (%s)" % ", ".join(dead), not dead, failures)
    check("success-line-not-built", "Sent. We reply within" not in html, failures)

    # 11b. Contract facts card: exactly these rows, in this order.
    facts_dl = find(root, lambda n: n.tag == "dl" and "facts" in n.attrs.get("class", "").split())
    rows = [" ".join(d.all_text().split()) for dl in facts_dl for d in dl.walk() if d.tag == "dt"]
    check("fact-rows-exact (%s)" % rows, rows == FACT_ROWS, failures)
    owed_path = os.path.join(os.path.dirname(os.path.abspath(index_path)), "OWED-FROM-JOEL.md")
    owed = open(owed_path, encoding="utf-8").read() if os.path.isfile(owed_path) else ""
    owed_missing = [i for i in BOOK_IDS if "`%s`" % i not in owed]
    check("owed-lists-all-27 (missing: %s)" % ", ".join(owed_missing), owed and not owed_missing, failures)
    title = find(root, lambda n: n.tag == "title")
    check("title-is-16-cyber", title and title[0].all_text().strip() == "16 Cyber", failures)
    metas = [n.attrs.get("content", "") for n in root.walk() if n.tag == "meta" and n.attrs.get("name") == "description"]
    check("meta-description", metas == ["16 Cyber supplies IT, cloud and cybersecurity products to federal agencies."], failures)
    check("no-holder-phrase-in-head", re.search(r"Category A contract holder", " ".join(metas) + (title[0].all_text() if title else "")) is None, failures)

    # 12. Fixed facts and copy.
    for fact in ("16 Cyber is a NASA SEWP VI contract holder.",
                 "We supply IT, cloud and cybersecurity products to federal agencies.",
                 "9W5N7", "MZPNX5XEM9N5",
                 "Ordering on SEWP VI opens November 1, 2026.",
                 "SEWP VI runs November 1, 2026 to October 31, 2036.",
                 "This site is built to meet Section 508 / WCAG 2.1 AA."):
        check("fact-on-live: " + fact[:40], fact in " ".join(text_outside_vars(root).split()), failures)
    strip = find(root, lambda n: "id-strip" in n.attrs.get("class", "").split())
    # Owner change 2 (10-12): the strip keeps its band and orange rule but holds no text,
    # and the "Category A contract holder" line is gone from the page body.
    check("strip-present-and-empty", strip and strip[0].has_ancestor(lambda p: p.tag == "header")
          and not strip[0].all_text().strip(), failures)
    body_text = " ".join(" ".join(n.all_text() for n in find(root, lambda n: n.tag == "body")).split())
    check("no-category-a-contract-holder-line",
          re.search(r"NASA SEWP VI,? Category A contract holder", body_text) is None, failures)
    check("footer-keeps-sewp-identifier", footer and "NASA SEWP VI, Category A" in text_outside_vars(footer[0]), failures)

    # 13. House rules: no em dashes, no brand logos, 1080 column, no external requests.
    base = os.path.dirname(os.path.abspath(index_path))
    docs = []
    for n in ("README.md", "OWED-FROM-JOEL.md"):
        doc_path = os.path.join(base, n)
        check("doc-present-" + n, os.path.isfile(doc_path), failures)
        if os.path.isfile(doc_path):
            docs.append((n, open(doc_path, encoding="utf-8").read()))
    for label, src in [("index", html), ("css", css), ("preview", preview)] + docs:
        check("no-em-dash-in-" + label, "\u2014" not in src and "&mdash;" not in src, failures)
    imgs = [n.attrs.get("src", "") for n in root.walk() if n.tag == "img"]
    check("only-our-logo-images", imgs and all("logo-16cyber" in s for s in imgs), failures)
    check("content-column-1080", re.search(r"--max\s*:\s*1080px", css) is not None, failures)
    check("no-external-requests-on-live", re.search(r"src\s*=\s*\"(https?:)?//", html) is None
          and re.search(r"<link[^>]+href\s*=\s*\"(https?:)?//", html) is None
          and "@import" not in css and re.search(r"url\(\s*['\"]?(https?:)?//", css) is None, failures)
    out_hosts = {h.lower() for h in re.findall(r"href=\"https?://([^/\"]+)", html)} - ALLOWED_HOSTS
    check("external-links-only-to-nasa-or-us (%s)" % ", ".join(sorted(out_hosts)), not out_hosts, failures)

    if failures:
        print("FAIL (%d):" % len(failures))
        for f_ in failures:
            print("  -", f_)
        return 1
    print("PASS: all v2 gate checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
