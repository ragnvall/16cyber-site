# What's owed from Joel before the site can say more

The site only states facts we already have in writing. Every other fact is a
variable: it sits in `index.html` with `data-var="<id>"` and the `hidden`
attribute, so the live page leaves it out, and the preview
(`tools/make-preview.py`) shows it as a purple [bracketed] chip. This is the
full list, 27 in all, taken from the design book's "All variables" table, so
Robert can ask Joel for them in one pass.

"NASA holder rule" marks the 6 that NASA's SEWP VI holder requirements call
for; "company" is a fact only 16 Cyber can state; "optional" can stay empty at
launch. Screen numbers are the design book's: 1 Home top, 2 How to buy,
3 Contract facts card, 4 What we supply, 5 Contact, 6 Quote form, 7 Ordering
guide, 8 About us page, 9 Capability statement, 10 Footer, D the book's
variable groups.

## The 27 variables

| id | Variable | Where it appears | Format or example | Required by |
|---|---|---|---|---|
| **Contract** | | | | |
| `contract_number` | Contract number | 1, 3, 7, 8, 9, 10, D | As printed on the NASA SEWP VI award record | NASA holder rule |
| `award_date` | Award date | D (on this site: under the contract number on card 3) | Month day, year, from the award record | optional |
| `period_of_performance` | Period of performance | 3, 7, D | Start and end dates of our contract, e.g. November 1, 2026 to October 31, 2036 | NASA holder rule |
| **Contacts** | | | | |
| `pm_name` | Program Manager name | 3, 5, 7, 8, 9 | Full name | NASA holder rule |
| `dpm_name` | Deputy PM name | 3, 5, 7, 8 | Full name | NASA holder rule |
| `sewp_phone_number` | SEWP phone number | 5, 6, 7, 9, 10 | (xxx) xxx-xxxx | company |
| `inbox_owner` | Inbox owner | 6 | Who reads sewp@16cyber.com first | company |
| **Commercial terms** | | | | |
| `surcharge_pct` | Surcharge % | 3, 7 | 0.34% is NASA's published rate; confirm before launch | company |
| `quote_reply_time` | Quote reply time | 2, 5, 6 | e.g. 2 business days | company |
| **Company facts** | | | | |
| `naics_codes` | NAICS codes | 3, 9, 10 | e.g. 541519 (primary), 423430; must match SAM.gov | company |
| `office_address` | Office address | 10 | Street, suite, city, state ZIP (the registered business address) | company |
| `small_business_status` | Small-business status | 3, 9 | e.g. Small business, per SBA record | company |
| `certifications` | Certifications | 3, 9 | e.g. SDVOSB, 8(a), HUBZone, or none | company |
| `jv_member_names` | JV member names (confirm) | 8 | Inode Ink and StorageHawk as registered | company |
| **Products** | | | | |
| `products_hardware` | Products sold: Hardware | 4 | Short list; items must be in SEWP's product database | company |
| `products_software` | Products sold: Software | 4 | Short list; items must be in SEWP's product database | company |
| `products_cloud` | Products sold: Cloud | 4 | Short list; items must be in SEWP's product database | company |
| `products_cybersecurity` | Products sold: Cybersecurity | 4 | Short list; items must be in SEWP's product database | company |
| `brands_confirmed` | Brands confirmed | 4 | Brand names, only after each confirms 16 Cyber to SEWP as an authorized reseller | optional |
| `capabilities_a1_a6` | Capabilities A.1 to A.6 (confirm) | 4, 9 | Yes or no on each: cybersecurity, cloud, systems integration, managed IT, hardware and software, training | company |
| `past_performance` | Past performance | 9 | Real orders only, with customer permission, once they exist | optional |
| **Documents** | | | | |
| `ordering_guide_pdf` | Ordering guide PDF | 1, 3, 7 | The PDF itself, or sign-off on the screen 7 layout | NASA holder rule |
| `guide_version_date` | Version date | 7 | Month year, printed on the ordering guide cover | company |
| `support_policy_text` | Support policy text | 5, 7 | Installation, warranty and support policy, a few paragraphs (the policy text SOW A.5.1(3b) asks every holder to post) | NASA holder rule |
| `capability_statement_design` | Capability statement PDF design | 9 | Designed PDF, or sign-off on the screen 9 layout | optional |
| **Copy** | | | | |
| `about_us_text` | About us text | 8 | One or two sentences | company |
| `differentiators` | Differentiators | 9 | Three to five short points | company |

`small_business_status`, `certifications` and `surcharge_pct` are not on the home page until the capability statement and ordering guide exist (owner, 10-12); the home page carries the other 24.

Screens 7, 8 and 9 are not built yet. Their variables still sit in
`index.html` (hidden), in the footer's document links, so `index.html` stays
the one place every variable lives.

One more marker that is not one of the 27: `form_endpoint` sits on the quote
form's note ("This form is not connected yet. Until it is, email
sewp@16cyber.com."). It is shown on the live page on purpose, and comes down
once the form has somewhere to deliver.

## Carried over from the v1 list
- `period_of_performance` also answers an open v1 question:
  Confirm the contract is active and orderable from November 1, 2026,
  when SEWP VI ordering opens.
- `differentiators` is where the "Why 16 Cyber" content from his sample page
  would go, once he confirms it.
- `capability_statement_design` covers the capability statement document his
  sample page's "Request capability statement" button points to.

## Content that needs Joel's sign-off before it goes up
His sample page (`16Cyber.html`) lists a capabilities grid (cybersecurity,
cloud, systems integration, managed IT, hardware/software, training) and
calls SEWP VI "Best-in-Class." The plan marks these as marketing claims
that need his confirmation, so they were left off this round. If he
confirms the six capabilities are accurate, they can go on the site as a
new section (variable `capabilities_a1_a6` above).

## Note on hosting
This repo is private, with GitHub Pages ready but not turned on. Making it
public and turning on Pages is Robert's step, not something this build
does on its own. See README.md for the five DNS records Joel will need to
add at GoDaddy.
