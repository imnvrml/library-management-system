# Test Plan and Test Report — Library Management System

| | |
|---|---|
| **Author** | Ramil İmanov (group M666İ5) |
| **Version** | 1.1 (plan + test report, 2026-11-25) |
| **Date** | 2026-11-15 |
| **Based on** | Requirements v1.1, Models v1.1 |

## 1. Purpose and scope

This document describes how the Library Management System is tested and lists every test case with the
requirement it verifies. Test cases are designed **before** the code (test-first), from the acceptance criteria
and business rules of the requirements, using the techniques in Section 3.

**In scope:** all Must requirements (FR-01 to FR-04, FR-06, FR-07, FR-09 to FR-15), the Should requirements
(FR-05, FR-08, FR-16 to FR-19) and the non-functional requirements NFR-01 to NFR-08.
**Out of scope:** the Could extensions FR-20 and FR-21 (not implemented), browser compatibility and visual
layout of the pages.

## 2. Test strategy

### 2.1 Test levels

| Level | Test object | How | Share |
|---|---|---|---|
| **Unit** | Pure logic without database or web: `FinePolicy`, `EligibilityPolicy`, ISBN validation, `Loan.is_overdue`, `Rules` | pytest, direct function calls | ~45 % |
| **Integration** | One service together with its repositories and a real SQLite database (in memory, new for each test) and a `FixedClock` | pytest fixtures build the service graph | ~35 % |
| **System** | The whole application through HTTP: login, role checks, forms, redirects, messages | Flask `test_client()` with a temporary database file | ~20 % |
| **Non-functional** | Performance (NFR-01), security (NFR-02, NFR-03), integrity (NFR-04), privacy (NFR-06), operability (NFR-08) | automated where possible; usability (NFR-05) as a manual walkthrough | — |

The pyramid shape (many unit tests, fewer system tests) keeps the suite fast (NFR-08: ≤ 30 s) while the
system tests prove that the layers work together.

### 2.2 Tools

| Tool | Purpose |
|---|---|
| pytest 8 | test runner, fixtures, parametrised tests |
| pytest-cov 7 | statement and branch coverage, HTML report |
| Flask test client | system tests without a real browser or server |
| `FixedClock` (test double) | sets "today" exactly, so date boundaries can be tested (A-10) |
| GitHub Actions | runs the whole suite on every push and pull request |
| `run_tests` script | runs the whole suite with one command locally |

### 2.3 Naming and traceability
Every automated test function carries the test case ID in its name, for example
`test_TC_CHK_03_loan_limit_reached`. The traceability matrix links requirement → test case ID → test function,
so a requirement without a test, or a test without a requirement, is visible.

### 2.4 Test data
- Fixed dates: unless stated otherwise, **today = 2026-12-01** (a Tuesday).
- Standard members: **Ann** (member, active), **Ben** (member, active), **Cem** (member, deactivated); standard librarian: **Lib**.
- Standard titles: *Dune* (ISBN 9780441172719), *Dune Messiah* (9780441172696), *Clean Code* (9780132350884).
- Copy codes `C-001`, `C-002`, …; money in qəpik (100 qəpik = 1.00 AZN).
- Each test builds its own data; no test depends on another test's data or order.

### 2.5 Entry criteria
- Requirements v1.1 and models v1.1 are approved.
- The test cases in Section 4 are reviewed and each one references a requirement.
- The code under test compiles (imports) and the test environment (Python 3.12, `requirements.txt`) installs without errors.

### 2.6 Exit criteria
- 100 % of test cases for **Must** requirements are executed and pass.
- ≥ 95 % of all automated test cases pass; every failure has a defect log entry.
- No open defect with severity **Critical** or **High**.
- Statement coverage of `library/services` ≥ 90 % (NFR-07).
- The manual usability walkthrough (TC-NFR-05) is done and its result recorded.

### 2.7 Defect management
Every defect found by a test, a review or manual use is recorded in the defect log (Section 6) with ID,
description, severity, how it was found, the fix and the commit.

| Severity | Meaning | Example |
|---|---|---|
| Critical | Data loss or a security hole | a member can see another member's account |
| High | A Must requirement does not work | checkout ignores the loan limit |
| Medium | A Should requirement does not work, or a wrong message | overdue list in wrong order |
| Low | Cosmetic | typo in a page title |

### 2.8 Test environment
Windows 11 and Ubuntu (GitHub Actions runner), Python 3.12, SQLite 3 (bundled with Python), packages from
`requirements.txt`. No network access is needed.

## 3. Test design

Five techniques are used. Each test case in Section 4 names the technique it comes from.

| Code | Technique | Used for |
|---|---|---|
| **EP** | Equivalence partitioning | input classes: ISBN, search text, credentials, roles |
| **BVA** | Boundary value analysis | every numeric or date limit in the business rules |
| **DT** | Decision table | checkout, renewal and reservation eligibility (several conditions together) |
| **ST** | State transition | life cycles of Copy and Reservation (models §3) |
| **UC** | Use-case-based | main and alternative flows of UC-05 to UC-08 (models §1.1) |

### 3.1 Equivalence partitions and boundary values

