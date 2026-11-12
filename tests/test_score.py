"""Unit tests for the "Score" atomic protocol (Sentence-BERT, all-MiniLM-L6-v2).

Contract (from our wire diagram): query (str), candidates (list[str]) ->
cosine similarity scores (list[float], one per candidate, same order).
Used twice in the workflow: Score themes and Score queries.
Sentence-BERT is the citable source (Reimers & Gurevych, EMNLP 2019); we test
the exact call our glue makes. Tested with sentence-transformers==6.2.0 and
the model revision pinned below.
"""
import pytest
from sentence_transformers import SentenceTransformer, util

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "8b3219a92973c328a8e22fadcfa821b5dc75636a"
encoder = SentenceTransformer(MODEL_NAME, revision=MODEL_REVISION)


def score(query, candidates):
    """The same calls the glue makes; not new protocol code."""
    query_embedding = encoder.encode(query, convert_to_tensor=True)
    candidate_embeddings = encoder.encode(candidates, convert_to_tensor=True)
    return util.cos_sim(query_embedding, candidate_embeddings)[0].tolist()


THEMES = ["Dermatology & Skin Conditions", "Gastrointestinal & Digestive Health", "Mental Health"]

# ---------- Typical inputs ----------

def test_one_float_per_candidate_in_order():
    scores = score("I have an itchy rash", THEMES)
    assert len(scores) == len(THEMES)
    assert all(isinstance(s, float) for s in scores)


def test_scores_are_cosine_similarities():
    for s in score("I have an itchy rash", THEMES):
        assert -1.0 - 1e-6 <= s <= 1.0 + 1e-6


def test_related_scores_higher_than_unrelated():
    rash, stomach, _ = score("I have an itchy red rash on my arm", THEMES)
    assert rash > stomach


def test_paraphrase_scores_higher_than_unrelated():
    paraphrase, unrelated = score("My head is pounding", ["I have a bad headache", "I need to renew my passport"])
    assert paraphrase > unrelated


def test_identical_text_scores_one():
    text = "My skin has developed intensely itchy, dry, red, and cracked patches."
    assert score(text, [text, "Something else entirely."])[0] == pytest.approx(1.0, abs=1e-4)


def test_repeated_calls_agree():
    assert score("chest pain", THEMES) == pytest.approx(score("chest pain", THEMES), abs=1e-6)

# ---------- Edge cases ----------

def test_single_candidate():
    assert len(score("rash", ["Dermatology"])) == 1


def test_empty_query_still_scores():
    assert len(score("", THEMES)) == len(THEMES)


def test_text_beyond_max_length_is_ignored():
    """Known behavior: inputs are truncated at the model's maximum sequence
    length (256 word pieces), so text after that point does not change scores."""
    long_query = "I have an itchy rash on my arm. " * 60
    assert score(long_query + "Also my stomach hurts badly.", THEMES) == pytest.approx(score(long_query, THEMES), abs=1e-5)

# ---------- Invalid inputs ----------

@pytest.mark.parametrize("bad_query", [None, 42])
def test_non_string_query_raises(bad_query):
    with pytest.raises((TypeError, ValueError)):
        score(bad_query, THEMES)
