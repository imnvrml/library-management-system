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

I used an AI coding assistant (Claude, by Anthropic, in the Claude Code tool) as a working partner during the
whole project. I directed the work step by step; the assistant produced drafts and ran commands, and nothing went
into the repository before I had approved that step.

**My decisions and work**
- I chose the topic (Library Management System) and the technology. The assistant proposed a command-line
  application; I decided on a web application with Flask and HTML pages instead.
- I split the project into the eight steps of the handout and approved or corrected each step before the next
  one started: requirements, models, test plan, implementation, test report, change request, review, reflection.
- I set and corrected the business rules. For example, I questioned the publication-year rule (1450 to today)
  during the requirements review, because it was ambiguous whether it meant the year of the work or of the edition,
  and changed it to "edition year, from 1800".
- I reviewed the requirements, diagrams and test plan before they were merged, and asked for explanations where a
  rule was unclear to me (for example why a title cannot be reserved while a copy is on the shelf).
- I chose and approved the change request CR-01 and the code-review fixes, and I carry out the manual usability
  test (TC-NFR-05) myself.

**What the assistant did**
- It drafted the text of the documents, the PlantUML diagrams, the Python code and the automated tests from the
  decisions above, and ran the tests, Git commands and pull requests on my computer.
- It proposed design options (for example the pure `EligibilityPolicy` for unit-testable decision rules), which
  I accepted after seeing the reason.

**How the AI output was checked**
- Every document is linked to the code by requirement and test case IDs; the traceability matrix and the test
  results are generated from real test runs (`scripts/trace.py`), not written by hand.
- Every pull request had to pass the full automated test suite in CI before it was merged.
- The checks found real mistakes in AI-written work — D-01, D-02, D-05 to D-08 and R-01 to R-03 — which are
  recorded in the defect log and the code review. This showed me that an assistant's output must be treated like
  any other untested code.

**What I learned**
The assistant made producing artefacts fast, but the engineering quality came from the process around it:
requirements with testable acceptance criteria, tests derived with systematic techniques, a written impact
analysis before a change, and a review checklist. I am responsible for the whole submission and can explain each
requirement, diagram, design decision and test.