| Input (rule) | Valid partitions | Invalid partitions | Boundary values tested | Test cases |
|---|---|---|---|---|
| Days late at return (FR-12, BR-07, BR-15) | ≤ 2 → no fine (grace, CR-01); 3–50 → 20 qəpik × every day late; > 50 → capped 1000 | — | −1, 0, 1, 2, 3, 49, 50, 51 (+365 as a far value) | TC-FINE-01…09 |
| ISBN (BR-11) | 13 digits with valid check digit, with or without hyphens | wrong check digit; 12 or 14 digits; non-digit character; empty | 12, 13, 14 digits | TC-ISBN-01…07 |
| Publication year (BR-12) | 1800 … current year | < 1800; > current year | 1799, 1800, 2026, 2027 | TC-CAT-03…06 |
| Active loans before checkout (BR-02) | 0–4 | ≥ 5 | 4, 5 | TC-CHK-10, TC-CHK-03 |
| Balance before checkout (BR-05) | ≤ 500 qəpik | > 500 | 500, 501 | TC-CHK-11, TC-CHK-05 |
| Overdue (BR-06) | due date ≥ today | due date < today | due today, due yesterday | TC-CHK-16, TC-CHK-15, TC-REN-05, TC-REN-04 |
| Renewal count (BR-03) | 0–1 | ≥ 2 | 1, 2 | TC-REN-02, TC-REN-03 |
| Active reservations (BR-10) | 0–2 | ≥ 3 | 2, 3 | TC-RES-06, TC-RES-05 |
| Pickup deadline (BR-08) | today ≤ deadline → hold stays | today > deadline → expires | deadline day, deadline + 1 | TC-EXP-03, TC-EXP-01 |
| Password length (BR-13) | ≥ 8 | ≤ 7 | 7, 8 | TC-MEM-03, TC-MEM-04 |
| Payment amount (FR-18) | 1 … balance | ≤ 0; > balance | 0, 1, balance, balance + 1 | TC-PAY-01…05 |
| Search text (FR-06) | empty; matches title; matches author; matches ISBN | — (no invalid text) | — | TC-SRC-01…06 |
| Credentials (FR-01) | correct e-mail + password | unknown e-mail; wrong password; deactivated account | — | TC-AUTH-01…04 |

### 3.2 Decision tables

Conditions are checked in the order listed; the first failing condition gives the message (this order is part
of the design and is tested by TC-CHK-12). "–" means "does not matter".

**DT-1 Checkout eligibility (FR-09, `EligibilityPolicy.checkout_refusal`)**

| Condition / Rule | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 |
|---|---|---|---|---|---|---|---|---|---|
| C1 Member active | Y | N | Y | Y | Y | Y | Y | Y | Y |
| C2 Active loans < 5 | Y | – | N | Y | Y | Y | Y | Y | Y |
| C3 No overdue loan | Y | – | – | N | Y | Y | Y | Y | Y |
| C4 Balance ≤ 5.00 AZN | Y | – | – | – | N | Y | Y | Y | Y |
| C5 Copy state | Available | – | – | – | – | On loan | Withdrawn | On hold (other) | On hold (this member) |
| **Action** | lend | "Account is deactivated" | "Loan limit reached (5)" | "Member has overdue items" | "Outstanding fines exceed 5.00 AZN" | "Copy is not available" | "Copy is not available" | "Copy is held for another member" | lend + fulfil reservation |
| **Test case** | TC-CHK-01 | TC-CHK-02 | TC-CHK-03 | TC-CHK-04 | TC-CHK-05 | TC-CHK-06 | TC-CHK-07 | TC-CHK-08 | TC-CHK-09 |

**DT-2 Renewal eligibility (FR-11, `EligibilityPolicy.renew_refusal`)**

| Condition / Rule | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| C1 Renewal count < 2 | Y | N | Y | Y |
| C2 Loan not overdue | Y | – | N | Y |
| C3 No Waiting reservation by another member | Y | – | – | N |
| **Action** | renew (+14 days) | "Maximum renewals reached (2)" | "Overdue loans cannot be renewed" | "Title is reserved by another member" |
| **Test case** | TC-REN-01 | TC-REN-03 | TC-REN-04 | TC-REN-06 |

**DT-3 Reservation eligibility (FR-13, `EligibilityPolicy.reservation_refusal`)**

| Condition / Rule | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|
| C1 No Available copy | Y | N | Y | Y | Y |
| C2 Not already reserved by this member | Y | – | N | Y | Y |
| C3 Title not on loan to this member | Y | – | – | N | Y |
| C4 Active reservations < 3 | Y | – | – | – | N |
| **Action** | add Waiting reservation | "A copy is available — borrow it at the desk" | "You already reserved this title" | "You already have this title on loan" | "Reservation limit reached (3)" |
| **Test case** | TC-RES-01 | TC-RES-02 | TC-RES-03 | TC-RES-04 | TC-RES-05 |

### 3.3 State transition tables

**ST-1 Copy (models §3.1).** Rows are states, columns are events. Every valid transition (0-switch coverage)
and every invalid event in a reachable state has a test case.

