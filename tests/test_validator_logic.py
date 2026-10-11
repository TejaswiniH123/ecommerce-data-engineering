
import logging

import pytest

from src.validate_data import run_check


class FakeCursor:
    """Simulates the small part of a database cursor used by run_check."""

    def __init__(self, result):
        self.result = result
        self.executed_query = None

    def execute(self, query):
        self.executed_query = query

    def fetchone(self):
        return (self.result,)


def test_zero_findings_pass(caplog):
    cursor = FakeCursor(0)

    with caplog.at_level(logging.INFO):
        result = run_check(
            cursor,
            "Invalid review scores",
            "SELECT COUNT(*) FROM reviews",
            should_fail=True,
        )

    assert result is True
    assert "PASS: Invalid review scores" in caplog.text


def test_warning_check_with_findings(caplog):
    cursor = FakeCursor(775)

    with caplog.at_level(logging.WARNING):
        result = run_check(
            cursor,
            "Orders without items",
            "SELECT COUNT(*) FROM orders",
            should_fail=False,
        )

    assert result is True
    assert "Found: 775" in caplog.text


def test_critical_check_with_findings_fails(caplog):
    cursor = FakeCursor(3)

    with caplog.at_level(logging.ERROR):
        result = run_check(
            cursor,
            "Orders without customers",
            "SELECT COUNT(*) FROM orders",
            should_fail=True,
        )

    assert result is False
    assert "FAIL:" in caplog.text
    assert "Found: 3" in caplog.text


def test_query_is_executed():
    cursor = FakeCursor(0)
    query = "SELECT COUNT(*) FROM reviews"

    run_check(
        cursor,
        "Review check",
        query,
        should_fail=True,
    )

    assert cursor.executed_query == query
