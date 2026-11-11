"""Historical clinic: routes a patient's question to a physician-verified answer.

This file is the minimal glue, regenerated from WORKFLOW.md. It calls two atomic
protocols (Sentence-BERT scoring, Presidio de-identification) and the disposable
components in components/; it does not reimplement them.

Usage:  python historical_clinic.py [--out-dir DIR]
Reads the patient's lines from standard input and writes a de-identified HTML
audit log to DIR (default: audit_logs).
"""
import argparse
import json
from pathlib import Path

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from sentence_transformers import SentenceTransformer, util

from components.explain_query import explain_query
from components.explain_theme import explain_theme
from components.export_audit_log import export_audit_log
from components.look_up_answer import FALLBACK, look_up_answer
from components.select_query import select_query
from components.select_theme import select_theme

HERE = Path(__file__).resolve().parent
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "8b3219a92973c328a8e22fadcfa821b5dc75636a"

OPENING = (
    "Thank you for trusting us with your care today. Our AI agent is going to route you "
    "to a real doctor-verified response as best we can. Along the way, you will receive "
    "AI-generated answers. These do not constitute medical advice. Please wait a moment."
)
CLOSING = (
    "Thank you again for trusting us with your care today, please let us know if you "
    "would like to schedule an appointment."
)
SELECTION_PROMPT = (
    " (1 for yes, 0 for no. Otherwise, please select N for new and if you rephrase your "
    "query we might be able to get you to the best answer faster.): "
)
NEW_QUERY_PROMPT = "Please enter your new query: "

# Atomic protocols: loaded once, called exactly as in their unit tests.
encoder = SentenceTransformer(MODEL_NAME, revision=MODEL_REVISION)
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()


def score(query, candidates):
    """Score: cosine similarity of the query to each candidate (Sentence-BERT)."""
    query_embedding = encoder.encode(query, convert_to_tensor=True)
    candidate_embeddings = encoder.encode(candidates, convert_to_tensor=True)
    return util.cos_sim(query_embedding, candidate_embeddings)[0].tolist()


def deidentify(text):
    """De-identify: redact identifiers from free text (Microsoft Presidio)."""
    findings = analyzer.analyze(text=text, language="en")
    return anonymizer.anonymize(text=text, analyzer_results=findings).text


def say(log, text):
    print(text)
    log.append(("Clinic", text))


def ask(log, prompt, allowed=None):
    """Show a prompt, read one line from the patient, and log both."""
    while True:
        reply = input(prompt).strip()
        if allowed is None or reply.lower() in allowed:
            log.append(("Clinic", prompt.strip()))
            log.append(("Patient", reply))
            return reply.lower() if allowed else reply


def log_scores(log, label, candidates, scores):
    ranked = sorted(zip(candidates, scores), key=lambda pair: -pair[1])
    log.append(("Clinic", f"[{label}] " + "; ".join(f"{c}: {s:.3f}" for c, s in ranked)))


def choose(log, query, candidates, label, select, explain, first_text, later_text):
    """Score, select, and explain candidates until the patient confirms one (1),
    rejects them all (0 each time), or rephrases (N). Returns (choice, query)."""
    while True:
        scores = score(query, candidates)
        log_scores(log, label, candidates, scores)
        rejected = set()
        first = True
        while True:
            selected = select(candidates, scores, rejected)
            if selected is None:
                return None, query
            rationale = explain(query, selected)
            text = (first_text if first else later_text).format(item=selected, why=rationale)
            first = False
            reply = ask(log, text + SELECTION_PROMPT, allowed={"1", "0", "n"})
            if reply == "1":
                return selected, query
            if reply == "0":
                rejected.add(selected)
                continue
            query = ask(log, NEW_QUERY_PROMPT)
            break  # rescore with the rephrased query


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", default="audit_logs", help="folder for the HTML audit log")
    args = parser.parse_args()

    themes = json.loads((HERE / "data" / "verified_themes.json").read_text(encoding="utf-8"))
    verified_responses = json.loads((HERE / "data" / "verified_responses.json").read_text(encoding="utf-8"))
    theme_names = list(themes)

    log = []
    say(log, OPENING)
    query = ask(log, "Enter your query: ")

    theme, query = choose(
        log, query, theme_names, "Theme scores", select_theme, explain_theme,
        "Thanks for waiting. It sounds like you want to discuss: {item} {why}",
        "I'm sorry, is {item} a better fit? {why}",
    )
    confirmed_query = None
    if theme is not None:
        confirmed_query, query = choose(
            log, query, themes[theme], "Query scores", select_query, explain_query,
            "Is this a good fit? {item} {why}",
            "I'm sorry. Is this a better fit? {item} {why}",
        )

    answer = look_up_answer(confirmed_query, verified_responses)
    say(log, answer)
    if answer != FALLBACK:
        say(log, CLOSING)

    redacted_log = [(speaker, deidentify(text)) for speaker, text in log]
    path = export_audit_log(redacted_log, args.out_dir)
    print(f"[Audit log saved to {path}]")


if __name__ == "__main__":
    main()
