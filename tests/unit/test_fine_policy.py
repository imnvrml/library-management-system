"""TC-FINE-01..07: FinePolicy.fine_for (FR-12, BR-07). Technique: BVA + EP."""
from datetime import date, timedelta

import pytest

from library.services.policies import FinePolicy

DUE = date(2026, 12, 15)


@pytest.mark.parametrize(
    "days_late, expected_qepik",
    [
        pytest.param(-1, 0, id="TC_FINE_01_returned_early"),
        pytest.param(0, 0, id="TC_FINE_02_returned_on_due_date"),
        pytest.param(1, 20, id="TC_FINE_03_one_day_late"),
        pytest.param(49, 980, id="TC_FINE_04_49_days_below_cap"),
        pytest.param(50, 1000, id="TC_FINE_05_50_days_exactly_cap"),
        pytest.param(51, 1000, id="TC_FINE_06_51_days_capped"),
        pytest.param(365, 1000, id="TC_FINE_07_far_above_cap"),
    ],
)
def test_TC_FINE_fine_for_days_late(rules, days_late, expected_qepik):
    returned = DUE + timedelta(days=days_late)
    assert FinePolicy(rules).fine_for(DUE, returned) == expected_qepik
