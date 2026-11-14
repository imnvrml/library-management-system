# Requirements Specification — Library Management System (LMS)

| | |
|---|---|
| **Author** | Ramil İmanov (group M666İ5) |
| **Version** | 1.0 |
| **Date** | 2026-11-15 |
| **Status** | Baseline for design |

## 1. Introduction

### 1.1 Purpose
This document specifies the requirements of a Library Management System (LMS) for a small community
library. It is the baseline for the analysis and design models, the test plan and the traceability matrix.

### 1.2 Background
The library currently records loans in a paper ledger and on index cards. Staff cannot see quickly which
copies are on the shelf, who has an overdue book, or who is next in line for a popular title. Fines are
calculated by hand and are often inconsistent. The library wants a small system that enforces the lending
rules the same way for every member.

### 1.3 Definitions

| Term | Meaning |
|---|---|
| **Title** | A bibliographic work identified by an ISBN (e.g. one edition of a novel). |
| **Copy** | One physical item of a title, identified by a unique copy code (barcode label). |
| **Member** | A registered person allowed to borrow copies. |
| **Librarian** | A staff member who operates the circulation desk. |
| **Loan** | The record that a copy was lent to a member, with a due date. |
| **Renewal** | Extending the due date of an active loan. |
| **Reservation** | A member's request to borrow a title when no copy is available. |
| **Hold** | A returned copy that is set aside for the first member in the reservation queue. |
| **Fine** | A charge for returning a copy after its due date. |
| **Balance** | The sum of a member's fines minus the payments they made. |
| **AZN** | Azerbaijani manat; 1 AZN = 100 qəpik. |

Requirements use the keyword **shall** for mandatory behaviour. Business rules (BR-xx, Section 7) hold the
numeric parameters so that each value is defined in exactly one place.

## 2. Scope

### 2.1 In scope
- Catalogue of titles and their physical copies.
- Member registration and accounts with two roles: Librarian and Member.
- Circulation: checkout, return, renewal, loan limits.
- Overdue fines and fine payments recorded at the desk.
- Reservation queue with holds for returned copies.
- Catalogue search and a member self-service page.

### 2.2 Out of scope
Online payment, e-mail/SMS notifications, barcode-scanner hardware, inter-library loans, acquisitions
(ordering books from suppliers), e-books, and multiple branches. These are listed as **Won't** in Section 5.

### 2.3 Core and extensions
The **core** (fully implemented) is every requirement with priority **Must**. **Should** requirements are
implemented if time allows; **Could** requirements are specified as extensions and may stay unimplemented.

## 3. Stakeholders

| Stakeholder | Role / interest | Influence |
|---|---|---|
| Library manager | Client and sponsor; defines lending rules and fine amounts; wants fewer lost books and consistent fines. | High |
| Librarians | Primary users at the desk; want fast checkout/return and clear error messages. | High |
| Members | Borrow books; want to know due dates, fines and their place in a reservation queue; want their data kept private. | Medium |
| Course instructor | Evaluates the engineering artefacts. | High |
| Developer (author) | Builds, tests and maintains the system. | Medium |

## 4. User roles

| Role | Can do |
|---|---|
| **Librarian** | Manage catalogue and members, check out, return, renew, record payments, view reports, place reservations on behalf of a member. |
| **Member** | Log in, search the catalogue, place and cancel own reservations, renew own loans, view own loans, fines and reservations. |
| **Visitor** (not logged in) | See the login page only. |

## 5. Functional requirements

Priority uses MoSCoW: **M** = Must, **S** = Should, **C** = Could, **W** = Won't (this release).
Every Must requirement has acceptance criteria (AC) in Given/When/Then form. Should requirements also have
short acceptance criteria because they are planned for implementation.

### 5.1 Accounts and access

**FR-01 — Log in and log out (M).** The system shall let a registered user log in with e-mail and password
and log out again.
- AC1: Given an active user with correct credentials, when they log in, then they see the home page of their role.
- AC2: Given a wrong password or unknown e-mail, when they log in, then the system shows "Invalid e-mail or password" (without saying which one was wrong) and no session is created.
- AC3: Given a deactivated member, when they log in with correct credentials, then login is refused with "Account is deactivated".
- AC4: Given a logged-in user, when they log out, then any protected page redirects to the login page.

