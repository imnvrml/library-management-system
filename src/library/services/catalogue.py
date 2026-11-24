"""Catalogue: ISBN rules (BR-11) and CatalogueService (FR-03 to FR-06)."""


def normalize_isbn(isbn: str) -> str:
    return isbn.replace("-", "").replace(" ", "").strip()


def is_valid_isbn(isbn: str) -> bool:
    """BR-11: 13 digits after removing hyphens/spaces, weights 1 and 3, weighted sum divisible by 10."""
    digits = normalize_isbn(isbn)
    if len(digits) != 13 or not digits.isdigit():
        return False
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(digits))
    return total % 10 == 0
