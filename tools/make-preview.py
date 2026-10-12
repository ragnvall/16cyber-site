#!/usr/bin/env python3
"""Make the single-file preview of 16cyber.com.

    python3 tools/make-preview.py [--date YYYY-MM-DD] [--book-dir DIR]

Reads index.html and styles.css from the repo root, inlines the CSS, the
Barlow fonts, the logo and the favicons as data: URIs, turns every variable
(an element with data-var) ON by removing its hidden attribute, and styles
those elements as purple [bracketed] chips. Writes one self-contained file:

    dist-preview/16cyber-site-preview-v2-<date>.html

and copies it into the design book folder (default
~/company-two/.lavish/16cyber-book) when that folder exists.
index.html stays the one source of truth; nothing here changes the live page.
Standard library only.
"""
import argparse
import base64
import datetime
import mimetypes
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BOOK_DIR = os.path.expanduser("~/company-two/.lavish/16cyber-book")

BANNER = ("Preview, not the live site. Purple items in [brackets] are the facts still needed; "
          "the live page leaves them out until they are in writing.")

# Purple appears only here, never on the live page.
PREVIEW_CSS = """
/* ===== Preview only ===== */
:where([data-var]) { padding: 0 .35em; }
[data-var] {
  background: #EFE7FF !important;
  color: #3B1D8F !important;
  border: 1px solid #C9B8F5 !important;
  border-radius: 2px !important;
}
/* Text inside a chip takes the chip's purple, so it reads on the dark footer too. */
[data-var] * { color: inherit !important; }
.preview-banner {
  background: #eceef2;
  color: #2b3036;
  border-bottom: 1px solid #c9ced6;
  font-size: 14.5px;
  line-height: 1.45;
  padding: 10px 24px;
  text-align: center;
}
"""

MIME = {".woff2": "font/woff2", ".png": "image/png", ".ico": "image/x-icon",
        ".svg": "image/svg+xml", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def data_uri(rel_path):
    root = os.path.realpath(ROOT)
    path = os.path.realpath(os.path.join(ROOT, rel_path))
    if not path.startswith(root + os.sep) or not os.path.isfile(path):
        sys.exit("make-preview: missing local file %r" % rel_path)
    ext = os.path.splitext(path)[1].lower()
    mime = MIME.get(ext) or mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as fh:
        return "data:%s;base64,%s" % (mime, base64.b64encode(fh.read()).decode("ascii"))


def is_local(value):
    return value and not value.startswith(("#", "data:", "//")) and ":" not in value


def inline_css(css):
    def repl(m):
        url = m.group(2)
        return "url('%s')" % data_uri(url) if is_local(url) else m.group(0)
    return re.sub(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)", repl, css)


def show_variables(html):
    """Remove the hidden attribute from every start tag that carries data-var."""
    count = 0

    def repl(m):
        nonlocal count
        tag = m.group(0)
        if "data-var=" not in tag:
            return tag
        new = re.sub(r"\s+hidden(?:=(?:\"\"|\"hidden\"|''|'hidden'))?(?=[\s/>])", "", tag)
        if new != tag:
            count += 1
        return new
    out = re.sub(r"<[a-zA-Z][^<>]*>", repl, html)
    return out, count


def build(date):
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    css = open(os.path.join(ROOT, "styles.css"), encoding="utf-8").read()

    link = re.search(r"<link\s+rel=\"stylesheet\"\s+href=\"styles\.css\"\s*>", html)
    if not link:
        sys.exit("make-preview: index.html no longer links styles.css as expected")
    style = "<style>\n" + inline_css(css) + PREVIEW_CSS + "</style>"
    html = html[:link.start()] + style + html[link.end():]

    def attr_repl(m):
        value = m.group(2)
        return '%s="%s"' % (m.group(1), data_uri(value)) if is_local(value) else m.group(0)
    html = re.sub(r"\b(src|href)=\"([^\"]*)\"", attr_repl, html)

    html, shown = show_variables(html)
    if re.search(r"<[a-zA-Z][^<>]*data-var=[^<>]*\shidden[\s>/=]", html):
        sys.exit("make-preview: a variable is still hidden after the flip")

    body = re.search(r"<body[^>]*>", html)
    if not body:
        sys.exit("make-preview: no <body> tag")
    banner = '\n<aside class="preview-banner" aria-label="Preview note">%s</aside>\n' % BANNER
    html = html[:body.end()] + banner + html[body.end():]
    html = html.replace("<title>", "<title>Preview: ", 1)

    out_dir = os.path.join(ROOT, "dist-preview")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "16cyber-site-preview-v2-%s.html" % date)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out, shown, len(html.encode("utf-8"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--book-dir", default=DEFAULT_BOOK_DIR)
    args = ap.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        sys.exit("make-preview: --date must be YYYY-MM-DD")
    out, shown, size = build(args.date)
    print("wrote %s (%d variables shown, %.0f KB)" % (out, shown, size / 1024))
    if size > 1.5 * 1024 * 1024:
        sys.exit("make-preview: preview is over 1.5 MB")
    if os.path.isdir(args.book_dir):
        dest = os.path.join(args.book_dir, os.path.basename(out))
        shutil.copyfile(out, dest)
        print("copied to %s" % dest)
    else:
        print("book folder %s not found; copy skipped" % args.book_dir)


if __name__ == "__main__":
    main()
