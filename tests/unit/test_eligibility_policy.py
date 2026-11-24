"""EligibilityPolicy unit tests: decision tables DT-1, DT-2, DT-3 and payment boundaries (test plan 3.2)."""
from datetime import date

import pytest

from library.domain import CopyStatus, Loan, MemberFacts
from library.services.policies import EligibilityPolicy

TODAY = date(2026, 12, 1)
OK_MEMBER = MemberFacts(is_active=True, active_loans=0, has_overdue=False, balance_qepik=0)


@pytest.fixture
def policy(rules):
    return EligibilityPolicy(rules)


def member(**changes):
    values = {"is_active": True, "active_loans": 0, "has_overdue": False, "balance_qepik": 0, **changes}
    return MemberFacts(**values)


# ---------- DT-1 checkout (FR-09) ----------

def test_TC_CHK_01_eligible_member_available_copy(policy):
    assert policy.checkout_refusal(OK_MEMBER, CopyStatus.AVAILABLE, held_for_member=False) is None


def test_TC_CHK_02_inactive_member(policy):
    assert policy.checkout_refusal(member(is_active=False), CopyStatus.AVAILABLE, False) == "Account is deactivated"


def test_TC_CHK_03_loan_limit_reached(policy):
    assert policy.checkout_refusal(member(active_loans=5), CopyStatus.AVAILABLE, False) == "Loan limit reached (5)"


def test_TC_CHK_04_member_has_overdue_loan(policy):
    assert policy.checkout_refusal(member(has_overdue=True), CopyStatus.AVAILABLE, False) == "Member has overdue items"


def test_TC_CHK_05_balance_above_threshold(policy):
    assert (policy.checkout_refusal(member(balance_qepik=501), CopyStatus.AVAILABLE, False)
            == "Outstanding fines exceed 5.00 AZN")


def test_TC_CHK_06_copy_on_loan(policy):
    assert policy.checkout_refusal(OK_MEMBER, CopyStatus.ON_LOAN, False) == "Copy is not available"


def test_TC_CHK_07_copy_withdrawn(policy):
    assert policy.checkout_refusal(OK_MEMBER, CopyStatus.WITHDRAWN, False) == "Copy is not available"


def test_TC_CHK_08_copy_on_hold_for_another_member(policy):
    assert policy.checkout_refusal(OK_MEMBER, CopyStatus.ON_HOLD, held_for_member=False) == "Copy is held for another member"


def test_TC_CHK_09_copy_on_hold_for_this_member(policy):
    assert policy.checkout_refusal(OK_MEMBER, CopyStatus.ON_HOLD, held_for_member=True) is None


def test_TC_CHK_10_four_active_loans_allowed(policy):
    assert policy.checkout_refusal(member(active_loans=4), CopyStatus.AVAILABLE, False) is None


def test_TC_CHK_11_balance_exactly_threshold_allowed(policy):
    assert policy.checkout_refusal(member(balance_qepik=500), CopyStatus.AVAILABLE, False) is None


def test_TC_CHK_12_first_failing_rule_wins(policy):
    facts = member(is_active=False, active_loans=5)
    assert policy.checkout_refusal(facts, CopyStatus.ON_LOAN, False) == "Account is deactivated"


# ---------- DT-2 renewal (FR-11) ----------

def loan(due, renewals=0):
    return Loan(id=1, copy_id=1, member_id=1, checkout_date=date(2026, 11, 20), due_date=due, renewal_count=renewals)


def test_TC_REN_01_renewal_allowed(policy):
    assert policy.renew_refusal(loan(date(2026, 12, 15)), date(2026, 12, 10), reserved_by_other=False) is None


def test_TC_REN_02_one_previous_renewal_allowed(policy):
    assert policy.renew_refusal(loan(date(2026, 12, 15), renewals=1), TODAY, False) is None


def test_TC_REN_03_maximum_renewals_reached(policy):
    assert policy.renew_refusal(loan(date(2026, 12, 15), renewals=2), TODAY, False) == "Maximum renewals reached (2)"


def test_TC_REN_04_overdue_loan(policy):
    assert policy.renew_refusal(loan(date(2026, 11, 30)), TODAY, False) == "Overdue loans cannot be renewed"


def test_TC_REN_05_due_today_is_not_overdue(policy):
    assert policy.renew_refusal(loan(date(2026, 12, 1)), TODAY, False) is None


def test_TC_REN_06_reserved_by_another_member(policy):
    assert (policy.renew_refusal(loan(date(2026, 12, 15)), TODAY, reserved_by_other=True)
            == "Title is reserved by another member")


# ---------- DT-3 reservation (FR-13) ----------

def test_TC_RES_01_reservation_allowed(policy):
    assert policy.reservation_refusal(available=0, already_reserved=False, on_loan=False, active=0) is None


def test_TC_RES_02_copy_available(policy):
    assert (policy.reservation_refusal(available=1, already_reserved=False, on_loan=False, active=0)
            == "A copy is available — borrow it at the desk")


def test_TC_RES_03_already_reserved(policy):
    assert (policy.reservation_refusal(available=0, already_reserved=True, on_loan=False, active=1)
            == "You already reserved this title")


def test_TC_RES_04_title_on_loan_to_member(policy):
    assert (policy.reservation_refusal(available=0, already_reserved=False, on_loan=True, active=0)
            == "You already have this title on loan")


def test_TC_RES_05_reservation_limit_reached(policy):
    assert (policy.reservation_refusal(available=0, already_reserved=False, on_loan=False, active=3)
            == "Reservation limit reached (3)")


def test_TC_RES_06_two_active_reservations_allowed(policy):
    assert policy.reservation_refusal(available=0, already_reserved=False, on_loan=False, active=2) is None


# ---------- payment (FR-18), BVA ----------

@pytest.mark.parametrize(
    "amount, balance, expected",
    [
        pytest.param(60, 100, None, id="TC_PAY_01_partial_payment"),
        pytest.param(0, 100, "Amount must be positive", id="TC_PAY_02_zero"),
        pytest.param(101, 100, "Amount exceeds balance", id="TC_PAY_03_above_balance"),
        pytest.param(100, 100, None, id="TC_PAY_04_exactly_balance"),
        pytest.param(1, 100, None, id="TC_PAY_05_minimum"),
    ],
)
def test_TC_PAY_payment_refusal(policy, amount, balance, expected):
    assert policy.payment_refusal(amount, balance) == expected


def test_loan_is_overdue_only_after_due_date():
    assert loan(date(2026, 11, 30)).is_overdue(TODAY)
    assert not loan(date(2026, 12, 1)).is_overdue(TODAY)
