"""Service layer (models 5.1). build_services wires repositories and services together."""
from dataclasses import dataclass

from library.clock import Clock
from library.db import Database
from library.repositories import (
    CopyRepository, LoanRepository, PaymentRepository, ReservationRepository, TitleRepository, UserRepository,
)
from library.rules import Rules
from library.services.auth import AuthService
from library.services.catalogue import CatalogueService
from library.services.circulation import CirculationService
from library.services.members import MemberService
from library.services.policies import EligibilityPolicy, FinePolicy
from library.services.reservations import ReservationService


@dataclass
class Services:
    db: Database
    clock: Clock
    rules: Rules
    users: UserRepository
    titles: TitleRepository
    copies: CopyRepository
    loans: LoanRepository
    reservations: ReservationRepository
    payments: PaymentRepository
    fines: FinePolicy
    policy: EligibilityPolicy
    auth: AuthService
    catalogue: CatalogueService
    members: MemberService
    queue: ReservationService
    circulation: CirculationService


def build_services(db: Database, clock: Clock, rules: Rules) -> Services:
    users, titles, copies = UserRepository(db), TitleRepository(db), CopyRepository(db)
    loans, reservations, payments = LoanRepository(db), ReservationRepository(db), PaymentRepository(db)
    fines, policy = FinePolicy(rules), EligibilityPolicy(rules)
    members = MemberService(db, users, loans, payments, policy, clock, rules)
    queue = ReservationService(db, reservations, copies, loans, titles, policy, clock, rules)
    return Services(
        db=db, clock=clock, rules=rules,
        users=users, titles=titles, copies=copies, loans=loans, reservations=reservations, payments=payments,
        fines=fines, policy=policy,
        auth=AuthService(users),
        catalogue=CatalogueService(db, titles, copies, clock, rules, queue=queue),
        members=members,
        queue=queue,
        circulation=CirculationService(db, copies, loans, users, titles, members, queue, fines, policy, clock, rules),
    )
