"""Unit tests for the Export audit log disposable component."""
import pytest

from components.export_audit_log import export_audit_log

LOG = [
    ("Clinic", "Welcome."),
    ("Patient", "My name is <PERSON>."),
    ("Clinic", "[Theme scores] Dermatology: 0.512"),
    ("Clinic", "Our physician recommends rest & fluids."),
]


def test_writes_one_html_file(tmp_path):
    path = export_audit_log(LOG, tmp_path)
    assert path.exists() and path.suffix == ".html"
    assert list(tmp_path.iterdir()) == [path]


def test_every_entry_appears_escaped(tmp_path):
    text = export_audit_log(LOG, tmp_path).read_text(encoding="utf-8")
    assert "Welcome." in text
    assert "My name is &lt;PERSON&gt;." in text
    assert "rest &amp; fluids" in text
    assert "<PERSON>" not in text


def test_patient_lines_are_marked(tmp_path):
    text = export_audit_log(LOG, tmp_path).read_text(encoding="utf-8")
    assert 'class="speaker patient"' in text


def test_scores_are_shown_as_notes(tmp_path):
    text = export_audit_log(LOG, tmp_path).read_text(encoding="utf-8")
    assert '<div class="note">[Theme scores] Dermatology: 0.512</div>' in text


def test_file_name_holds_no_patient_text(tmp_path):
    path = export_audit_log([("Patient", "Maria")], tmp_path)
    assert path.name.startswith("audit_log_") and "Maria" not in path.name


def test_creates_missing_folder(tmp_path):
    path = export_audit_log(LOG, tmp_path / "new" / "folder")
    assert path.exists()


def test_empty_log_still_writes(tmp_path):
    assert export_audit_log([], tmp_path).exists()


def test_non_list_raises(tmp_path):
    with pytest.raises(ValueError):
        export_audit_log("not a log", tmp_path)
