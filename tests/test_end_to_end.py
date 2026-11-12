"""End-to-end test: runs the glue (historical_clinic.py) on one synthetic
patient session and checks the outcome. This is the acceptance test for glue
regenerated from WORKFLOW.md.

The session (tests/data/test_session.txt) gives a vague first query containing
a fake name and phone number, rephrases (N), confirms the theme (1), rejects
the first verified query (0), rephrases again (N), and confirms (1). It
exercises every branch of the wire diagram.

By default the LLM is stubbed (HC_LLM=stub). Set HC_LLM=ollama to run it live
against Gemma; the checks are the same because the route does not depend on
the LLM's wording.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from components.look_up_answer import look_up_answer

REPO = Path(__file__).resolve().parent.parent
SESSION = REPO / "tests" / "data" / "test_session.txt"
TARGET = "My skin has developed intensely itchy, dry, red, and cracked patches."
RESPONSES = json.loads((REPO / "data" / "verified_responses.json").read_text(encoding="utf-8"))


def run_session(out_dir):
    env = {**os.environ, "HC_LLM": os.environ.get("HC_LLM", "stub")}
    return subprocess.run(
        [sys.executable, str(REPO / "historical_clinic.py"), "--out-dir", str(out_dir)],
        input=SESSION.read_text(encoding="utf-8"), capture_output=True, text=True,
        cwd=REPO, env=env, timeout=900,
    )


def test_session_reaches_verified_answer(tmp_path):
    result = run_session(tmp_path)
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "It sounds like you want to discuss: Dermatology & Skin Conditions" in out
    assert out.count("Is this a good fit? " + TARGET) == 2
    assert look_up_answer(TARGET, RESPONSES) in out

    logs = list(tmp_path.glob("audit_log_*.html"))
    assert len(logs) == 1
    html = logs[0].read_text(encoding="utf-8")
    assert "Maria Lopez" not in html
    assert "212-555-0143" not in html
    assert "&lt;PERSON&gt;" in html and "&lt;PHONE_NUMBER&gt;" in html
    assert "Dermatology &amp; Skin Conditions" in html
