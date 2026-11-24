"""TC-ISBN-01..07: ISBN-13 validation (FR-03 AC2, BR-11). Technique: EP + BVA."""
import pytest

from library.services.catalogue import is_valid_isbn, normalize_isbn


@pytest.mark.parametrize(
    "isbn, valid",
    [
        pytest.param("9780306406157", True, id="TC_ISBN_01_valid"),
        pytest.param("978-0-306-40615-7", True, id="TC_ISBN_02_valid_with_hyphens"),
        pytest.param("9780306406158", False, id="TC_ISBN_03_wrong_check_digit"),
        pytest.param("978030640615", False, id="TC_ISBN_04_12_digits"),
        pytest.param("97803064061570", False, id="TC_ISBN_05_14_digits"),
        pytest.param("978030640615X", False, id="TC_ISBN_06_letter"),
        pytest.param("", False, id="TC_ISBN_07_empty"),
    ],
)
def test_TC_ISBN_is_valid_isbn(isbn, valid):
    assert is_valid_isbn(isbn) is valid


def test_normalize_isbn_removes_hyphens_and_spaces():
    assert normalize_isbn(" 978-0 306-40615-7 ") == "9780306406157"
