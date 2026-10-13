# Placement card: the static cut (2026-10-13)

**Question.** With the quote form, the "Get a quote" button and the script gone, where does the page say how to get a quote and who to call about a problem order (NASA A.5.1 items 3a and 3c)?

Owner's words (chat, 10-13, relaying Joel Salamone): "The website needs to be as basic and minimum as possible. No one will use it interactively. Totally static."
Owner, same conversation: the only dynamic thing is the quote form; the rest is what NASA asks for.

**Option A (default, chosen by the chair under the owner's words).** "How to buy" keeps its three steps (step 1 already says to email sewp@16cyber.com) and gains ONE short paragraph after the fair-opportunity callout:
"Problem with an order? Email sewp@16cyber.com or call [SEWP phone number]." The phone is the existing hidden `sewp_phone_number` variable (a span inside the sentence, hidden on live, chip in the preview); the email is plain text. The header keeps the logo and the three nav links; the "Get a quote" button goes. The quote section, the form, its note, its CSS and the inline script go. The footer is unchanged (email, phone, address, identifiers).
Surface: section `#how-to-buy`, end of the section. File scope: index.html, styles.css, OWED-FROM-JOEL.md. Advancement trigger: none; this is the final shape until Joel's facts arrive.

**Option B.** Put the problem-order line in the footer's contact column instead. Rejected: NASA groups it with "how to obtain a quote", and the footer is already dense on phones.

Owner may override in chat before the PR flips to ready.
