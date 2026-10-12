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

# The 27 ids from the design book's "All variables" table.
BOOK_IDS = [
    "contract_number", "award_date", "period_of_performance",
    "pm_name", "dpm_name", "sewp_phone_number", "inbox_owner",
    "surcharge_pct", "quote_reply_time",
    "naics_codes", "office_address", "small_business_status", "certifications", "jv_member_names",
    "products_hardware", "products_software", "products_cloud", "products_cybersecurity",
    "brands_confirmed", "capabilities_a1_a6", "past_performance",
    "ordering_guide_pdf", "guide_version_date", "support_policy_text", "capability_statement_design",
    "about_us_text", "differentiators",
]
ALWAYS_ON = {"form_endpoint"}
# Owner change 3 (10-12): these three wait for the capability statement and
# ordering guide; they stay in OWED-FROM-JOEL.md but leave the home page.
OFF_HOME = {"small_business_status", "certifications", "surcharge_pct"}
HOME_IDS = [i for i in BOOK_IDS if i not in OFF_HOME]
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
ALLOWED_HOSTS = {"sewp.nasa.gov", "www.sewp.nasa.gov", "16cyber.com", "www.16cyber.com"}
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
    check("book-has-27-ids", len(BOOK_IDS) == 27 and len(HOME_IDS) == 24, failures)
    missing = [i for i in HOME_IDS if i not in ids]
    check("all-24-home-ids-present (missing: %s)" % ", ".join(missing), not missing, failures)
    unknown = sorted(ids - set(HOME_IDS) - ALWAYS_ON)
    check("no-unknown-data-var-ids (%s)" % ", ".join(unknown), not unknown, failures)

    # 2. Live page: every variable OFF except form_endpoint, which is ON.
    shown = [n.attrs["data-var"] for n in vars_ if n.attrs["data-var"] not in ALWAYS_ON and "hidden" not in n.attrs]
    check("every-variable-hidden-on-live (shown: %s)" % ", ".join(shown), not shown, failures)
    fe = [n for n in vars_ if n.attrs["data-var"] == "form_endpoint"]
    check("form-endpoint-note-present-and-visible",
          fe and all("hidden" not in n.attrs for n in fe)
          and any(" ".join(n.all_text().split()) == FORM_NOTE for n in fe), failures)
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
        check("preview-has-all-24-home-ids", all(i in {n.attrs["data-var"] for n in pvars} for i in HOME_IDS), failures)
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
        check("preview-no-script", "<script" not in preview.lower(), failures)
        # Purple is a preview-only colour.
        check("purple-only-in-preview", not any(s in (html + css).upper() for s in ("#EFE7FF", "#3B1D8F", "#C9B8F5")), failures)

    # 4. No mailto anywhere; the address is text in the top, form and footer areas.
    for label, src in (("index", html), ("css", css), ("preview", preview)):
        check("no-mailto-in-" + label, "mailto:" not in src.lower(), failures)
    hero = find(root, lambda n: n.attrs.get("id") == "top")
    header = find(root, lambda n: n.tag == "header")
    top_text = "".join(n.all_text() for n in header + hero)
    check("email-in-header-area", EMAIL in top_text, failures)
    quote = find(root, lambda n: n.attrs.get("id") == "quote")
    quote_live = "".join(text_outside_vars(n) for n in quote) + "".join(
        n.all_text() for q in quote for n in q.walk() if n.attrs.get("data-var") in ALWAYS_ON)
    check("email-in-form-area", quote and EMAIL in quote_live, failures)
    footer = find(root, lambda n: n.tag == "footer")
    check("email-in-footer", footer and EMAIL in text_outside_vars(footer[0]), failures)

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
          [s.attrs.get("id") for s in sections] == ["top", "how-to-buy", "contract-facts", "what-we-supply", "quote"],
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

    # 9. No JavaScript, no event handlers.
    check("no-script-tag", "<script" not in html.lower(), failures)
    check("no-on-handlers", not any(k.startswith("on") for n in root.walk() for k in n.attrs), failures)
    check("no-javascript-urls", "javascript:" not in html.lower(), failures)

    # 10. Every same-page anchor resolves; nav and quote button go to real sections.
    ids_on_page = {n.attrs["id"] for n in root.walk() if "id" in n.attrs}
    anchors = [n.attrs["href"][1:] for n in root.walk() if n.tag == "a" and n.attrs.get("href", "").startswith("#")]
    dangling = sorted({a for a in anchors if a not in ids_on_page})
    check("anchors-resolve (%s)" % ", ".join(dangling), not dangling, failures)
    for target in ("how-to-buy", "contract-facts", "what-we-supply", "quote"):
        check("nav-target-" + target, target in anchors and target in ids_on_page, failures)
    nav = find(root, lambda n: n.tag == "nav")
    check("nav-three-links", nav and [n.attrs.get("href") for n in nav[0].walk() if n.tag == "a"]
          == ["#how-to-buy", "#contract-facts", "#what-we-supply"], failures)
    check("no-contact-section", "contact" not in ids_on_page, failures)
    hdr_quote = [n for h in header for n in h.walk() if n.tag == "a" and n.attrs.get("href") == "#quote"
                 and not n.has_ancestor(lambda p: p.tag == "nav")]
    check("header-get-a-quote-outside-nav", bool(hdr_quote), failures)

    # 11. The quote form.
    forms = find(root, lambda n: n.tag == "form")
    check("one-form", len(forms) == 1, failures)
    if forms:
        f = forms[0]
        check("form-action-hash-post", f.attrs.get("action") == "#" and f.attrs.get("method", "").lower() == "post", failures)
        fields = [n for n in f.walk() if n.tag in ("input", "textarea", "select") and n.attrs.get("type") not in ("submit", "hidden")]
        labels = {n.attrs.get("for") for n in f.walk() if n.tag == "label"}
        hp = [n for n in fields if n.attrs.get("name") == "company_website"]
        check("honeypot-present", len(hp) == 1 and hp[0].attrs.get("tabindex") == "-1"
              and hp[0].has_ancestor(lambda p: p.attrs.get("aria-hidden") == "true"), failures)
        real = [n for n in fields if n.attrs.get("name") != "company_website"]
        check("five-real-fields", len(real) == 5, failures)
        unlabeled = [n.attrs.get("name") for n in real if n.attrs.get("id") not in labels]
        check("every-field-has-visible-label (%s)" % unlabeled, not unlabeled, failures)
        hp_ids = {n.attrs.get("id") for n in hp}

        def decls(style):
            """Effective value per property: !important beats any later plain value,
            the last !important wins among important ones, else the last wins."""
            out, important = {}, set()
            for k, v in css_color_decls("{" + style + "}"):
                v = v.lower()
                imp = re.search(r"!\s*important\s*$", v) is not None
                v = re.sub(r"\s*!\s*important\s*$", "", v).strip()
                if imp or k not in important:
                    out[k] = v
                    if imp:
                        important.add(k)
            return out

        def hides(d, allow_sr_only=False):
            if re.match(r"none\b", d.get("display", "")) or re.match(r"hidden\b", d.get("visibility", "")):
                return True
            sr_only = d.get("position", "").startswith("absolute") and (
                "clip" in d or "clip-path" in d or re.match(r"1px\b", d.get("width", "")))
            return bool(sr_only) and not allow_sr_only

        def concealed(n):
            cls = set(n.attrs.get("class", "").split())
            return ("hidden" in n.attrs or n.attrs.get("aria-hidden") == "true"
                    or cls & {"hp", "sr-only", "visually-hidden"}
                    or hides(decls(n.attrs.get("style", ""))))
        form_labels = [n for n in f.walk() if n.tag == "label"]
        unseen = [n.attrs.get("for") for n in form_labels if n.attrs.get("for") not in hp_ids
                  and (concealed(n) or n.has_ancestor(concealed))]
        check("every-label-visible-except-honeypot (%s)" % unseen, not unseen, failures)
        # The stylesheet must not hide a real label either (any rule naming label,
        # or a real label's id or class). Only the honeypot's own rule may.
        label_hooks = set()
        for n in form_labels:
            if n.attrs.get("for") not in hp_ids:
                label_hooks |= {"#" + n.attrs["id"].lower()} if n.attrs.get("id") else set()
                label_hooks |= {"." + c.lower() for c in n.attrs.get("class", "").split()}
        hp_marks = [h.lower() for h in hp_ids if h] + ["company_website", ".hp"]
        css_bad = []
        for sel_group, block in re.findall(r"([^{}]+)\{([^{}]*)\}", re.sub(r"/\*.*?\*/", "", css, flags=re.S)):
            for sel in sel_group.split(","):
                sel = " ".join(sel.lower().split())
                names_label = re.search(r"(^|[\s>+~(])label\b", sel) or any(
                    re.search(re.escape(h) + r"(?![\w-])", sel) for h in label_hooks)
                if names_label and not any(m in sel for m in hp_marks) and hides(decls(block)):
                    css_bad.append(sel)
        check("css-never-hides-a-real-label (%s)" % "; ".join(css_bad), not css_bad, failures)
        need = " ".join(n.all_text().strip() for n in f.walk() if n.tag == "label")
        for lab in ("Name", "Agency or company", "Work email", "Phone", "What you need, how many, and by when"):
            check("label-" + lab, lab in need, failures)
        check("one-textarea", len([n for n in real if n.tag == "textarea"]) == 1, failures)
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
