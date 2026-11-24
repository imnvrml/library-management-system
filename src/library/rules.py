"""Business-rule values (requirements section 7). Changing a value here changes the rule everywhere."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Rules:
    loan_days: int = 14                # BR-01
    max_loans: int = 5                 # BR-02
    max_renewals: int = 2              # BR-03
    borrow_threshold_qepik: int = 500  # BR-05 (refused when balance is greater)
    fine_per_day_qepik: int = 20       # BR-07
    max_fine_qepik: int = 1000         # BR-07
    pickup_days: int = 3               # BR-08
    max_reservations: int = 3          # BR-10
    min_year: int = 1800               # BR-12
    min_password_len: int = 8          # BR-13
