# historical-clinic

This repository holds unit tests for the **De-identify** atomic protocol, which redacts personal identifiers from free text before a conversation log is exported. The protocol is a thin wrapper around [Microsoft Presidio](https://microsoft.github.io/presidio/), which is the citable source; the tests exercise the exact two calls the workflow's glue code makes.

## Contract

| | Type | Description |
|---|---|---|
| **Input** | `str` | Free text (e.g. a conversation log) |
| **Output** | `str` | The same text with identifiers replaced by entity tags such as `<PERSON>`, `<PHONE_NUMBER>`, `<EMAIL_ADDRESS>` |

```python
findings = analyzer.analyze(text=text, language="en")
redacted = anonymizer.anonymize(text=text, analyzer_results=findings).text
```

## Tested versions

- presidio-analyzer 2.2.364
- presidio-anonymizer 2.2.364
- spaCy model `en_core_web_lg` 3.8.0

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

## Running the tests

```bash
pytest -v
```

Expected result: **7 passed, 2 xfailed**.

## What the tests cover

- **Typical inputs:** names, phone numbers, and email addresses are redacted, and the output is a string.
- **Edge cases:** empty input returns an empty string; lowercase names are still caught; long inputs are fully redacted.
- **Invalid inputs:** non-string input (`None`, `42`) raises `ValueError`.

## Known limitations

These are marked `xfail(strict=True)`, so the suite will fail loudly if a future Presidio release changes the behavior:

- Symptom durations (e.g. "for three days") are redacted as `DATE_TIME`, which can remove clinically relevant information.
- US ZIP codes are **not** redacted by default.
