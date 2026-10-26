"""Unit tests for the "De-identify" atomic protocol (Microsoft Presidio).

Contract (from our wire diagram): free text (str) -> redacted text (str).
Presidio is the citable source; we test the exact call our glue will make.
Tested with presidio-analyzer==2.2.364, presidio-anonymizer==2.2.364, en_core_web_lg 3.8.0.
"""
import pytest
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()


def deidentify(text):
    """The same two calls the glue makes; not new protocol code."""
    findings = analyzer.analyze(text=text, language="en")
    return anonymizer.anonymize(text=text, analyzer_results=findings).text


# ---------- Typical inputs ----------
def test_redacts_name_and_phone():
    out = deidentify("My name is Maria Lopez and my number is 212-555-0143.")
    assert "Maria Lopez" not in out
    assert "212-555-0143" not in out
    assert "<PERSON>" in out and "<PHONE_NUMBER>" in out


def test_returns_a_string():
    assert isinstance(deidentify("My name is Maria Lopez."), str)


def test_redacts_email():
    assert deidentify("Reach me at maria.lopez@example.com") == "Reach me at <EMAIL_ADDRESS>"


# ---------- Edge cases ----------
def test_empty_string_returns_empty_string():
    assert deidentify("") == ""


def test_lowercase_name_is_still_redacted():
    assert "maria lopez" not in deidentify("my name is maria lopez")


def test_long_input_is_fully_redacted():
    out = deidentify("Call 212-555-0143. " * 500)
    assert "212-555-0143" not in out


@pytest.mark.xfail(strict=True, reason="Known limitation: durations are redacted as DATE_TIME")
def test_symptom_duration_is_preserved():
    text = "I have had a headache for three days."
    assert deidentify(text) == text


@pytest.mark.xfail(strict=True, reason="Known limitation: ZIP code is not redacted")
def test_zip_code_is_redacted():
    assert "11201" not in deidentify("I live at 125 Main Street, Brooklyn, NY 11201")


# ---------- Invalid inputs ----------
@pytest.mark.parametrize("bad_input", [None, 42])
def test_non_string_input_raises(bad_input):
    with pytest.raises(ValueError):
        deidentify(bad_input)
