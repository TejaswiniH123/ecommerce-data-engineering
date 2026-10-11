
import pytest
from decimal import Decimal

def is_valid_review_score(score):
    """A review score must be an integer from 1 to 5."""
    return (
        isinstance(score, int)
        and not isinstance(score, bool)
        and 1 <= score <= 5
    )


def is_valid_non_negative_amount(amount):
    """An amount must be numeric, finite, and non-negative."""
    import math
    from decimal import Decimal

    if isinstance(amount, bool):
        return False

    if not isinstance(amount, (int, float, Decimal)):
        return False

    try:
        return math.isfinite(amount) and amount >= 0
    except (TypeError, ValueError, OverflowError):
        return False


@pytest.mark.parametrize(
    "score",
    [1, 2, 3, 4, 5],
)
def test_valid_review_scores(score):
    assert is_valid_review_score(score)


@pytest.mark.parametrize(
    "score",
    [0, 6, -1, None, 2.5, "5", True],
)
def test_invalid_review_scores(score):
    assert not is_valid_review_score(score)


@pytest.mark.parametrize(
    "amount",
    [0, 10, 99.99, Decimal("12.50")],
)
def test_valid_amounts(amount):
    assert is_valid_non_negative_amount(amount)


@pytest.mark.parametrize(
    "amount",
    [-1, Decimal("-0.01"), None, "10", float("nan"), float("inf"), True],
)
def test_invalid_amounts(amount):
    assert not is_valid_non_negative_amount(amount)
