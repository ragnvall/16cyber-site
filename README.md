# 16cyber.com

One-page informational site for 16 Cyber (NASA SEWP VI). Plain HTML and CSS, no build step, no JavaScript.

Plan: `~/company-two/plans/PLAN-16cyber-001-site.md`

Still missing before the page says more: see `OWED-FROM-JOEL.md`.

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
