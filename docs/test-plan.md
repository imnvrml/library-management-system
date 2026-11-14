# Test Plan and Test Report — Library Management System

| | |
|---|---|
| **Author** | Ramil İmanov (group M666İ5) |
| **Version** | 1.0 (plan; results are added in the test report section) |
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
| Days late at return (FR-12, BR-07) | ≤ 0 → no fine; 1–50 → 20 qəpik/day; > 50 → capped 1000 | — | −1, 0, 1, 49, 50, 51 (+365 as a far value) | TC-FINE-01…07 |
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

