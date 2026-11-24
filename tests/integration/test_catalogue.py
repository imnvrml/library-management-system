"""Catalogue and search integration tests: TC-CAT-01..10, 12, 13 and TC-SRC-01..03, 05, 06 (FR-03 to FR-06)."""
import pytest

from helpers import CLEAN_CODE, DUNE, DUNE_MESSIAH, add_copies, add_title
from library.domain import CopyStatus
from library.errors import BusinessRuleError


def test_TC_CAT_01_add_valid_title(svc):
    add_title(svc)
    found = svc.catalogue.titles.find_by_isbn(DUNE)
    assert found.title == "Dune" and found.pub_year == 1990


def test_TC_CAT_02_duplicate_isbn(svc):
    add_title(svc)
    with pytest.raises(BusinessRuleError, match="ISBN already exists"):
        add_title(svc, title="Another Dune")


@pytest.mark.parametrize("year", [pytest.param(1799, id="TC_CAT_03_1799"), pytest.param(2027, id="TC_CAT_06_2027")])
def test_TC_CAT_year_outside_range_rejected(svc, year):
    with pytest.raises(BusinessRuleError, match="year"):
        add_title(svc, year=year)


@pytest.mark.parametrize("year", [pytest.param(1800, id="TC_CAT_04_1800"), pytest.param(2026, id="TC_CAT_05_2026")])
def test_TC_CAT_year_inside_range_accepted(svc, year):
    assert add_title(svc, year=year).pub_year == year


def test_TC_CAT_07_empty_title(svc):
    with pytest.raises(BusinessRuleError, match="Title"):
        add_title(svc, title="  ")


def test_TC_CAT_08_empty_author(svc):
    with pytest.raises(BusinessRuleError, match="Author"):
        add_title(svc, author="")


def test_add_title_rejects_invalid_isbn(svc):
    with pytest.raises(BusinessRuleError, match="Invalid ISBN"):
        add_title(svc, isbn="9780441172710")


def test_TC_CAT_09_add_copy_is_available(svc):
    dune = add_title(svc)
    assert svc.catalogue.search("dune")[0].available == 0
    (copy,) = add_copies(svc, dune, "C-001")
    assert copy.status == CopyStatus.AVAILABLE
    assert svc.catalogue.search("dune")[0].available == 1


def test_TC_CAT_10_duplicate_copy_code(svc):
    dune = add_title(svc)
    add_copies(svc, dune, "C-001")
    with pytest.raises(BusinessRuleError, match="Copy code already exists"):
        add_copies(svc, dune, "C-001")


def test_TC_CAT_12_withdraw_available_copy(svc):
    dune = add_title(svc)
    (copy,) = add_copies(svc, dune, "C-001")
    assert svc.catalogue.withdraw_copy(copy.id).status == CopyStatus.WITHDRAWN
    summary = svc.catalogue.search("dune")[0]
    assert (summary.available, summary.total) == (0, 0)


def test_TC_CAT_13_withdraw_copy_on_loan(svc):
    dune = add_title(svc)
    (copy,) = add_copies(svc, dune, "C-001")
    svc.catalogue.copies.set_status(copy.id, CopyStatus.ON_LOAN)
    with pytest.raises(BusinessRuleError, match="Copy is not on the shelf"):
        svc.catalogue.withdraw_copy(copy.id)


@pytest.fixture
def three_titles(svc):
    add_title(svc, DUNE, "Dune", "Frank Herbert", 1990)
    add_title(svc, DUNE_MESSIAH, "Dune Messiah", "Frank Herbert", 1987)
    add_title(svc, CLEAN_CODE, "Clean Code", "Robert C. Martin", 2008)


def titles_of(results):
    return [r.title for r in results]


def test_TC_SRC_01_search_by_title_case_insensitive(svc, three_titles):
    assert titles_of(svc.catalogue.search("dune")) == ["Dune", "Dune Messiah"]


def test_TC_SRC_02_search_by_author(svc, three_titles):
    assert titles_of(svc.catalogue.search("herbert")) == ["Dune", "Dune Messiah"]


def test_TC_SRC_03_search_by_isbn(svc, three_titles):
    assert titles_of(svc.catalogue.search(CLEAN_CODE)) == ["Clean Code"]


def test_TC_SRC_05_available_of_total(svc):
    dune = add_title(svc)
    first, _, _ = add_copies(svc, dune, "C-001", "C-002", "C-003")
    svc.catalogue.copies.set_status(first.id, CopyStatus.ON_LOAN)
    summary = svc.catalogue.search("dune")[0]
    assert (summary.available, summary.total) == (2, 3)


def test_TC_SRC_06_empty_search_lists_all_alphabetically(svc, three_titles):
    assert titles_of(svc.catalogue.search("")) == ["Clean Code", "Dune", "Dune Messiah"]


def test_search_with_no_match_returns_empty_list(svc, three_titles):
    assert svc.catalogue.search("zzz") == []
