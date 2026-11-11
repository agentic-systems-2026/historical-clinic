# Build plan: complete historical-clinic workflow

Working notes for building the Session 11 example ("rough draft that runs end to end"). This file is the hand-off between work sessions: an assistant with no other context can resume from it. Delete it when the build is finished.

## Goal

A finished example, not a rough draft:
- every disposable component written and in the repository;
- every component (atomic and disposable) with unit tests that run in GitHub Actions;
- the whole workflow published as markdown instructions (`WORKFLOW.md`) from which an LLM can regenerate the glue, verified by running it in full on one test input.

## Course definitions (EPID 695/895)

- **Atomic protocol:** well-defined I/O, citable provenance, unit tests required, reused across library workflows. Here: Score (Sentence-BERT all-MiniLM-L6-v2, pinned revision) and De-identify (Microsoft Presidio). The tests define the exact call the glue makes; there is no wrapper module.
- **Disposable component:** well-defined I/O, written for one workflow, unit tests optional (we include them), mostly LLM calls with prompt assets returning a specified data structure. The coding agent must call the provided script, never rewrite it. Here: `components/`.
- **Minimal glue:** all code the coding agent writes from the markdown. Here: `historical_clinic.py`, regenerated from `WORKFLOW.md`.
- **Workflow / agentic:** any multistage library protocol; "agentic" means an LLM chooses a path at a decision node or processes text inside a component (here: the two Explain components).

## Decisions

- LLM: Gemma via Ollama's HTTP API, temperature 0, seed 0, default tag `gemma3:1b` (`components/gemma.py`). `HC_LLM=stub` returns a fixed reply for tests.
- CI: every push and pull request runs all tests with the stub LLM. Weekly (Monday 12:00 UTC) and on demand, a second job installs Ollama 0.40.6, pulls `gemma3:1b`, and runs the end-to-end test live.
- Data: `data/verified_themes.json` and `data/verified_responses.json` are the original course files, unchanged (10 themes, 99 queries, 19 historical physicians).
- Test input: `tests/data/test_session.txt`, a synthetic session with a fake name and phone number that exercises N, 1, 0, N, 1.
- Departures from the original `historical_clinic.py` (Session 3): funnel mode only; one session per run; scoring is Sentence-BERT instead of LLM scoring; rejecting every theme or query gives the fallback through Look up answer (`None` path); audit log is de-identified and its file name holds no patient text.
- Pins (all at least two weeks old on 2026-11-11): sentence-transformers 6.2.0, transformers 5.20.2, torch 2.14.1 (CPU index), pytest 9.1.1, presidio 2.2.364, spaCy model en_core_web_lg (via `spacy download`).

## Milestones

- [x] 1. Layout, data assets, `.gitignore`, `pytest.ini`, this plan
- [x] 2. Score atomic protocol tests (`tests/test_score.py`); De-identify test moved to `tests/`
- [x] 3. Disposable components and their tests (`components/`, `prompts/`, `tests/test_select.py`, `test_explain.py`, `test_gemma.py`, `test_look_up_answer.py`, `test_export_audit_log.py`)
- [x] 4. Reference glue (`historical_clinic.py`) and end-to-end test (`tests/test_end_to_end.py`)
- [x] 5. CI for everything (`.github/workflows/tests.yml`)
- [x] 6. `WORKFLOW.md`
- [ ] 7. First CI run green on GitHub (see "Verify in CI" below)
- [ ] 8. Live run on the instructor's computer with Ollama + Gemma; check the audit log by eye
- [ ] 9. Regeneration check: fresh LLM session regenerates the glue from `WORKFLOW.md`; `pytest -v` passes; live run works
- [ ] 10. README rewrite (contract table per component, how to run, how to regenerate, known limitations); update `docs/wire_diagram.png` only if the build changed the design
- [ ] 11. Merge `full-workflow` into `main`; delete this file

## Verify in CI (not testable in the build sandbox)

The build sandbox could not download from Hugging Face, so these were checked only with a stand-in encoder:
1. **Model revision** `8b3219a92973c328a8e22fadcfa821b5dc75636a` for all-MiniLM-L6-v2 was taken from a third-party pin. If CI fails to download it, replace it in `tests/test_score.py`, `historical_clinic.py`, and `WORKFLOW.md` with a commit hash from the model's "Files and versions → History" page on Hugging Face.
2. **Theme ranking:** the end-to-end test assumes the real encoder ranks "Dermatology & Skin Conditions" first for the skin query. If not, change the query in `tests/data/test_session.txt` and `TARGET` in `tests/test_end_to_end.py` to a verified query whose theme does rank first.
3. **Invalid-input test** in `tests/test_score.py` assumes `encode(None)` raises TypeError or ValueError; adjust to the actual exception if not.
4. The `live` job (Ollama install and Gemma pull on the runner) has not run yet; trigger it with **Actions → tests → Run workflow**.

## Known limitations (for the README and the Session 13 system card)

- De-identify redacts physician names in the audit log (for example "Our physician, <PERSON> / Rhazes"), because it runs on every log entry, including LLM text that may echo the patient. Durations are redacted as DATE_TIME and ZIP codes are kept (existing xfail tests).
- Sentence-BERT truncates input after 256 word pieces; long queries are scored on their beginning only (tested).
- Score themes compares the query with theme names, which are short; ranking can be weak for vague queries (the rephrase loop handles this).

## Resume prompt

Paste this into a new chat (with code execution on) to continue:

> I'm building the complete example workflow for my course EPID 695/895 (Agentic AI in Healthcare and Public Health). Clone https://github.com/agentic-systems-2026/historical-clinic, check out the `full-workflow` branch, and read `docs/BUILD_PLAN.md`, `WORKFLOW.md`, and `docs/wire_diagram.png`. Continue from the first unchecked milestone. I push all changes myself, so give me the changed files and the git commands. Ask me before changing any decision recorded in the plan.
