"""Unit tests for the Look up answer disposable component."""
import json
from pathlib import Path

import pytest

from components.look_up_answer import FALLBACK, look_up_answer

DATA = Path(__file__).resolve().parent.parent / "data"
RESPONSES = json.loads((DATA / "verified_responses.json").read_text(encoding="utf-8"))
THEMES = json.loads((DATA / "verified_themes.json").read_text(encoding="utf-8"))

TOY = [{
    "name": "Galen of Pergamon", "year_of_birth": 129,
    "matching_queries": ["Query A", "Query B"],
    "matching_responses": ["Answer A", "Answer B"],
}]


def test_exact_match_returns_attributed_answer():
    assert look_up_answer("Query B", TOY) == "Our physician, Galen of Pergamon, b. 129, recommends: Answer B"


def test_surrounding_whitespace_is_ignored():
    assert look_up_answer("  Query A ", TOY).endswith("Answer A")


def test_no_match_returns_fallback():
    assert look_up_answer("Query C", TOY) == FALLBACK


def test_near_match_is_not_a_match():
    assert look_up_answer("query a", TOY) == FALLBACK


def test_none_returns_fallback():
    assert look_up_answer(None, TOY) == FALLBACK


def test_missing_response_returns_fallback():
    broken = [{"name": "X", "year_of_birth": 1, "matching_queries": ["Q"], "matching_responses": []}]
    assert look_up_answer("Q", broken) == FALLBACK


def test_non_string_raises():
    with pytest.raises(ValueError):
        look_up_answer(42, TOY)


def test_every_verified_query_has_an_answer():
    """Data check: each query in verified_themes.json has a verified response."""
    for queries in THEMES.values():
        for query in queries:
            assert look_up_answer(query, RESPONSES) != FALLBACK, query
