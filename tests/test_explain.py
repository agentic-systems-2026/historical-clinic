"""Unit tests for the Explain theme and Explain query disposable components.

A fake `generate` stands in for Gemma, so these run without Ollama.
"""
import pytest

from components import gemma
from components.explain_query import explain_query
from components.explain_theme import explain_theme

EXPLAINERS = [explain_theme, explain_query]


def fake(reply):
    calls = []

    def generate(prompt):
        calls.append(prompt)
        return reply

    generate.calls = calls
    return generate


@pytest.mark.parametrize("explain", EXPLAINERS)
def test_prompt_contains_query_and_candidate(explain):
    generate = fake("We think this might be a fit because it does.")
    explain("my ankle hurts", "Musculoskeletal health", generate=generate)
    assert len(generate.calls) == 1
    assert "my ankle hurts" in generate.calls[0]
    assert "Musculoskeletal health" in generate.calls[0]
    assert "We think this might be a fit because" in generate.calls[0]


@pytest.mark.parametrize("explain", EXPLAINERS)
def test_returns_reply_text(explain):
    reply = "We think this might be a fit because ankles are joints."
    assert explain("q", "c", generate=fake(reply)) == reply


@pytest.mark.parametrize("explain", EXPLAINERS)
def test_long_reply_trimmed_to_three_sentences(explain):
    reply = "One. Two. Three. Four. Five."
    assert explain("q", "c", generate=fake(reply)) == "One. Two. Three."


@pytest.mark.parametrize("explain", EXPLAINERS)
def test_whitespace_is_collapsed(explain):
    assert explain("q", "c", generate=fake("  A\n\nreply.  ")) == "A reply."


@pytest.mark.parametrize("explain", EXPLAINERS)
@pytest.mark.parametrize("reply", ["", "   ", None])
def test_empty_reply_gives_fallback(explain, reply):
    assert explain("q", "c", generate=fake(reply)) == gemma.FALLBACK_REPLY


@pytest.mark.parametrize("explain", EXPLAINERS)
def test_braces_in_patient_text_are_safe(explain):
    generate = fake("ok.")
    explain("my {weird} query", "c", generate=generate)
    assert "my {weird} query" in generate.calls[0]


@pytest.mark.parametrize("explain", EXPLAINERS)
@pytest.mark.parametrize("bad", [None, 42])
def test_non_string_input_raises(explain, bad):
    with pytest.raises(ValueError):
        explain(bad, "c", generate=fake("ok."))


@pytest.mark.parametrize("explain", EXPLAINERS)
def test_stub_mode_needs_no_server(explain, monkeypatch):
    monkeypatch.setenv("HC_LLM", "stub")
    assert explain("q", "c") == gemma.STUB_REPLY
