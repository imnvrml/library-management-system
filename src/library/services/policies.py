"""Policy objects (models 5.1): business decisions as pure functions, without database or web.

Each *_refusal method returns None when the action is allowed, or the message of the first rule that
fails. The order of the checks is the order of the decision tables in docs/test-plan.md section 3.2.
"""
from datetime import date

from library.domain import CopyStatus, Loan, MemberFacts, azn
from library.rules import Rules


class FinePolicy:
    def __init__(self, rules: Rules):
        self.rules = rules

    def fine_for(self, due: date, returned: date) -> int:
        """FR-12: no fine within the grace period (BR-15); after it every day late counts, capped (BR-07)."""
        days_late = (returned - due).days
        if days_late <= self.rules.grace_days:
            return 0
        return min(days_late * self.rules.fine_per_day_qepik, self.rules.max_fine_qepik)


class EligibilityPolicy:
    def __init__(self, rules: Rules):
        self.rules = rules

    def checkout_refusal(self, member: MemberFacts, copy_status: CopyStatus, held_for_member: bool) -> str | None:
        """DT-1 (FR-09). held_for_member: the copy is On hold for this borrower."""
        r = self.rules
        if not member.is_active:
            return "Account is deactivated"
        if member.active_loans >= r.max_loans:
            return f"Loan limit reached ({r.max_loans})"
        if member.has_overdue:
            return "Member has overdue items"
        if member.balance_qepik > r.borrow_threshold_qepik:
            return f"Outstanding fines exceed {azn(r.borrow_threshold_qepik)}"
        if copy_status == CopyStatus.ON_HOLD and not held_for_member:
            return "Copy is held for another member"
        if copy_status not in (CopyStatus.AVAILABLE, CopyStatus.ON_HOLD):
            return "Copy is not available"
        return None

    def renew_refusal(self, loan: Loan, today: date, reserved_by_other: bool) -> str | None:
        """DT-2 (FR-11)."""
        if loan.renewal_count >= self.rules.max_renewals:
            return f"Maximum renewals reached ({self.rules.max_renewals})"
        if loan.is_overdue(today):
            return "Overdue loans cannot be renewed"
        if reserved_by_other:
            return "Title is reserved by another member"
        return None

    def reservation_refusal(self, available: int, already_reserved: bool, on_loan: bool, active: int) -> str | None:
        """DT-3 (FR-13)."""
        if available > 0:
            return "A copy is available — borrow it at the desk"
        if already_reserved:
            return "You already reserved this title"
        if on_loan:
            return "You already have this title on loan"
        if active >= self.rules.max_reservations:
            return f"Reservation limit reached ({self.rules.max_reservations})"
        return None

    def payment_refusal(self, amount_qepik: int, balance_qepik: int) -> str | None:
        """FR-18: a payment must be positive and must not exceed the balance."""
        if amount_qepik <= 0:
            return "Amount must be positive"
        if amount_qepik > balance_qepik:
            return "Amount exceeds balance"
        return None
