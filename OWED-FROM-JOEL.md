# What's owed from Joel before the site can say more

The site only states facts we already have in writing. Every other fact is a
variable: it sits in `index.html` with `data-var="<id>"` and the `hidden`
attribute, so the live page leaves it out, and the preview
(`tools/make-preview.py`) shows it as a purple [bracketed] chip. This is the
full list, 22 in all, taken from the design book's "All variables" table, so
Robert can ask Joel for them in one pass. The home page carries 8 of them as
hidden slots; 3 are filled; the other 11 wait for pages not built yet.

"NASA holder rule" marks the ones NASA's SEWP VI holder requirements call
for; "company" is a fact only 16 Cyber can state; "optional" can stay empty at
launch. Screen numbers follow the home page's sections, in NASA's order:
1 Top, 2 About SEWP, 3 Fair opportunity, 4 How to contact SEWP,
5 Contract information, 6 Contacts, 7 Ordering guide, 8 Vendors.
"Later" means not on the home page: G the ordering guide document,
C the capability statement, U the about us page.

## The 22 variables

| id | Variable | Where it appears | Format or example | Required by |
|---|---|---|---|---|
| **Contract** | | | | |
| `contract_number` | Contract number | 1, 5, G, C | As printed on the NASA SEWP VI award record | NASA holder rule |
| `award_date` | Award date | Later: G | Month day, year, from the award record | optional |
| `period_of_performance` | Period of performance | 5, G | Start and end dates of our contract, e.g. November 1, 2026 to October 31, 2036 | NASA holder rule |
| `sewp_holder_page` | SEWP contract holder page | 5 | Link to 16 Cyber's page on sewp.nasa.gov, once NASA posts it | optional |
| **Contacts** | | | | |
| `pm_name` | Program Manager name | 6 | FILLED: Khai Huynh (source: Joel's email 10-13) | done |
| `dpm_name` | Deputy PM name | 6 | FILLED: Jessica Hagood (source: Joel's email 10-13) | done |
| `sewp_phone_number` | SEWP phone number | 6, G, C | (xxx) xxx-xxxx | company |
| **Commercial terms** | | | | |
| `surcharge_pct` | Surcharge % | 5, G | 0.34% is NASA's published rate; confirm before launch | company |
| **Company facts** | | | | |
| `naics_codes` | NAICS codes | Later: C | e.g. 541519 (primary), 423430; must match SAM.gov | company |
| `office_address` | Office address | Later: U | Street, suite, city, state ZIP (the registered business address) | company |
| `small_business_status` | Small-business status | Later: C | e.g. Small business, per SBA record | company |
| `certifications` | Certifications | Later: C | e.g. SDVOSB, 8(a), HUBZone, or none | company |
| `jv_member_names` | JV member names (confirm) | Later: U | Inode Ink and StorageHawk as registered | company |
| **Products** | | | | |
| `brands_confirmed` | Vendors confirmed | 8 | FILLED: 63 names from Daniel Furth's "SEWP Vendor List v1.xlsx" (source: Daniel's email 10-13), no authorization claim | done |
| `capabilities_a1_a6` | Capabilities A.1 to A.6 (confirm) | Later: C | Yes or no on each: cybersecurity, cloud, systems integration, managed IT, hardware and software, training | company |
| `past_performance` | Past performance | Later: C | Real orders only, with customer permission, once they exist | optional |
| **Documents** | | | | |
| `ordering_guide_pdf` | Ordering guide PDF | 7 | The PDF itself, or sign-off on its layout | NASA holder rule |
| `guide_version_date` | Version date | 7 | Month year, printed on the ordering guide cover | company |
| `support_policy_text` | Support policy text | 7 | Installation, warranty and support policy, a few paragraphs (the policy text SOW A.5.1(3b) asks every holder to post) | NASA holder rule |
| `capability_statement_design` | Capability statement PDF design | Later: C | Designed PDF, or sign-off on its layout | optional |
| **Copy** | | | | |
| `about_us_text` | About us text | Later: U | One or two sentences | company |
| `differentiators` | Differentiators | Later: C | Three to five short points | company |

The 11 "Later" variables are not in `index.html`; this table is where they
live until their pages are built.

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
that need his confirmation, so they are not on the site. If he confirms
the six capabilities are accurate, they can go on the capability statement
(variable `capabilities_a1_a6` above).
