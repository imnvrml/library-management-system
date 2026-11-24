"""Use-case-based system tests and pages: TC-UC05..08, TC-SRC-04, TC-ACCT-01..02 (test plan 3.4, 4.9, 4.10)."""
from datetime import date

from helpers import CSRF, login, post


def test_TC_UC05_01_checkout_main_flow(client, data):
    login(client, "lib@example.com")
    page = post(client, "/circulation/checkout", member_email="ann@example.com", copy_code="C-001")
    assert b"due 2026-12-15" in page.data


def test_TC_UC05_02_checkout_loan_limit(client, svc, data):
    for code in ("X-1", "X-2", "X-3", "X-4", "X-5"):
        svc.catalogue.add_copy(data["dune"].id, code)
        svc.circulation.checkout(data["ann"].id, code)
    login(client, "lib@example.com")
    page = post(client, "/circulation/checkout", member_email="ann@example.com", copy_code="C-001")
    assert b"Loan limit reached (5)" in page.data
    assert len(svc.loans.open_loans_of(data["ann"].id)) == 5


def test_TC_UC06_01_late_return_shows_fine(client, svc, app, data):
    clock = app.config["CLOCK"]
    clock.day = date(2026, 11, 13)
    svc.circulation.checkout(data["ann"].id, "C-001")  # due 11-27, returned 4 days late
    clock.day = date(2026, 12, 1)
    login(client, "lib@example.com")
    page = post(client, "/circulation/return", copy_code="C-001")
    assert b"Fine 0.80 AZN" in page.data


def test_TC_UC06_02_returned_copy_goes_on_hold(client, svc, data):
    svc.circulation.checkout(data["ann"].id, "C-001")
    svc.circulation.checkout(data["ann"].id, "C-002")
    svc.queue.place(data["ben"].id, data["dune"].id)
    login(client, "lib@example.com")
    page = post(client, "/circulation/return", copy_code="C-001")
    assert b"on hold for the next member" in page.data


def test_TC_UC07_01_member_renews_own_loan(client, svc, data):
    loan = svc.circulation.checkout(data["ann"].id, "C-001")
    login(client, "ann@example.com")
    page = post(client, f"/loans/{loan.id}/renew")
    assert b"New due date 2026-12-29" in page.data


def test_TC_UC07_02_member_renews_another_members_loan(client, svc, data):
    loan = svc.circulation.checkout(data["ben"].id, "C-001")
    login(client, "ann@example.com")
    assert client.post(f"/loans/{loan.id}/renew", data={"csrf_token": CSRF}).status_code == 403


def test_TC_UC08_01_member_reserves_and_sees_position(client, svc, data):
    svc.circulation.checkout(data["ben"].id, "C-001")
    svc.circulation.checkout(data["ben"].id, "C-002")
    login(client, "ann@example.com")
    page = post(client, f"/titles/{data['dune'].id}/reserve")
    assert b"position in the queue: 1" in page.data


def test_TC_UC08_02_reserve_refused_when_copy_on_shelf(client, data):
    login(client, "ann@example.com")
    page = post(client, f"/titles/{data['dune'].id}/reserve")
    assert "A copy is available — borrow it at the desk".encode() in page.data


def test_TC_SRC_04_search_without_result(client, data):
    login(client, "ann@example.com")
    assert b"No titles found" in client.get("/titles?q=zzz").data


def test_search_page_shows_available_of_total(client, svc, data):
    svc.circulation.checkout(data["ben"].id, "C-001")
    login(client, "ann@example.com")
    assert b"1 of 2 available" in client.get("/titles?q=dune").data


def test_TC_ACCT_01_account_page_shows_loans_and_balance(client, svc, app, data):
    clock = app.config["CLOCK"]
    clock.day = date(2026, 11, 13)
    svc.circulation.checkout(data["ann"].id, "C-001")
    clock.day = date(2026, 12, 1)
    svc.circulation.return_copy("C-001")               # 4 days late: fine 80
    svc.circulation.checkout(data["ann"].id, "C-001")
    svc.circulation.checkout(data["ann"].id, "C-002")
    login(client, "ann@example.com")
    page = client.get("/account").data
    assert page.count(b"2026-12-15") >= 2 and b"0.80 AZN" in page


def test_TC_ACCT_02_queue_position_without_other_names(client, svc, data):
    svc.circulation.checkout(data["ben"].id, "C-001")
    svc.circulation.checkout(data["ben"].id, "C-002")
    dan = svc.members.register("Dan Danov", "dan@example.com", None, "secret123")
    svc.queue.place(dan.id, data["dune"].id)            # Dan is first in the queue
    svc.queue.place(data["ann"].id, data["dune"].id)    # Ann is second
    login(client, "ann@example.com")
    page = client.get("/account").data
    assert b"position 2" in page
    assert b"Dan" not in page


def test_dashboard_lists_counts_and_forms(client, data):
    login(client, "lib@example.com")
    page = client.get("/dashboard").data
    assert b"Check out" in page and b"Return" in page


def test_librarian_adds_title_and_copy_through_forms(client, svc, data):
    login(client, "lib@example.com")
    page = post(client, "/titles", isbn="9780132350884", title="Clean Code", author="Robert C. Martin",
                publisher="Prentice Hall", year="2008")
    assert b"Clean Code" in page.data
    title = svc.titles.find_by_isbn("9780132350884")
    page = post(client, f"/titles/{title.id}/copies", code="CC-001")
    assert b"CC-001" in page.data


def test_librarian_registers_member_and_records_payment(client, svc, app, data):
    login(client, "lib@example.com")
    page = post(client, "/members", full_name="Dan Demo", email="dan@example.com", phone="", password="secret123")
    assert b"Dan Demo" in page.data
    clock = app.config["CLOCK"]
    clock.day = date(2026, 11, 13)
    svc.circulation.checkout(data["ann"].id, "C-001")
    clock.day = date(2026, 12, 1)
    svc.circulation.return_copy("C-001")               # fine 0.80 AZN
    page = post(client, f"/members/{data['ann'].id}/payments", amount="0.80")
    assert b"Payment recorded. New balance 0.00 AZN" in page.data   # D-08: check the success message


def test_overdue_page(client, svc, app, data):
    clock = app.config["CLOCK"]
    clock.day = date(2026, 11, 7)
    svc.circulation.checkout(data["ann"].id, "C-001")
    clock.day = date(2026, 12, 1)
    login(client, "lib@example.com")
    page = client.get("/circulation/overdue").data
    assert b"C-001" in page and b"10" in page and b"2.00 AZN" in page
