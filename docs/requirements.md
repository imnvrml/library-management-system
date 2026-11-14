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

