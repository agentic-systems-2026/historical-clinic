"""Disposable component: Explain query.

LLM writes a 2-3 sentence rationale for the selected verified query.
Input:  user_query (str), query (str), a verified query from the confirmed theme
Output: rationale (str), at most 3 sentences, never empty
Prompt asset: prompts/explain_query.txt
"""
from pathlib import Path

from components import gemma

PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "explain_query.txt").read_text(encoding="utf-8").strip()


def explain_query(user_query: str, query: str, generate=None) -> str:
    """Return a short rationale for why the verified `query` may fit `user_query`.

    `generate` (prompt -> reply) defaults to Gemma via Ollama; tests pass a fake.
    """
    if not isinstance(user_query, str) or not isinstance(query, str):
        raise ValueError("user_query and query must be strings")
    generate = generate or gemma.generate
    reply = generate(PROMPT.format(user_query=user_query, query=query))
    return gemma.clean_reply(reply)
