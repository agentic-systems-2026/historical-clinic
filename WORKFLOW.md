# Historical clinic: instructions for a coding agent

Write one file, `historical_clinic.py`, in the top level of this repository. It is the minimal glue for the workflow in `docs/wire_diagram.png`: it routes a patient's question to an answer written in the voice of a historical physician and verified in advance, then saves a de-identified audit log.

## Rules

1. Write only `historical_clinic.py`. Do not create, edit, or replace any other file.
2. Call the disposable components in `components/` exactly as described below. Do not copy, rewrite, or reimplement them.
3. Call the two atomic protocols exactly as shown in the code blocks below.
4. Use only the packages in `requirements.txt` and the Python standard library.
5. Use the exact text given in quotation marks for everything shown to the patient.

## How it runs

```
python historical_clinic.py [--out-dir DIR]
```

- Use `argparse`. `--out-dir` sets the folder for the audit log (default: `audit_logs`).
- Read every patient reply from standard input with `input(prompt)`. Print every clinic message with `print`.
- Read the data relative to the script's own folder (`Path(__file__).resolve().parent`), not the working directory:
  - `data/verified_themes.json`: a dict mapping each theme name (str) to its verified queries (list[str]). Keep the file's order.
  - `data/verified_responses.json`: a list of dicts, passed unchanged to Look up answer.
- Run one patient session, then exit with status 0.

## Atomic protocols

Load each model once, at module level, then define these two functions exactly.

**Score** (Sentence-BERT). Used for both Score themes and Score queries.

```python
from sentence_transformers import SentenceTransformer, util

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "8b3219a92973c328a8e22fadcfa821b5dc75636a"
encoder = SentenceTransformer(MODEL_NAME, revision=MODEL_REVISION)

def score(query, candidates):
    query_embedding = encoder.encode(query, convert_to_tensor=True)
    candidate_embeddings = encoder.encode(candidates, convert_to_tensor=True)
    return util.cos_sim(query_embedding, candidate_embeddings)[0].tolist()
```

**De-identify** (Microsoft Presidio).

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def deidentify(text):
    findings = analyzer.analyze(text=text, language="en")
    return anonymizer.anonymize(text=text, analyzer_results=findings).text
```

## Disposable components

| Import | Call | Returns |
|---|---|---|
| `from components.select_theme import select_theme` | `select_theme(themes, scores, rejected)` | highest-scoring theme not in `rejected` (a set), or `None` |
| `from components.explain_theme import explain_theme` | `explain_theme(user_query, theme)` | 2–3 sentence rationale (str) |
| `from components.select_query import select_query` | `select_query(queries, scores, rejected)` | highest-scoring query not in `rejected`, or `None` |
| `from components.explain_query import explain_query` | `explain_query(user_query, query)` | 2–3 sentence rationale (str) |
| `from components.look_up_answer import look_up_answer, FALLBACK` | `look_up_answer(confirmed_query, verified_responses)` | response to the patient (str); equals `FALLBACK` if there is no verified answer |
| `from components.export_audit_log import export_audit_log` | `export_audit_log(redacted_log, out_dir)` | path of the HTML file it wrote |

The Explain components call Gemma through Ollama. Do not pass them a `generate` argument; they read the environment variable `HC_LLM` themselves (`stub` gives a fixed reply for testing).

## Text shown to the patient

- OPENING: "Thank you for trusting us with your care today. Our AI agent is going to route you to a real doctor-verified response as best we can. Along the way, you will receive AI-generated answers. These do not constitute medical advice. Please wait a moment."
- ASK_QUERY: "Enter your query: "
- SELECTION_PROMPT: " (1 for yes, 0 for no. Otherwise, please select N for new and if you rephrase your query we might be able to get you to the best answer faster.): "
- NEW_QUERY_PROMPT: "Please enter your new query: "
- First theme offered: "Thanks for waiting. It sounds like you want to discuss: {theme} {rationale}" followed by SELECTION_PROMPT
- Later themes: "I'm sorry, is {theme} a better fit? {rationale}" followed by SELECTION_PROMPT
- First query offered: "Is this a good fit? {query} {rationale}" followed by SELECTION_PROMPT
- Later queries: "I'm sorry. Is this a better fit? {query} {rationale}" followed by SELECTION_PROMPT
- CLOSING: "Thank you again for trusting us with your care today, please let us know if you would like to schedule an appointment."

## Steps

1. Print OPENING. Ask ASK_QUERY to get the patient's query.
2. **Theme stage.** Score the query against the theme names. Then repeat:
   - Select theme, using the set of themes rejected so far. If it returns `None`, the theme stage ends with no theme.
   - Explain theme, then ask the patient with the matching text above (the first offer after each scoring uses the "first" wording).
   - Accept only the replies `1`, `0`, or `N`, case-insensitive. If the reply is anything else, ask the same question again.
   - `1`: the theme is confirmed; go to step 3.
   - `0`: add the theme to the rejected set and offer the next one, without scoring again.
   - `N`: ask NEW_QUERY_PROMPT. The answer replaces the query. Clear the rejected set and go back to scoring themes.
3. **Query stage.** Runs only if a theme was confirmed. Do the same as step 2 with the confirmed theme's verified queries, using Select query, Explain query, and the query wording. On `N`, the theme stays confirmed; rescore only its queries with the new query.
4. Call Look up answer with the confirmed query, or `None` if either stage ended without one. Print the result. If it is not `FALLBACK`, also print CLOSING.
5. Build the conversation log as a list of `(speaker, text)` tuples while the session runs. The speaker is `"Clinic"` or `"Patient"`. Log, in order:
   - every clinic message printed,
   - every question asked (its text, stripped of surrounding spaces),
   - every accepted patient reply exactly as typed (trim surrounding spaces),
   - after each scoring, one clinic note starting with `[Theme scores]` or `[Query scores]` that lists every candidate with its score to three decimals, highest first, like `[Theme scores] Dermatology & Skin Conditions: 0.512; ...`.
6. At the end, de-identify the text of every log entry, keeping the speaker. Pass the redacted log and `--out-dir` to Export audit log, then print `[Audit log saved to {path}]`.

## Acceptance test

From the top of the repository, with the packages installed and the spaCy model downloaded (`python -m spacy download en_core_web_lg`):

```
pytest -v
```

Every test must pass (two are expected failures, marked `xfail`). `tests/test_end_to_end.py` runs `historical_clinic.py` on the synthetic session in `tests/data/test_session.txt` with the LLM stubbed.

To run the same session live, start Ollama with Gemma available (`ollama pull gemma3:1b`) and run:

```
python historical_clinic.py < tests/data/test_session.txt
```

In Windows PowerShell, which has no `<`, use:

```
Get-Content tests/data/test_session.txt | python historical_clinic.py
```