**FR-02 — Role-based access (M).** The system shall allow each page and action only to the roles listed in
Section 4.
- AC1: Given a Member, when they open any librarian page, then the system answers HTTP 403.
- AC2: Given a Visitor, when they open any page other than the login page, then they are redirected to the login page.
- AC3: Given a Member, when they request another member's loans, fines or reservations, then the system answers HTTP 403.

### 5.2 Catalogue

**FR-03 — Add a title (M).** The librarian shall be able to add a title with ISBN, title, author(s),
publisher and publication year.
- AC1: Given a valid ISBN-13 that is not yet in the catalogue, when the librarian saves the form, then the title is stored and shown in the catalogue.
- AC2: Given an ISBN that fails the ISBN-13 check-digit rule (BR-11) or is not 13 digits, when saving, then the title is rejected with "Invalid ISBN".
- AC3: Given an ISBN that already exists, when saving, then the title is rejected with "ISBN already exists".
- AC4: Given a publication year outside BR-12, or an empty title or author, when saving, then the form is rejected and names the invalid field.

**FR-04 — Add copies (M).** The librarian shall be able to add one or more physical copies to an existing
title; each copy gets a unique copy code and starts in state *Available*.
- AC1: Given an existing title, when the librarian adds a copy with an unused code, then the copy appears with state Available and the title's available count increases by 1.
- AC2: Given a copy code that is already used, when saving, then the copy is rejected with "Copy code already exists".

**FR-05 — Edit title and withdraw copy (S).** The librarian shall be able to correct title data and withdraw
a copy that is no longer lendable (state *Withdrawn*). A copy that is on loan or on hold cannot be withdrawn.
- AC1: Given an Available copy, when the librarian withdraws it, then its state is Withdrawn and it is no longer counted as available.
- AC2: Given a copy that is On loan, when the librarian tries to withdraw it, then the system refuses with "Copy is not on the shelf".

**FR-06 — Search the catalogue (M).** Any logged-in user shall be able to search titles by a part of the
title, author or ISBN (case-insensitive). Each result shows the number of available copies and the total
number of copies.
- AC1: Given titles "Dune" and "Dune Messiah", when a user searches "dune", then both titles are listed.
- AC2: Given a search text that matches nothing, when searching, then the system shows "No titles found".
- AC3: Given a title with 3 copies of which 1 is on loan, when it is listed, then it shows "2 of 3 available".
- AC4: Given an empty search text, when searching, then all titles are listed in alphabetical order.

### 5.3 Members

**FR-07 — Register a member (M).** The librarian shall be able to register a member with full name, e-mail,
phone and an initial password. The e-mail must be unique.
- AC1: Given valid data and an unused e-mail, when the librarian saves, then the member is created as active with role Member and can log in.
- AC2: Given an e-mail already used by another user, when saving, then registration is rejected with "E-mail already registered".
- AC3: Given a password shorter than BR-13, when saving, then registration is rejected with "Password too short".

**FR-08 — Deactivate a member (S).** The librarian shall be able to deactivate a member who has no active
loans and a zero balance. A deactivated member cannot log in or borrow; their history is kept.
- AC1: Given a member with no active loans and balance 0.00, when the librarian deactivates them, then the account is inactive.
- AC2: Given a member with an active loan or a positive balance, when deactivating, then the system refuses and states the reason.

### 5.4 Circulation

**FR-09 — Check out a copy (M).** The librarian shall be able to lend a copy to a member. The loan's due date
is the checkout date plus the loan period (BR-01). Checkout is allowed only if **all** of these hold:
the member is active; the member has fewer active loans than the loan limit (BR-02); the member has no
overdue loan (BR-06); the member's balance does not exceed the borrowing threshold (BR-05); and the copy is
Available, or is On hold **for this member** (BR-09).
- AC1: Given an eligible member and an Available copy, when the librarian checks it out on 2026-12-01, then a loan with due date 2026-12-15 is created and the copy becomes On loan.
- AC2: Given a member with 5 active loans, when checking out another copy, then the system refuses with "Loan limit reached (5)".
- AC3: Given a member with an overdue loan, when checking out, then the system refuses with "Member has overdue items".
- AC4: Given a member whose balance is 5.01 AZN, when checking out, then the system refuses with "Outstanding fines exceed 5.00 AZN"; with balance exactly 5.00 AZN checkout is allowed.
- AC5: Given a copy that is On loan or Withdrawn, when checking it out, then the system refuses with "Copy is not available".
- AC6: Given a copy On hold for member A, when it is checked out to member B, then the system refuses with "Copy is held for another member"; for member A it succeeds and A's reservation becomes Fulfilled.
- AC7: Given an inactive member, when checking out, then the system refuses with "Account is deactivated".

