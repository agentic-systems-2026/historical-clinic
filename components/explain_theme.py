"""Disposable component: Explain theme.

LLM writes a 2-3 sentence rationale for the selected theme.
Input:  user_query (str), theme (str)
Output: rationale (str), at most 3 sentences, never empty
Prompt asset: prompts/explain_theme.txt
"""
from pathlib import Path

from components import gemma

PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "explain_theme.txt").read_text(encoding="utf-8").strip()


def explain_theme(user_query: str, theme: str, generate=None) -> str:
    """Return a short rationale for why `theme` may fit `user_query`.

    `generate` (prompt -> reply) defaults to Gemma via Ollama; tests pass a fake.
    """
    if not isinstance(user_query, str) or not isinstance(theme, str):
        raise ValueError("user_query and theme must be strings")
    generate = generate or gemma.generate
    reply = generate(PROMPT.format(user_query=user_query, theme=theme))
    return gemma.clean_reply(reply)