| State \ Event | check out | return | withdraw | hold expires / cancelled |
|---|---|---|---|---|
| **Available** | → On loan (TC-CHK-13) | refused "Copy is not on loan" (TC-RET-03) | → Withdrawn (TC-CAT-12) | not applicable |
| **On loan** | refused "Copy is not available" (TC-CHK-06) | → Available (TC-RET-01) or → On hold (TC-RET-02) | refused "Copy is not on the shelf" (TC-CAT-13) | not applicable |
| **On hold** | holder → On loan (TC-CHK-14); other → refused (TC-CHK-08) | refused "Copy is not on loan" (TC-STC-02) | refused "Copy is not on the shelf" (TC-STC-01) | → On hold for next (TC-EXP-02, TC-CAN-02) or → Available (TC-EXP-01, TC-CAN-03) |
| **Withdrawn** | refused "Copy is not available" (TC-CHK-07) | refused "Copy is not on loan" (TC-STC-03) | not tested (no change) | not applicable |
| **(new copy)** | — | — | — | add copy → Available (TC-CAT-09) or → On hold (TC-CAT-11) |

A 1-switch path test (TC-STC-04) runs one copy through Available → On loan → On hold → On hold (next member)
→ On loan → Available.

**ST-2 Reservation (models §3.2)**

| State \ Event | copy becomes free | holder borrows | deadline passes | cancel |
|---|---|---|---|---|
| **Waiting** | → Ready (TC-RET-02, TC-CAT-11, TC-EXP-02) | — | no change | → Cancelled (TC-CAN-01) |
| **Ready for pickup** | — | → Fulfilled (TC-CHK-14) | → Expired (TC-EXP-01); deadline day: no change (TC-EXP-03) | → Cancelled (TC-CAN-02, TC-CAN-03) |
| **Fulfilled** | — | — | — | refused "Reservation is not active" (TC-STR-01) |
| **Expired / Cancelled** | — | — | — | refused "Reservation is not active" (TC-STR-02) |

### 3.4 Use-case-based tests

