# 16cyber.com

One-page informational site for 16 Cyber (NASA SEWP VI). Plain HTML and CSS, no build step. No JavaScript at all: the page is fully static (owner decision 2026-10-13).

Plan: `~/company-two/plans/PLAN-16cyber-001-site.md`

Still missing before the page says more: see `OWED-FROM-JOEL.md`.

## Structure

The page mirrors NASA's example website for SEWP VI contract holders, section
for section and in NASA's order, in 16 Cyber's look: 1 Top (the holder line
and the contract number), 2 About SEWP, 3 Fair opportunity (the A.1.13
clause), 4 How to contact SEWP (NASA's help desk), 5 Contract information,
6 Contacts (the one place the email appears), 7 Ordering guide, 8 Vendors.
The footer carries the links to NASA SEWP and the two member companies, the
contract identifiers and the Section 508 line.

## Variables and the preview

A fact that is not in writing yet sits in `index.html` as an element with
`data-var="<id>"` and the `hidden` attribute, holding its [bracketed label],
for example `<dd data-var="contract_number" hidden>[Contract number]</dd>`.
The live page leaves every such element out. To fill one, put the real value
in place of the label and delete `hidden`. The ids are listed in
`OWED-FROM-JOEL.md`.

To see the page with every variable shown as a purple chip:

    python3 tools/make-preview.py

It writes one self-contained file, `dist-preview/16cyber-site-preview-v2-<date>.html`
(CSS, fonts and images included), and copies it into the design
book folder when that folder exists. `dist-preview/` is not committed.
Check both with `python3 tests/v3-gates.py index.html <preview file>`.

## Going live

This repo is private today. Going live is two steps, both Robert's to take
(never automated by a build):

1. **Make the repo public, then turn on GitHub Pages.**
   In the repo on GitHub: Settings > General > Danger Zone > Change
   visibility > make public. Then Settings > Pages > Build and deployment >
   Source: "Deploy from a branch" > Branch: `main`, folder `/ (root)` >
   Save. GitHub serves the site at `https://<org-or-user>.github.io/16cyber-site/`
   first, then at `16cyber.com` once the DNS below resolves and the custom
   domain is saved in the same Pages settings screen (the `CNAME` file in
   this repo already names `16cyber.com`, so Pages will offer it).

2. **Joel adds five DNS records at GoDaddy, in 16cyber.com's zone.**
   Nothing else in the zone changes, so email on the domain keeps working.

   Four `A` records for the bare domain (`16cyber.com`), each pointing to
   one of GitHub Pages' IP addresses:

   | Type | Host | Value |
   |---|---|---|
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |

   One `CNAME` record for the `www` subdomain, pointing at the GitHub Pages
   hostname for this repo:

   | Type | Host | Value |
   |---|---|---|
   | CNAME | www | `<org-or-user>.github.io` |

   HTTPS is automatic once GitHub verifies the domain; this can take up to
   24 hours after the DNS records are saved.
