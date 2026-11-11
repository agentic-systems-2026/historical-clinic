"""Unit tests for the Select theme and Select query disposable components."""
import pytest

from components.select_query import select_query
from components.select_theme import select_theme

SELECTORS = [select_theme, select_query]


@pytest.mark.parametrize("select", SELECTORS)
def test_returns_highest_scoring(select):
    assert select(["a", "b", "c"], [0.1, 0.9, 0.5], set()) == "b"


@pytest.mark.parametrize("select", SELECTORS)
def test_skips_rejected(select):
    assert select(["a", "b", "c"], [0.1, 0.9, 0.5], {"b"}) == "c"


@pytest.mark.parametrize("select", SELECTORS)
def test_all_rejected_returns_none(select):
    assert select(["a", "b"], [0.1, 0.9], {"a", "b"}) is None


@pytest.mark.parametrize("select", SELECTORS)
def test_empty_candidates_returns_none(select):
    assert select([], [], set()) is None


@pytest.mark.parametrize("select", SELECTORS)
def test_tie_goes_to_first_listed(select):
    assert select(["a", "b"], [0.5, 0.5], set()) == "a"


@pytest.mark.parametrize("select", SELECTORS)
def test_negative_scores_still_select(select):
    assert select(["a", "b"], [-0.4, -0.2], set()) == "b"


@pytest.mark.parametrize("select", SELECTORS)
def test_mismatched_lengths_raise(select):
    with pytest.raises(ValueError):
        select(["a", "b"], [0.5], set())
