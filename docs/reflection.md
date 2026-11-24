# Reflection — Library Management System

| | |
|---|---|
| **Author** | Ramil İmanov (group M666İ5) |
| **Date** | 2026-11-25 |

## 1. Requirement problems discovered late, and what they cost

**The new-copy gap (D-03).** FR-04 said that a new copy "starts Available". Only when I drew the state machine of
*Copy* did I see that a new copy of a title with members waiting would go to the shelf and let anyone take it,
breaking the queue promise of FR-14. Because the gap was found during modelling, the cost was small: one new
acceptance criterion (FR-04 AC3), one transition in two state machines, one test case and requirements v1.1. Had I
found it after coding, the same fix would also have touched the catalogue service and its tests. The lesson is
that state machines are a cheap requirements-review tool: every transition has to come from somewhere.

**Decision rules that could not be unit-tested (D-04).** My first design hid the checkout, renewal and
reservation rules inside services that need a database. I only noticed this when I tried to write the decision
tables as unit tests. Extracting a pure `EligibilityPolicy` (models v1.1) cost an hour of diagram updates but
made 30 test cases true unit tests that run in milliseconds.

**Details the requirements did not settle.** Several small questions came up only while coding: does the
"total" in "2 of 3 available" include withdrawn copies (I decided no), are e-mail addresses case-sensitive (I
decided no and store them in lower case), and should a librarian *action* answer 200 or a redirect (TC-ACC-05 had
to be corrected). Each was cheap to decide, but each decision now lives only in the code and in this reflection
instead of in the requirements. A short "data and display rules" section in the requirements would have caught
them earlier.

**The change request (CR-01).** The grace period was easy to implement (two lines of code) because rule values
were kept in one `Rules` object and fines are stored per loan, so no data had to be migrated. The impact analysis
predicted five failing tests; four failed. The fifth test passed for the wrong reason (D-08) — it only checked
that a page showed "0.00 AZN". Without the written prediction I would not have looked at that test again.

## 2. Where the implementation deviated from the design, and why

| Deviation | Reason |
|---|---|
| `Clock` also has `now()` (diagram: only `today()`) | A reservation needs date *and* time to keep the queue order. |
| `checkout_refusal(member facts, copy status, held_for_member)` instead of `(member, copy, member_id)` | Keeps the policy free of database look-ups, so it stays a pure, unit-testable function. |
| Extra small result classes: `TitleSummary`, `ReservationView`, `OverdueLoan`, `DeskStats` | Pages need combined data (title + counts, reservation + position); returning named objects is clearer than tuples. |
| `MemberService.account_summary()` was not written; the account page asks the repositories and services directly | The page only lists rows that already exist as repository methods; a separate method would have duplicated them. In a larger system I would add it to keep the web layer thinner. |
| `Database` lives in `library/db.py`, not in the repositories package | It is shared by all layers for transactions, not a repository. |
| CSRF token check and `safe_next()` are not in any diagram | Security details that the design level did not show; added during implementation and the code review (R-02). |
| Dashboard statistics were first written as SQL in the web layer | A shortcut that broke the "SQL only in repositories" rule of the architecture; found in the code review and fixed (R-03). |

All other classes, methods and layers match the design class diagrams; the traceability matrix links every Must
requirement to its design element and code module.

## 3. What I would do differently

1. **Write the decision tables before the class diagram.** Most design changes came from the test design; doing
   it earlier would have avoided models v1.1.
2. **Add display and data rules to the requirements** (counts, case sensitivity, message wording) instead of
   deciding them in code.
3. **Run the manual usability walkthrough (NFR-05) as soon as the first page works**, not at the end; it is still
   open at the time of writing.
4. **Generate the traceability matrix from the first test**, as `scripts/trace.py` does now, instead of planning to
   write it by hand at the end.
5. **Keep the review checklist next to me while coding.** All three review findings (R-01…R-03) were known
   rules that I simply did not check while writing the code.

## 4. Use of AI tools

I used an AI assistant (Claude, by Anthropic, in the Claude Code tool) throughout the project. I describe its role
honestly here:

- **What the AI did:** it analysed the course handout, proposed the overall plan and the eight steps, and drafted
  the requirements, the PlantUML diagrams, the test plan, most of the Python code and tests, the scripts and the
  first versions of these documents. It also ran the tests, the Git commands and the GitHub pull requests on my
  computer.
- **What I did:** I chose the topic and the technology (Flask with HTML pages instead of the proposed command-line
  version), approved or changed every step before the next one started, set the business-rule values (for
  example I changed the publication-year limit from 1450 to 1800), decided which proposals to accept, and
  reviewed the results.
- **How I checked the AI's work:** nothing was accepted without running it. Every document is linked to the code
  by test case IDs, every pull request had to pass the automated tests in CI, and the traceability matrix is
  generated from real test results, not written by hand. Several mistakes made during the work (D-01, D-02, D-05
  to D-08, R-01 to R-03) were found by these checks and are recorded in the defect log and the code review.
- **What I learned from it:** the AI was fast at producing artefacts, but the engineering value came from the
  checks around it — tests derived from requirements, the impact prediction for CR-01 and the review
  checklist. I am responsible for every part of the submission and can explain each requirement, diagram and test.
