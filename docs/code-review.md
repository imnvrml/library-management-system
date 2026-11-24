# Code Review — Library Management System

| | |
|---|---|
| **Reviewer** | Ramil İmanov (self-review) |
| **Date** | 2026-11-25 |
| **Scope** | All code in `src/library/` and `tests/` on `main` after step 6 (commit `Merge pull request #24`) |
| **Method** | Each checklist item was checked file by file; every finding got an ID, a test where possible, and a fix on branch `fix/code-review` |

## 1. Checklist

Result: ✅ OK · ⚠️ finding (see section 2) · ➖ accepted limitation (see section 3)

| # | Area | Checklist item | Result |
|---|---|---|---|
| 1 | Requirements | Every Must requirement is implemented and has at least one passing test (`docs/traceability.md`) | ✅ |
| 2 | Requirements | Messages shown to users are the exact texts from the acceptance criteria | ✅ |
| 3 | Design | Code structure matches the design class diagrams (layers, class and method names) | ✅ deviations documented (reflection §2) |
| 4 | Design | Business rules only in the service layer; web layer has no business logic | ✅ |
| 5 | Design | SQL only in the repositories | ⚠️ R-03 |
| 6 | Design | Rule values only in `Rules` (no magic numbers in services) | ✅ |
| 7 | Correctness | Date boundaries use the injected `Clock`, never `date.today()` directly | ✅ (only `SystemClock`) |
| 8 | Correctness | Money is calculated in integer qəpik, never in float | ✅ (`parse_azn`, `azn`) |
| 9 | Correctness | Every multi-step change runs inside one transaction (NFR-04) | ✅ (checkout, return, renew, place, cancel, expire, add copy) |
| 10 | Correctness | Refused actions change nothing (rollback on `BusinessRuleError`) | ✅ (tests `test_checkout_refusal_saves_nothing`, TC-NFR-04) |
| 11 | Security | Passwords hashed with a salted slow hash; never logged or shown | ✅ (scrypt, TC-NFR-02) |
| 12 | Security | Every page declares its roles; members cannot act on other members' records | ✅ (TC-ACC-01…04, TC-NFR-03) |
| 13 | Security | Every POST form carries a CSRF token | ✅ (`test_post_without_csrf_token_is_rejected`) |
| 14 | Security | No publicly known secret key | ⚠️ R-01 |
| 15 | Security | Redirect targets taken from the request are limited to this site | ⚠️ R-02 |
| 16 | Security | SQL uses parameters only (no string formatting with user input) | ✅ (one f-string in a test only, for a table name) |
| 17 | Security | Templates escape all user data (Jinja autoescape on) | ✅ |
| 18 | Security | Brute-force protection on login | ➖ L-01 |
| 19 | Privacy | Members never see other members' names (NFR-06) | ✅ (TC-ACCT-02) |
| 20 | Error handling | Unknown IDs give a clear message or 404, never a server error | ✅ |
| 21 | Performance | No query inside a loop on large tables | ➖ L-02 |
| 22 | Usability / a11y | Every input has a visible label; messages use `role="status"`/`role="alert"`; works at phone width | ✅ |
| 23 | Tests | Every test carries a test case ID or is listed as a technical test in the traceability matrix | ✅ |
| 24 | Tests | Tests are independent (own data, fixed clock, no order dependence) | ✅ |
| 25 | Tests | Assertions check the effect, not only that a page loads | ⚠️ was D-08 (fixed in step 6) |
| 26 | Maintainability | Functions are short; names follow the design; comments explain *why* | ✅ |
| 27 | Process | No generated files or secrets in Git | ✅ after D-05 |
| 28 | Process | CI runs all tests on every push and pull request | ✅ |

## 2. Findings fixed during the review

| ID | Severity | File | Finding | Fix | Test | Commit |
|---|---|---|---|---|---|---|
| R-01 | High | `src/library/__init__.py` | Without `LIBRARY_SECRET_KEY` the app used the fixed key `dev-only-change-me`, which is in the public repository. Anyone could forge a session cookie and log in as a librarian. | A random 64-character key is generated at start when none is configured; README explains how to set a permanent one. | `test_R01_no_fixed_secret_key_when_not_configured` | `05cb678` |
| R-02 | Medium | `src/library/web/__init__.py`, `auth.py` | The redirect check allowed `/\evil.example`, which browsers treat like `//evil.example` (open redirect after login). | One helper `safe_next()` used by login and all forms; rejects `//` and any backslash. | `test_R02_login_ignores_next_url_pointing_to_another_site` | `6dbbf5e` |
| R-03 | Low | `src/library/web/circulation.py` | The dashboard ran its own SQL in the web layer, against the architecture rule "SQL only in repositories". | `CirculationService.desk_stats()` with three small repository methods. | `test_R03_desk_statistics_come_from_the_service_layer` | `32bde01` |

## 3. Accepted limitations (not fixed, with reason)

| ID | Limitation | Why accepted | When to change |
|---|---|---|---|
| L-01 | No limit on failed login attempts. | The system runs on the library's own computer (C-04), not on the internet. | Before making the system reachable from outside the library network. |
| L-02 | Some pages load related rows one by one (member list, overdue list, account page). | With a few hundred members and loans each page needs far less than 100 ms; NFR-01 is met by a wide margin (p95 = 7.1 ms for search). | If a page becomes slower than 1 s, replace the loops with one JOIN query in the repository. |
| L-03 | Search ignores upper/lower case only for English letters (SQLite `LIKE`), so "İ"/"i" are different. | All demo and test data is in English; titles in Azerbaijani still match when typed with the same case. | When Azerbaijani titles are added, use a normalised search column or the ICU extension. |

## 4. Result
All 158 automated tests pass after the review fixes. No Critical or High finding is open.