**FR-10 — Return a copy (M).** The librarian shall be able to register the return of a copy that is on loan.
The system closes the loan, records the return date, charges a fine if the return is late (FR-12), and then
either places the copy On hold for the first waiting reservation of the title (FR-14) or makes it Available.
- AC1: Given a loan due 2026-12-15 and no waiting reservation, when the copy is returned on 2026-12-15, then the loan is closed with fine 0.00 and the copy is Available.
- AC2: Given a waiting reservation for the title, when a copy is returned, then the copy becomes On hold for the first member in the queue and that reservation becomes Ready for pickup with a pickup deadline (BR-08).
- AC3: Given a copy that is not on loan, when the librarian tries to return it, then the system refuses with "Copy is not on loan".

**FR-11 — Renew a loan (M).** A member (for own loans) or the librarian shall be able to renew an active
loan. The new due date is the current due date plus the loan period (BR-01). Renewal is refused if the loan
has already been renewed the maximum number of times (BR-03), if the loan is overdue, or if another member
has a waiting reservation for the same title (BR-04).
- AC1: Given a loan due 2026-12-15 renewed 0 times, when it is renewed on 2026-12-10, then the due date becomes 2026-12-29 and the renewal count is 1.
- AC2: Given a loan already renewed 2 times, when renewing, then the system refuses with "Maximum renewals reached (2)".
- AC3: Given an overdue loan, when renewing, then the system refuses with "Overdue loans cannot be renewed".
- AC4: Given a waiting reservation by another member for the same title, when renewing, then the system refuses with "Title is reserved by another member".

**FR-12 — Calculate overdue fines (M).** When a copy is returned after its due date, the system shall charge
a fine of BR-07 per calendar day late, capped per loan at the BR-07 maximum. Days late = return date − due
date. Fines are calculated exactly in qəpik (no floating-point rounding).
- AC1: Returned on the due date → fine 0.00 AZN.
- AC2: Returned 1 day late → fine 0.20 AZN.
- AC3: Returned 50 days late → fine 10.00 AZN (exactly the cap).
- AC4: Returned 51 days or more late → fine 10.00 AZN (capped).

### 5.5 Reservations

**FR-13 — Place a reservation (M).** A member (for themselves) or the librarian (on behalf of a member) shall
be able to reserve a title. A reservation is accepted only if the title has no Available copy, the member does
not already have an active reservation for the title, the member does not currently borrow a copy of the
title, and the member has fewer active reservations than BR-10. The reservation joins the end of the title's
queue with state *Waiting*.
- AC1: Given a title with all copies on loan, when a member reserves it, then a Waiting reservation is created and the member sees their queue position.
- AC2: Given a title with at least one Available copy, when reserving, then the system refuses with "A copy is available — borrow it at the desk".
- AC3: Given the member already has an active reservation for the title, when reserving again, then the system refuses with "You already reserved this title".
- AC4: Given the member has 3 active reservations, when reserving a fourth title, then the system refuses with "Reservation limit reached (3)".
- AC5: Given the member currently borrows a copy of the title, when reserving it, then the system refuses with "You already have this title on loan".

**FR-14 — Serve the reservation queue (M).** When a copy of a reserved title is returned, the system shall
assign it to the oldest Waiting reservation of that title (first come, first served), put the copy On hold,
set the reservation to *Ready for pickup* and set the pickup deadline (BR-08).
- AC1: Given reservations by A (placed first) and B, when a copy is returned, then A's reservation is Ready for pickup and B stays Waiting at position 1.
- AC2: Given a reservation is Ready for pickup, when the member borrows the held copy (FR-09), then the reservation becomes Fulfilled.

