"""Run the whole automated test suite with coverage in one command:

    python run_tests.py            # all tests
    python run_tests.py -k CHK     # extra arguments are passed to pytest

The HTML coverage report is written to htmlcov/index.html.
"""
import sys

import pytest

if __name__ == "__main__":
    sys.exit(pytest.main([
        "--cov=library",
        "--cov-report=term-missing",
        "--cov-report=html",
        *sys.argv[1:],
    ]))
