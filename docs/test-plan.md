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