**FR-15 — Expire uncollected holds (M).** If a held copy is not borrowed by the end of its pickup deadline,
the system shall set the reservation to *Expired* and pass the copy to the next Waiting reservation of the
title (FR-14), or make it Available if the queue is empty. Expiry is checked before every circulation action
and on the librarian dashboard (see A-05).
- AC1: Given a hold with pickup deadline 2026-12-18 and no other reservation, when expiry is checked on 2026-12-19, then the reservation is Expired and the copy is Available.
- AC2: Given the same hold and a second Waiting reservation by B, when expiry is checked on 2026-12-19, then the copy is On hold for B with a new pickup deadline.
- AC3: Given the same hold, when expiry is checked on 2026-12-18 (the deadline day), then nothing changes.

**FR-16 — Cancel a reservation (S).** A member shall be able to cancel their own Waiting or Ready-for-pickup
reservation; the librarian may cancel any. Cancelling a Ready-for-pickup reservation passes the held copy on
as in FR-15.
- AC1: Given a Waiting reservation, when the member cancels it, then its state is Cancelled and later members move up one position.

### 5.6 Fines, self-service and reports

**FR-17 — Member account page (S).** A member shall be able to see their active loans with due dates, loan
history, current balance, fines, and reservations with queue position.
- AC1: Given a member with 2 active loans and a 0.40 AZN fine, when they open "My account", then both loans with due dates and a balance of 0.40 AZN are shown.

**FR-18 — Record a fine payment (S).** The librarian shall be able to record a cash payment that reduces the
member's balance. The amount must be positive and must not exceed the balance.
- AC1: Given a balance of 1.00 AZN, when a payment of 0.60 AZN is recorded, then the balance is 0.40 AZN.
- AC2: Given a balance of 1.00 AZN, when a payment of 1.01 AZN or 0.00 AZN is entered, then it is rejected.

**FR-19 — Overdue list (S).** The librarian shall be able to see all overdue loans with member, title, due
date, days late and the fine accrued so far, sorted by days late (most first).

**FR-20 — Statistics report (C).** The librarian could see monthly numbers of loans, returns, new members
and fines charged.

**FR-21 — Lost or damaged copy (C).** The librarian could mark a copy on loan as Lost, which closes the loan
and charges a replacement fee entered by the librarian.

### 5.7 Won't (this release)

| ID | Excluded feature | Reason |
|---|---|---|
| W-01 | Online payment of fines | Needs a payment provider and contracts; the library takes cash at the desk. |
| W-02 | E-mail / SMS reminders | Needs a mail/SMS service; members see due dates on their account page instead. |
| W-03 | Barcode-scanner hardware | Copy codes are typed in; a USB scanner acting as a keyboard would still work. |
| W-04 | Inter-library loans and multiple branches | The library has one site. |
| W-05 | Member self-registration | The library checks identity at the desk before creating an account. |

## 6. Non-functional requirements

Each requirement states how it is measured, so that it can be verified by a test or an inspection.

| ID | Category | Requirement | Measure / verification | Priority |
|---|---|---|---|---|
| NFR-01 | Performance | Catalogue search shall return results quickly on a realistic data volume. | With 1,000 titles and 3,000 copies in the database, 95 % of searches complete in ≤ 1 s on the reference laptop (any 4-core CPU, 8 GB RAM); measured by an automated timing test over 100 searches. | M |
| NFR-02 | Security | Passwords shall never be stored in plain text. | Every stored password is a salted hash produced by Werkzeug `generate_password_hash` (scrypt or PBKDF2); an automated test asserts that the stored value differs from the password and that no column contains the plain text. | M |
| NFR-03 | Security / privacy | Users shall only reach data and actions allowed for their role (FR-02). | 100 % of librarian routes are covered by an automated test that calls them as a Member (expects 403) and as a Visitor (expects redirect to login). | M |
| NFR-04 | Data integrity | Checkout, return, renewal and hold expiry shall be atomic. | Each operation runs in one database transaction; a fault-injection test that raises an error in the middle of a return leaves loan, copy and reservation rows unchanged. | M |
| NFR-05 | Usability | A new librarian shall be able to perform a checkout without training. | In a walkthrough with 2 people who have never seen the system, each completes a checkout and a return within 2 minutes using only on-screen labels; every refused action shows a message that names the rule (e.g. "Loan limit reached (5)"). | S |
| NFR-06 | Privacy | The system shall store only the personal data needed for lending. | Member data is limited to full name, e-mail, phone and password hash; checked by schema inspection. Members never see other members' names in queues (only their own position). | M |
| NFR-07 | Maintainability | The business rules shall be well tested. | Statement coverage of the service (business-logic) layer ≥ 90 %, measured with pytest-cov. | S |
| NFR-08 | Portability / operability | The system shall be easy to install and test. | Runs on Windows 10+ and Linux with Python 3.12 and only the packages in `requirements.txt`; install + start takes ≤ 5 commands; the full automated test suite runs with one command in ≤ 30 s. | M |

