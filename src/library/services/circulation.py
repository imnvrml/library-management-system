"""CirculationService (FR-09 to FR-12, FR-19): checkout, return, renewal and the overdue list."""
from dataclasses import dataclass
from datetime import timedelta

from library.clock import Clock
from library.db import Database
from library.domain import CopyStatus, Loan, MemberFacts, Role, User
from library.errors import AccessDeniedError, BusinessRuleError
from library.repositories import CopyRepository, LoanRepository, TitleRepository, UserRepository
from library.rules import Rules
from library.services.members import MemberService
from library.services.policies import EligibilityPolicy, FinePolicy
from library.services.reservations import ReservationService


@dataclass
class OverdueLoan:
    loan: Loan
    member_name: str
    title: str
    copy_code: str
    days_late: int
    fine_so_far_qepik: int


class CirculationService:
    def __init__(self, db: Database, copies: CopyRepository, loans: LoanRepository, users: UserRepository,
                 titles: TitleRepository, members: MemberService, queue: ReservationService, fines: FinePolicy,
                 policy: EligibilityPolicy, clock: Clock, rules: Rules):
        self.db, self.copies, self.loans, self.users, self.titles = db, copies, loans, users, titles
        self.members, self.queue, self.fines, self.policy = members, queue, fines, policy
        self.clock, self.rules = clock, rules

    def checkout(self, member_id: int, copy_code: str) -> Loan:
        """FR-09 (UC-05, SD-01)."""
        with self.db.transaction():
            self.queue.expire_holds()
            today = self.clock.today()
            member = self.users.get(member_id)
            if member is None or member.role != Role.MEMBER:
                raise BusinessRuleError("Member not found")
            copy = self.copies.find_by_code(copy_code or "")
            if copy is None:
                raise BusinessRuleError("Copy not found")
            open_loans = self.loans.open_loans_of(member_id)
            facts = MemberFacts(
                is_active=member.is_active,
                active_loans=len(open_loans),
                has_overdue=any(loan.is_overdue(today) for loan in open_loans),
                balance_qepik=self.members.balance(member_id),
            )
            held_for_member = copy.status == CopyStatus.ON_HOLD and self.queue.holder_of(copy) == member_id
            refusal = self.policy.checkout_refusal(facts, copy.status, held_for_member)
            if refusal:
                raise BusinessRuleError(refusal)
            if held_for_member:
                self.queue.fulfil_hold(copy, member_id)
            loan = self.loans.add(Loan(None, copy.id, member_id, today, today + timedelta(days=self.rules.loan_days)))
            self.copies.set_status(copy.id, CopyStatus.ON_LOAN)
            return loan

    def return_copy(self, copy_code: str) -> Loan:
        """FR-10, FR-12, FR-14 (UC-06, SD-02)."""
        with self.db.transaction():
            self.queue.expire_holds()
            today = self.clock.today()
            copy = self.copies.find_by_code(copy_code or "")
            if copy is None:
                raise BusinessRuleError("Copy not found")
            loan = self.loans.open_loan_for_copy(copy.id)
            if loan is None:
                raise BusinessRuleError("Copy is not on loan")
            loan.return_date = today
            loan.fine_qepik = self.fines.fine_for(loan.due_date, today)
            self.loans.update(loan)
            self.queue.serve_queue(copy)
            return loan

    def renew(self, loan_id: int, actor: User) -> Loan:
        """FR-11 (UC-07, SD-03)."""
        with self.db.transaction():
            self.queue.expire_holds()
            loan = self.loans.get(loan_id)
            if loan is None or loan.return_date is not None:
                raise BusinessRuleError("Loan not found or already returned")
            if actor.role == Role.MEMBER and loan.member_id != actor.id:
                raise AccessDeniedError()
            copy = self.copies.get(loan.copy_id)
            reserved = self.queue.has_waiting(copy.title_id, exclude_member_id=loan.member_id)
            refusal = self.policy.renew_refusal(loan, self.clock.today(), reserved)
            if refusal:
                raise BusinessRuleError(refusal)
            loan.due_date += timedelta(days=self.rules.loan_days)
            loan.renewal_count += 1
            self.loans.update(loan)
            return loan

    def overdue_loans(self) -> list[OverdueLoan]:
        """FR-19: most days late first, with the fine accrued so far."""
        today = self.clock.today()
        rows = []
        for loan in self.loans.overdue(today):
            copy = self.copies.get(loan.copy_id)
            rows.append(OverdueLoan(
                loan, self.users.get(loan.member_id).full_name, self.titles.get(copy.title_id).title, copy.code,
                (today - loan.due_date).days, self.fines.fine_for(loan.due_date, today),
            ))
        return sorted(rows, key=lambda r: (-r.days_late, r.copy_code))
