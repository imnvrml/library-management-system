"""MemberService (FR-07, FR-08, FR-17, FR-18)."""
from library.clock import Clock
from library.db import Database
from library.domain import Payment, Role, User
from library.errors import BusinessRuleError
from library.repositories import LoanRepository, PaymentRepository, UserRepository
from library.rules import Rules
from library.services.auth import AuthService
from library.services.policies import EligibilityPolicy


class MemberService:
    def __init__(self, db: Database, users: UserRepository, loans: LoanRepository, payments: PaymentRepository,
                 policy: EligibilityPolicy, clock: Clock, rules: Rules):
        self.db, self.users, self.loans, self.payments = db, users, loans, payments
        self.policy, self.clock, self.rules = policy, clock, rules

    def register(self, full_name: str, email: str, phone: str | None, password: str,
                 role: Role = Role.MEMBER) -> User:
        """FR-07. role=LIBRARIAN is only used by the setup command (assumption A-03)."""
        full_name, email = (full_name or "").strip(), (email or "").strip().lower()
        if not full_name:
            raise BusinessRuleError("Full name is required")
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise BusinessRuleError("Invalid e-mail")
        if len(password or "") < self.rules.min_password_len:
            raise BusinessRuleError("Password too short")
        with self.db.transaction():
            if self.users.find_by_email(email):
                raise BusinessRuleError("E-mail already registered")
            user = User(None, email, AuthService.hash_password(password), full_name, (phone or "").strip() or None,
                        role, True)
            return self.users.add(user, self.clock.now())

    def deactivate(self, member_id: int) -> User:
        """FR-08: only members without open loans and with a zero balance."""
        with self.db.transaction():
            member = self.users.get(member_id)
            if member is None or member.role != Role.MEMBER:
                raise BusinessRuleError("Member not found")
            if self.loans.open_loans_of(member_id):
                raise BusinessRuleError("Member has open loans")
            if self.balance(member_id) > 0:
                raise BusinessRuleError("Member has an outstanding balance")
            self.users.set_active(member_id, False)
            return self.users.get(member_id)

    def balance(self, member_id: int) -> int:
        """Fines charged minus payments, in qəpik. Calculated, never stored (models 4.3)."""
        return self.loans.total_fines(member_id) - self.payments.total_paid(member_id)

    def record_payment(self, member_id: int, amount_qepik: int, librarian_id: int) -> Payment:
        """FR-18."""
        with self.db.transaction():
            refusal = self.policy.payment_refusal(amount_qepik, self.balance(member_id))
            if refusal:
                raise BusinessRuleError(refusal)
            return self.payments.add(Payment(None, member_id, librarian_id, amount_qepik, self.clock.now()))