## 7. Business rules

The numeric parameters below are referenced by the functional requirements. They are defined in one
configuration module in the code so that the library manager can change them without changing logic.

| ID | Rule | Value |
|---|---|---|
| BR-01 | Loan period (also the renewal extension) | 14 calendar days |
| BR-02 | Maximum number of active loans per member | 5 |
| BR-03 | Maximum renewals per loan | 2 |
| BR-04 | A loan cannot be renewed while another member has a Waiting reservation for the same title | — |
| BR-05 | Borrowing threshold: checkout is refused if the balance is **greater than** this amount | 5.00 AZN |
| BR-06 | A loan is overdue when the current date is later than its due date; a member with an overdue loan cannot borrow | — |
| BR-07 | Overdue fine per calendar day / maximum fine per loan | 0.20 AZN / 10.00 AZN |
| BR-08 | Pickup period for a hold: pickup deadline = date the hold starts + this period; the copy can be collected until the end of the deadline day | 3 calendar days |
| BR-09 | A copy On hold can only be checked out to the member it is held for | — |
| BR-10 | Maximum active reservations (Waiting or Ready for pickup) per member | 3 |
| BR-11 | ISBN format: 13 digits after removing hyphens and spaces; check digit valid (weights 1 and 3 alternating, weighted sum divisible by 10) | — |
| BR-12 | Allowed publication year **of this edition** (not of the original work) | 1800 to the current year |
| BR-13 | Minimum password length | 8 characters |
| BR-14 | Money is stored and calculated as whole qəpik (integers) and shown as AZN with 2 decimals | — |

## 8. Assumptions

The topic description is brief; where it was vague, the following decisions were made.

| ID | Assumption | Justification |
|---|---|---|
| A-01 | The library has one site, one time zone (Asia/Baku) and one circulation desk. | "Community library" suggests a single small site; multiple branches are excluded (W-04). |
| A-02 | Fines count calendar days, including weekends and public holidays. | Matches the current paper practice and keeps the rule simple; to be confirmed (OI-01). |
| A-03 | All librarians have the same permissions; there is no separate administrator role. The first librarian account is created with a setup command. | A small library has 1–3 staff members who all do the same work. |
| A-04 | Only librarians create member accounts. | Identity is checked at the desk (W-05). |
| A-05 | There is no background scheduler. Hold expiry (FR-15) is evaluated before every circulation action and when the librarian dashboard is opened. | Expiry only matters when someone acts on a copy, so evaluating it on demand gives the same result as a nightly job with less infrastructure. |
| A-06 | A title can be reserved only when none of its copies is Available. | If a copy is on the shelf, the member can simply borrow it; this keeps queues short. Koha allows more (see Appendix A), which is not needed here. |
| A-07 | A renewal extends the loan from the current due date, not from the renewal date. | Members are not penalised for renewing early; the new due date is predictable. |
| A-08 | Fines are charged when the copy is returned. The fine accrued so far on an overdue loan is shown for information (FR-19) but is not part of the balance. | An overdue loan already blocks borrowing (BR-06), so counting it twice is unnecessary. |
| A-09 | Copy codes are typed in by the librarian. | Barcode hardware is out of scope (W-03). |
| A-10 | The system reads "today" from one clock component that tests can replace. | Date rules (due dates, fines, holds) must be testable at exact boundaries. |
| A-11 | The user interface is in English. | Matches the language of the course documents. |