| Use case flow | Test case (system level) |
|---|---|
| UC-05 main flow (check out) | TC-UC05-01 |
| UC-05 alternative 3a (rule fails, e.g. loan limit) | TC-UC05-02 |
| UC-06 main flow (return, no queue, late fine) | TC-UC06-01 |
| UC-06 alternative 6a (copy goes on hold) | TC-UC06-02 |
| UC-07 main flow (member renews own loan) | TC-UC07-01 |
| UC-07 alternative 3a (another member's loan → 403) | TC-UC07-02 |
| UC-08 main flow (member reserves, sees position) | TC-UC08-01 |
| UC-08 alternative 3a (copy available → refused) | TC-UC08-02 |

## 4. Test cases

Levels: **U** = unit, **I** = integration, **S** = system, **M** = manual. Unless stated, today = 2026-12-01.
The columns *Actual* and *Result* are filled in when the tests are executed (Section 5).

### 4.1 Fines (FR-12, BR-07, BR-15)

| ID | Req | Tech | Lvl | Input | Expected | Actual | Result |
|---|---|---|---|---|---|---|---|
| TC-FINE-01 | FR-12 | BVA | U | due 12-15, returned 12-14 (−1 day) | 0 | as expected | Pass |
| TC-FINE-02 | FR-12 AC1 | BVA | U | due 12-15, returned 12-15 (0) | 0 | as expected | Pass |
| TC-FINE-03 | FR-12 AC2 | BVA | U | due 12-15, returned 12-16 (1) | 0 (grace period, CR-01; was 20) | as expected | Pass |
| TC-FINE-04 | FR-12 | BVA | U | 49 days late | 980 | as expected | Pass |
| TC-FINE-05 | FR-12 AC3 | BVA | U | 50 days late | 1000 | as expected | Pass |
| TC-FINE-06 | FR-12 AC4 | BVA | U | 51 days late | 1000 | as expected | Pass |
| TC-FINE-07 | FR-12 AC4 | EP | U | 365 days late | 1000 | as expected | Pass |
| TC-FINE-08 | FR-12 AC5 | BVA | U | 2 days late (last grace day, CR-01) | 0 | as expected | Pass |
| TC-FINE-09 | FR-12 AC6 | BVA | U | 3 days late (first day after grace, CR-01) | 60 | as expected | Pass |

### 4.2 ISBN validation (FR-03 AC2, BR-11)

| ID | Req | Tech | Lvl | Input | Expected | Actual | Result |
|---|---|---|---|---|---|---|---|
| TC-ISBN-01 | BR-11 | EP | U | `9780306406157` | valid | as expected | Pass |
| TC-ISBN-02 | BR-11 | EP | U | `978-0-306-40615-7` | valid (hyphens removed) | as expected | Pass |
| TC-ISBN-03 | BR-11 | EP | U | `9780306406158` (wrong check digit) | invalid | as expected | Pass |
| TC-ISBN-04 | BR-11 | BVA | U | `978030640615` (12 digits) | invalid | as expected | Pass |
| TC-ISBN-05 | BR-11 | BVA | U | `97803064061570` (14 digits) | invalid | as expected | Pass |
| TC-ISBN-06 | BR-11 | EP | U | `978030640615X` | invalid | as expected | Pass |
| TC-ISBN-07 | BR-11 | EP | U | empty string | invalid | as expected | Pass |

### 4.3 Catalogue and search (FR-03 to FR-06)

| ID | Req | Tech | Lvl | Input | Expected | Actual | Result |
|---|---|---|---|---|---|---|---|
| TC-CAT-01 | FR-03 AC1 | EP | I | add *Dune*, ISBN 9780441172719, year 1990 | title stored, found by ISBN | as expected | Pass |
| TC-CAT-02 | FR-03 AC3 | EP | I | add a second title with ISBN 9780441172719 | "ISBN already exists" | as expected | Pass |
| TC-CAT-03 | FR-03 AC4 | BVA | I | year 1799 | rejected, names "year" | as expected | Pass |
| TC-CAT-04 | FR-03 AC4 | BVA | I | year 1800 | accepted | as expected | Pass |
| TC-CAT-05 | FR-03 AC4 | BVA | I | year 2026 (current) | accepted | as expected | Pass |
| TC-CAT-06 | FR-03 AC4 | BVA | I | year 2027 | rejected, names "year" | as expected | Pass |
| TC-CAT-07 | FR-03 AC4 | EP | I | empty title | rejected, names "title" | as expected | Pass |
| TC-CAT-08 | FR-03 AC4 | EP | I | empty author | rejected, names "author" | as expected | Pass |
| TC-CAT-09 | FR-04 AC1 | ST | I | add copy C-001 to *Dune*, no reservations | copy Available; available count 0 → 1 | as expected | Pass |
| TC-CAT-10 | FR-04 AC2 | EP | I | add copy with existing code C-001 | "Copy code already exists" | as expected | Pass |
| TC-CAT-11 | FR-04 AC3 | ST | I | *Dune* has Waiting reservation by Ann; add copy C-002 | C-002 On hold for Ann; Ann's reservation Ready, deadline 12-04 | as expected | Pass |
| TC-CAT-12 | FR-05 AC1 | ST | I | withdraw Available copy | copy Withdrawn, not counted as available | as expected | Pass |
| TC-CAT-13 | FR-05 AC2 | ST | I | withdraw copy On loan | "Copy is not on the shelf" | as expected | Pass |
| TC-SRC-01 | FR-06 AC1 | EP | I | titles *Dune*, *Dune Messiah*, *Clean Code*; search "dune" | *Dune*, *Dune Messiah* | as expected | Pass |
| TC-SRC-02 | FR-06 | EP | I | search "herbert" (author) | both Dune titles | as expected | Pass |
| TC-SRC-03 | FR-06 | EP | I | search "9780132350884" | *Clean Code* | as expected | Pass |
| TC-SRC-04 | FR-06 AC2 | EP | S | search "zzz" | page shows "No titles found" | as expected | Pass |
| TC-SRC-05 | FR-06 AC3 | EP | I | *Dune* with 3 copies, 1 On loan | "2 of 3 available" (available 2, total 3) | as expected | Pass |
| TC-SRC-06 | FR-06 AC4 | EP | I | empty search text | all 3 titles in alphabetical order | as expected | Pass |

### 4.4 Accounts, access and members (FR-01, FR-02, FR-07, FR-08)

| ID | Req | Tech | Lvl | Input | Expected | Actual | Result |
|---|---|---|---|---|---|---|---|
| TC-AUTH-01 | FR-01 AC1 | EP | S | Ann logs in with correct password | redirect to /account; Lib → librarian dashboard | as expected | Pass |
| TC-AUTH-02 | FR-01 AC2 | EP | S | Ann with wrong password | "Invalid e-mail or password"; no session | as expected | Pass |
| TC-AUTH-03 | FR-01 AC2 | EP | S | unknown e-mail | same message as TC-AUTH-02; no session | as expected | Pass |
| TC-AUTH-04 | FR-01 AC3 | EP | I | Cem (deactivated) with correct password | "Account is deactivated" | as expected | Pass |
| TC-AUTH-05 | FR-01 AC4 | ST | S | Ann logs out, then opens /account | redirect to /login | as expected | Pass |
| TC-ACC-01 | FR-02 AC1, NFR-03 | EP | S | Ann calls **every** librarian route (parametrised) | HTTP 403 for each | as expected | Pass |
| TC-ACC-02 | FR-02 AC2, NFR-03 | EP | S | not logged in, calls every protected route | redirect to /login for each | as expected | Pass |
| TC-ACC-03 | FR-02 AC3 | EP | S | Ann posts renew for Ben's loan | HTTP 403; Ben's loan unchanged | as expected | Pass |
| TC-ACC-04 | FR-02 AC3 | EP | S | Ann cancels Ben's reservation | HTTP 403; reservation unchanged | as expected | Pass |
| TC-ACC-05 | FR-02 | EP | S | Lib calls every librarian route | never 403: pages 200, actions 200 or 302 | as expected | Pass |
| TC-MEM-01 | FR-07 AC1 | EP | I | register Dan, unused e-mail, password 8 chars | active Member; can log in | as expected | Pass |
| TC-MEM-02 | FR-07 AC2 | EP | I | register with Ann's e-mail | "E-mail already registered" | as expected | Pass |
| TC-MEM-03 | FR-07 AC3 | BVA | I | password of 7 characters | "Password too short" | as expected | Pass |
| TC-MEM-04 | FR-07 AC3 | BVA | I | password of 8 characters | accepted | as expected | Pass |
| TC-MEM-05 | FR-08 AC1 | DT | I | deactivate Ben: no loans, balance 0 | Ben inactive; cannot log in | as expected | Pass |
| TC-MEM-06 | FR-08 AC2 | DT | I | deactivate Ann with 1 open loan | refused, reason "open loans" | as expected | Pass |
| TC-MEM-07 | FR-08 AC2 | DT | I | deactivate Ann with balance 20 | refused, reason "outstanding balance" | as expected | Pass |

### 4.5 Checkout (FR-09, DT-1)

| ID | Req | Tech | Lvl | Input | Expected | Actual | Result |
|---|---|---|---|---|---|---|---|
| TC-CHK-01 | FR-09 | DT R1 | U | active, 0 loans, no overdue, balance 0, copy Available | None (allowed) | as expected | Pass |
| TC-CHK-02 | FR-09 AC7 | DT R2 | U | inactive member | "Account is deactivated" | as expected | Pass |
| TC-CHK-03 | FR-09 AC2 | DT R3, BVA | U | 5 active loans | "Loan limit reached (5)" | as expected | Pass |
| TC-CHK-04 | FR-09 AC3 | DT R4 | U | has an overdue loan | "Member has overdue items" | as expected | Pass |
| TC-CHK-05 | FR-09 AC4 | DT R5, BVA | U | balance 501 | "Outstanding fines exceed 5.00 AZN" | as expected | Pass |
| TC-CHK-06 | FR-09 AC5 | DT R6 | U | copy On loan | "Copy is not available" | as expected | Pass |
| TC-CHK-07 | FR-09 AC5 | DT R7 | U | copy Withdrawn | "Copy is not available" | as expected | Pass |
| TC-CHK-08 | FR-09 AC6 | DT R8 | U | copy On hold for Ben, borrower Ann | "Copy is held for another member" | as expected | Pass |
| TC-CHK-09 | FR-09 AC6 | DT R9 | U | copy On hold for Ann, borrower Ann | None (allowed) | as expected | Pass |
| TC-CHK-10 | FR-09 | BVA | U | 4 active loans | None (allowed) | as expected | Pass |
| TC-CHK-11 | FR-09 AC4 | BVA | U | balance 500 | None (allowed) | as expected | Pass |
| TC-CHK-12 | FR-09 | DT | U | inactive + 5 loans + copy On loan | "Account is deactivated" (first failing rule) | as expected | Pass |
| TC-CHK-13 | FR-09 AC1 | ST | I | Ann borrows C-001 on 2026-12-01 | loan due 2026-12-15; copy On loan | as expected | Pass |
| TC-CHK-14 | FR-09 AC6, FR-14 AC2 | ST | I | C-001 On hold for Ann; Ann borrows it | loan created; reservation Fulfilled; copy On loan | as expected | Pass |
| TC-CHK-15 | FR-09 AC3, BR-06 | BVA | I | Ann has a loan due 2026-11-30 | "Member has overdue items" | as expected | Pass |
| TC-CHK-16 | BR-06 | BVA | I | Ann has a loan due 2026-12-01 (today) | checkout allowed | as expected | Pass |
| TC-CHK-17 | FR-09 | EP | I | copy code "NOPE" | "Copy not found"; nothing saved | as expected | Pass |

### 4.6 Return, holds and expiry (FR-10, FR-14, FR-15, FR-16)

| ID | Req | Tech | Lvl | Input | Expected | Actual | Result |
|---|---|---|---|---|---|---|---|
| TC-RET-01 | FR-10 AC1 | ST | I | loan due 12-15, returned 12-15, no reservations | loan closed, fine 0, copy Available | as expected | Pass |
| TC-RET-02 | FR-10 AC2, FR-14 AC1 | ST | I | Waiting: Ann (first), Ben; copy returned 12-01 | copy On hold for Ann; Ann Ready, deadline 12-04; Ben Waiting, position 1 | as expected | Pass |
| TC-RET-03 | FR-10 AC3 | ST | I | return an Available copy | "Copy is not on loan" | as expected | Pass |
| TC-RET-04 | FR-10, FR-12 | BVA | I | loan due 11-27, returned 12-01 (4 days; CR-01 changed it from 2 days) | fine 80 stored; Ann's balance 80 | as expected | Pass |
| TC-EXP-01 | FR-15 AC1 | ST, BVA | I | Ann's hold deadline 12-18; expiry run 12-19; no other reservation | Ann Expired; copy Available | as expected | Pass |
| TC-EXP-02 | FR-15 AC2 | ST | I | as EXP-01 plus Ben Waiting | copy On hold for Ben, deadline 12-22 | as expected | Pass |
| TC-EXP-03 | FR-15 AC3 | BVA | I | expiry run on 12-18 (deadline day) | nothing changes | as expected | Pass |
| TC-EXP-04 | FR-15, A-05 | ST | I | as EXP-02, but no explicit expiry: Ben checks out the copy on 12-19 | checkout runs expiry first and succeeds for Ben | as expected | Pass |
| TC-CAN-01 | FR-16 AC1 | ST | I | Waiting: Ann, Ben, Cem*; Ann cancels | Ann Cancelled; Ben position 1 | as expected | Pass |
| TC-CAN-02 | FR-16 | ST | I | Ann Ready (copy held), Ben Waiting; Ann cancels | copy On hold for Ben | as expected | Pass |
| TC-CAN-03 | FR-16 | ST | I | Ann Ready, queue empty; Ann cancels | copy Available | as expected | Pass |
| TC-STR-01 | FR-16 | ST | I | cancel a Fulfilled reservation | "Reservation is not active" | as expected | Pass |
| TC-STR-02 | FR-16 | ST | I | cancel an Expired reservation | "Reservation is not active" | as expected | Pass |
| TC-STC-01 | FR-05 AC2 | ST | I | withdraw a copy On hold | "Copy is not on the shelf" | as expected | Pass |
| TC-STC-02 | FR-10 AC3 | ST | I | return a copy On hold | "Copy is not on loan" | as expected | Pass |
| TC-STC-03 | FR-10 AC3 | ST | I | return a Withdrawn copy | "Copy is not on loan" | as expected | Pass |
| TC-STC-04 | FR-09, FR-10, FR-14, FR-15 | ST (1-switch) | I | one copy: Ann borrows → Ben, Cem* reserve → Ann returns → Ben's hold expires → Cem borrows → Cem returns | states: On loan → On hold (Ben) → On hold (Cem) → On loan → Available | as expected | Pass |

\* In TC-CAN-01 and TC-STC-04 "Cem" is an active member created for the test (the standard Cem is deactivated).

### 4.7 Renewal (FR-11, DT-2)

| ID | Req | Tech | Lvl | Input | Expected | Actual | Result |
|---|---|---|---|---|---|---|---|
| TC-REN-01 | FR-11 | DT R1 | U | count 0, due 12-15, today 12-10, not reserved | None (allowed) | as expected | Pass |
| TC-REN-02 | FR-11 | BVA | U | count 1 | None (allowed) | as expected | Pass |
| TC-REN-03 | FR-11 AC2 | DT R2, BVA | U | count 2 | "Maximum renewals reached (2)" | as expected | Pass |
| TC-REN-04 | FR-11 AC3 | DT R3, BVA | U | due 11-30, today 12-01 | "Overdue loans cannot be renewed" | as expected | Pass |
| TC-REN-05 | FR-11 | BVA | U | due 12-01, today 12-01 | None (allowed) | as expected | Pass |
| TC-REN-06 | FR-11 AC4 | DT R4 | U | reserved by another member | "Title is reserved by another member" | as expected | Pass |
| TC-REN-07 | FR-11 AC1 | ST | I | loan due 12-15, count 0, renewed on 12-10 | due 12-29, count 1 | as expected | Pass |
| TC-REN-08 | FR-02 AC3 | EP | I | Ann renews Ben's loan | AccessDeniedError; loan unchanged | as expected | Pass |
| TC-REN-09 | FR-11 AC4, BR-04 | DT | I | Ben has a Waiting reservation for the title; Ann renews | "Title is reserved by another member" | as expected | Pass |

### 4.8 Reservation (FR-13, DT-3)

| ID | Req | Tech | Lvl | Input | Expected | Actual | Result |
|---|---|---|---|---|---|---|---|
| TC-RES-01 | FR-13 | DT R1 | U | available 0, not reserved, not on loan, active 0 | None (allowed) | as expected | Pass |
| TC-RES-02 | FR-13 AC2 | DT R2 | U | available 1 | "A copy is available — borrow it at the desk" | as expected | Pass |
| TC-RES-03 | FR-13 AC3 | DT R3 | U | already reserved | "You already reserved this title" | as expected | Pass |
| TC-RES-04 | FR-13 AC5 | DT R4 | U | title on loan to member | "You already have this title on loan" | as expected | Pass |
| TC-RES-05 | FR-13 AC4 | DT R5, BVA | U | active 3 | "Reservation limit reached (3)" | as expected | Pass |
| TC-RES-06 | FR-13 | BVA | U | active 2 | None (allowed) | as expected | Pass |
| TC-RES-07 | FR-13 AC1, FR-14 | ST | I | all copies of *Dune* on loan; Ann then Ben reserve | Ann Waiting position 1; Ben position 2 | as expected | Pass |
| TC-RES-08 | FR-13 | EP | I | only copy On hold for Ben; Ann reserves | accepted (no Available copy) | as expected | Pass |

### 4.9 Account page, payments and overdue list (FR-17, FR-18, FR-19)

| ID | Req | Tech | Lvl | Input | Expected | Actual | Result |
|---|---|---|---|---|---|---|---|
| TC-ACCT-01 | FR-17 AC1 | UC | S | Ann: 2 open loans, fines 80 (CR-01) | page shows both loans with due dates and "0.80 AZN" | as expected | Pass |
| TC-ACCT-02 | FR-17, NFR-06 | EP | S | Ann is 2nd in a queue behind Ben | page shows "position 2"; Ben's name not shown | as expected | Pass |
| TC-PAY-01 | FR-18 AC1 | EP | U | amount 60, balance 100 | None (allowed) | as expected | Pass |
| TC-PAY-02 | FR-18 AC2 | BVA | U | amount 0 | "Amount must be positive" | as expected | Pass |
| TC-PAY-03 | FR-18 AC2 | BVA | U | amount 101, balance 100 | "Amount exceeds balance" | as expected | Pass |
| TC-PAY-04 | FR-18 | BVA | U | amount 100, balance 100 | None (allowed) | as expected | Pass |
| TC-PAY-05 | FR-18 | BVA | U | amount 1 | None (allowed) | as expected | Pass |
| TC-PAY-06 | FR-18 AC1 | EP | I | balance 100; record 60 | balance 40 | as expected | Pass |
| TC-OVD-01 | FR-19 | EP | I | loans due 11-21 (10 days) and 11-28 (3 days) | listed: 10 days (200) first, then 3 days (60) | as expected | Pass |
| TC-OVD-02 | FR-19 | BVA | I | loan due 12-01 (today) | not listed | as expected | Pass |

### 4.10 Use-case-based system tests (UC-05 to UC-08)

| ID | Req | Tech | Lvl | Input | Expected | Actual | Result |
|---|---|---|---|---|---|---|---|
| TC-UC05-01 | FR-09 | UC | S | Lib posts checkout form: Ann, C-001 | page shows "due 2026-12-15" | as expected | Pass |
| TC-UC05-02 | FR-09 AC2 | UC | S | Ann has 5 loans; Lib posts checkout | page shows "Loan limit reached (5)"; no new loan | as expected | Pass |
| TC-UC06-01 | FR-10, FR-12 | UC | S | Lib returns C-001, 4 days late (CR-01) | page shows fine "0.80 AZN" | as expected | Pass |
| TC-UC06-02 | FR-10 AC2 | UC | S | Ben waiting; Lib returns C-001 | page says copy is on hold for the next member | as expected | Pass |
| TC-UC07-01 | FR-11 | UC | S | Ann clicks Renew on own loan | page shows new due date | as expected | Pass |
| TC-UC07-02 | FR-02 AC3 | UC | S | Ann posts renew for Ben's loan id | HTTP 403 | as expected | Pass |
| TC-UC08-01 | FR-13 | UC | S | Ann reserves *Dune* (all on loan) | page shows "position 1" | as expected | Pass |
| TC-UC08-02 | FR-13 AC2 | UC | S | Ann reserves title with a copy on the shelf | page shows "A copy is available — borrow it at the desk" | as expected | Pass |

### 4.11 Non-functional tests

| ID | Req | Tech | Lvl | Input | Expected | Actual | Result |
|---|---|---|---|---|---|---|---|
| TC-NFR-01 | NFR-01 | — | I | 1,000 titles, 3,000 copies; 100 random searches | 95th percentile ≤ 1 s | as expected | Pass |
| TC-NFR-02 | NFR-02 | EP | I | register member with password "secret123" | stored hash ≠ password; starts with `scrypt:` or `pbkdf2:`; no column contains "secret123" | as expected | Pass |
| TC-NFR-03 | NFR-03 | — | S | list of all routes vs routes covered by TC-ACC-01/02 | every librarian route is covered | as expected | Pass |
| TC-NFR-04 | NFR-04 | — | I | inject an error in `serve_queue` during a return | loan still open, copy still On loan, no reservation changed | as expected | Pass |
| TC-NFR-05 | NFR-05 | — | M | 2 people who never used the system: checkout + return | each finishes in ≤ 2 min with on-screen labels only | Not run yet: manual walkthrough with 2 people is planned before submission | Not run |
| TC-NFR-06 | NFR-06 | — | I | inspect `user` table columns | only id, email, password_hash, full_name, phone, role, is_active, created_at | as expected | Pass |
| TC-NFR-07 | NFR-07 | — | — | coverage report of `library/services` | ≥ 90 % statements | Coverage of library/services 87–100 % per module, 95 % total (section 5.3) | Pass |
| TC-NFR-08 | NFR-08 | — | — | fresh clone, new venv, `run_tests` | install + start in ≤ 5 commands; suite ≤ 30 s | CI installs from requirements.txt and runs the suite in < 20 s; install + start = 5 commands (README) | Pass |

### 4.12 Summary

| Area | Unit | Integration | System | Manual / other | Total |
|---|---|---|---|---|---|
| Fines, ISBN | 16 | — | — | — | 16 |
| Catalogue, search | — | 18 | 1 | — | 19 |
| Accounts, access, members | — | 8 | 9 | — | 17 |
| Checkout | 12 | 5 | — | — | 17 |
| Return, holds, expiry, state | — | 17 | — | — | 17 |
| Renewal | 6 | 3 | — | — | 9 |
| Reservation | 6 | 2 | — | — | 8 |
| Account, payments, overdue | 5 | 3 | 2 | — | 10 |
| Use-case-based | — | — | 8 | — | 8 |
| Non-functional | — | 4 | 1 | 3 | 8 |
| **Total** | **45** | **60** | **21** | **3** | **129** |

Techniques used: EP, BVA, DT, ST and UC (five; the course requires at least three).

## 5. Test report

### 5.1 Execution summary

| Item | Value |
|---|---|
| Date of the final run | 2026-11-25 (and on every push in GitHub Actions) |
| Command | `python run_tests.py` (results copied into section 4 by `python scripts/trace.py`) |
| Environment | Windows 11 + Python 3.12.10 locally; Ubuntu + Python 3.12 in CI |
| Test cases in the plan | 129 (127 + TC-FINE-08/09 added by CR-01) |
| Automated test cases | 126 (all pass) |
| Executed test functions / parameter sets | 158 (all pass), of which 32 are technical tests without a test case ID (listed in `docs/traceability.md` §3) |
| Measured, not a test function | TC-NFR-07 (coverage), TC-NFR-08 (install and run time) — both pass |
| Not run | TC-NFR-05 (manual usability walkthrough) — planned before submission |
| Duration of the whole suite | 4–10 s locally, < 20 s in CI (NFR-08 limit: 30 s) |
| NFR-01 search time | p95 = 7.1 ms for 1,000 titles / 3,000 copies on the development laptop (limit 1 s) |

**Exit criteria (section 2.6):** all Must test cases executed and passing — met; ≥ 95 % of automated test
cases pass — met (100 %); no open Critical/High defect — met; service coverage ≥ 90 % — met (see 5.3);
usability walkthrough — **not yet met** (TC-NFR-05).

### 5.2 Changes to test cases during execution
- **TC-ACC-05:** the expected result "HTTP 200 for each" only holds for pages (GET). Librarian *actions*
  (POST) answer with a redirect (302) after showing a message. The test now expects 200 for GET and 200/302 for
  POST; the important property — never 403 for a librarian — is unchanged.
- **TC-NFR-01:** implemented with a fixed random seed so that the 100 searches are the same on every run.

### 5.3 Code coverage

Statement and branch coverage measured with pytest-cov on the full suite (`htmlcov/index.html`):

| Layer | Modules | Coverage |
|---|---|---|
| Business logic | `services/policies.py` 100 %, `auth.py` 100 %, `circulation.py` 94 %, `reservations.py` 92 %, `catalogue.py` 90 %, `members.py` 87 % | ≥ 90 % in total (NFR-07 met) |
| Data access | `repositories/__init__.py` 96 %, `db.py` 93 % | — |
| Presentation | `web/*.py` 87–100 % | — |
| **Whole system** | 1,047 statements, 190 branches | **95 %** |

**What coverage tells us and what it does not.** Coverage shows which lines and branches were *executed* by at
least one test. The uncovered lines are mostly defensive branches such as "Title not found" or "Member not
found" that the user interface cannot reach with normal use. High coverage does **not** prove the code is
correct: a line can run without any assertion checking its effect, and coverage cannot reveal a requirement
that was never coded (for example the missing FR-04 rule found in review, D-03, would not have shown up as a
coverage gap). That is why the test cases were derived from the requirements with systematic techniques, and why
the traceability matrix, not the coverage number, is used to decide whether every requirement is tested.

### 5.4 Observations
- All service-level tests passed the first time they were run after the code was written. The test-first order
  is visible in Git: every feature branch starts with a `test: … (red)` commit.
- The system tests found one real defect in the web layer (D-01); a manual run found another one in the demo data
  (D-02). Both were fixed and covered by tests.

## 6. Defect log

Every problem found during design, implementation and testing, including problems in documents, tests and
the build. Severity levels: section 2.7.

| ID | Date | Found by | Description | Severity | Fix | Commit |
|---|---|---|---|---|---|---|
| D-01 | 2026-11-25 | Test TC-AUTH-01 (system) | After login the user was sent to `/` and redirected a second time instead of going straight to the role's home page (FR-01 AC1). | Low | `auth.login` redirects directly to the dashboard (librarian) or "My account" (member). | `a4976f4` |
| D-02 | 2026-11-25 | Manual run of `flask seed-demo` | Demo data crashed with "Copy code already exists": *Dune* and *Dune Messiah* both produced copy codes `DUN-001`. | Low | Explicit unique code prefix per demo title; regression test `test_seed_demo_creates_data_once`. | `acf3efa` |
| D-03 | 2026-11-15 | Review while drawing the Copy state machine | Requirement gap: a new copy of a title with waiting reservations would become Available and bypass the queue (FR-04 vs FR-14). | High | Requirements v1.1: FR-04 AC3; test TC-CAT-11. | `c5550f8` |
| D-04 | 2026-11-15 | Review while writing the test plan | Design defect: decision rules were inside services that need a database, so the decision tables could not be unit-tested. | Medium | Models v1.1: pure `EligibilityPolicy`. | `1721c51` |
| D-05 | 2026-11-25 | Code review of the commit list | Generated folder `src/library_ms.egg-info` was committed by `git add -A`. | Low | Removed from the repository and added to `.gitignore`. | `3060217` |
| D-06 | 2026-11-25 | Timing of the test run | The suite took 17 s because every test member got a full-cost scrypt password hash; risk for NFR-08 (≤ 30 s) as the suite grows. | Medium | Tests use a cheaper PBKDF2 setting through a fixture; production keeps scrypt (checked by TC-NFR-02). | `0a513c9` |
| D-07 | 2026-11-25 | First run of the system tests | `tests/system/conftest.py` imported itself (`from conftest import …`), so no system test could start. | Low | Shared test data moved to `tests/helpers.py`. | `2cf9c06` |
| D-08 | 2026-11-25 | Impact analysis of CR-01 (prediction vs. actual run) | The system test for recording a payment passed for the wrong reason: it only checked that the page shows "0.00 AZN", which is also true when the payment is refused. | Medium | The test now checks the success message "Payment recorded. New balance 0.00 AZN". | see CR-01 commits |
| D-09 | 2026-11-25 | Code review (R-01) | Fixed, publicly known session key when `LIBRARY_SECRET_KEY` is not set; sessions could be forged. | High | Random key at start. | `05cb678` |
| D-10 | 2026-11-25 | Code review (R-02) | Open redirect: `/\evil.example` passed the redirect check after login. | Medium | `safe_next()` rejects `//` and backslashes. | `6dbbf5e` |
| D-11 | 2026-11-25 | Code review (R-03) | SQL in the web layer (dashboard), against the architecture. | Low | `CirculationService.desk_stats()`. | `32bde01` |

No defect is open.