## 9. Constraints

| ID | Constraint |
|---|---|
| C-01 | Implementation in Python 3.12 with Flask, Jinja templates and SQLite (standard `sqlite3` module). |
| C-02 | One developer; deadline 02.12.2026. |
| C-03 | No budget: only free and open-source tools. |
| C-04 | The system runs locally on one computer; no hosting or internet connection is needed. |
| C-05 | Repository layout `docs/`, `src/`, `tests/`; documents submitted as PDF; Git with a meaningful history. |

## 10. Open issues

| ID | Issue | Owner | Current handling |
|---|---|---|---|
| OI-01 | Should days when the library is closed be excluded from fines? | Library manager | Calendar days (A-02). |
| OI-02 | What replacement fee applies to a lost copy? | Library manager | Entered manually by the librarian (FR-21, Could). |
| OI-03 | Do children need different loan limits (member categories, as in Koha)? | Library manager | One category for all members. |
| OI-04 | How long must loan history be kept for privacy reasons? | Library manager | Kept indefinitely in this release. |
| OI-05 | The course brief refers to a change-request section and an AI-use section that are not in the handout ("Section ??"). | Course instructor | Change request handled in a separate document; AI use described in the reflection. |

## Appendix A — Analysis of existing systems

Two existing systems were studied from their public documentation to collect requirements and to check
the decisions above.

### A.1 Koha (open-source integrated library system)
Koha is a full library system used by thousands of libraries. Its circulation is driven by a **circulation
and fine rules matrix**: for each combination of library, patron category and item type it defines the loan
period, the number of renewals allowed, the fine per day and a maximum fine. A system preference
(`noissuescharge`) blocks checkouts once a patron owes more than a set amount, and another
(`ReservesMaxPickUpDelay`) sets how many days a hold waits on the shelf before it expires.

**What we learned and used:**
- Lending parameters belong in rules, not in code → business rules table (Section 7) kept in one configuration module.
- Blocking by outstanding balance → BR-05 and FR-09 AC4.
- Fine per day with a cap → BR-07 and FR-12.
- Holds that expire after a pickup period → BR-08 and FR-15.
- Renewal limits shared by all renewals → BR-03.
- **Rejected for this project:** the full rule matrix per patron category and item type, multiple branches, and reservations while copies are on the shelf. They add configuration effort that a single small library does not need (A-01, A-06, OI-03).

### A.2 Libib (cloud cataloguing and lending service)
Libib is a lightweight web and mobile service aimed at small libraries such as schools and churches. Lending
is part of the paid Pro tier. The owner sets one default loan period in days, and staff can override a due
date. The checkout list shows the soonest-due items first and marks overdue items in red. Staff can place
holds for patrons, patrons can place holds from the published library page, and patrons can log in to see
their lending history and active holds. Libib also sends e-mail reminders and offers a self-checkout kiosk.

**What we learned and used:**
- One simple loan period suits a small library better than a complex matrix → BR-01.
- Overdue items should stand out → FR-19 overdue list, sorted by days late.
- Members want to see their own loans and holds → FR-17 member account page.
- Staff place holds on behalf of patrons → FR-13 allows the librarian to reserve for a member.
- **Rejected for this project:** e-mail reminders and self-checkout kiosk (W-02, W-03), because they need a mail service and barcode hardware.

### A.3 Sources
- Koha circulation and fine rules (ByWater Solutions knowledge base): https://help.bywatersolutions.com/portal/en/kb/articles/circulation-and-fine-rule-matrix
- Koha renewals: https://help.bywatersolutions.com/portal/en/kb/articles/renewals
- Koha bug 40913 (ReservesMaxPickUpDelay): https://lists.koha-community.org/archives/list/koha-bugs@lists.koha-community.org/thread/QLX4FBSDPC7KTPKMX2RPXISILWYH3UCX/
- Libib lending overview: https://support.libib.com/?p=267
- Libib Pro: https://support.libib.com/getting-started/get-libib-pro.html
- Libib holds: https://support.libib.com/tags/holds

