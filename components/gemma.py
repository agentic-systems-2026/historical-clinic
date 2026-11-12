"""Shared LLM call used by the two Explain components (not a diagram node).

Calls Gemma served locally by Ollama through its HTTP API, with temperature 0
and a fixed seed so repeated runs give the same text where the model allows it.

Environment variables:
    HC_LLM          "stub" returns a fixed reply without calling Ollama (used by
                    tests and CI); anything else, or unset, calls Ollama.
    HC_GEMMA_MODEL  Ollama model tag (default: gemma3:1b).
    OLLAMA_HOST     Ollama server address (default: http://localhost:11434).
"""
import json
import os
import re
import urllib.error
import urllib.request

DEFAULT_MODEL = "gemma3:1b"
DEFAULT_HOST = "http://localhost:11434"
STUB_REPLY = "We think this might be a fit because this is a stub reply used for testing."
FALLBACK_REPLY = "We think this might be a fit because it is the closest match we found."


def generate(prompt: str) -> str:
    """Send one prompt to Gemma and return the raw reply text."""
    if not isinstance(prompt, str):
        raise ValueError("prompt must be a string")
    if os.environ.get("HC_LLM", "").lower() == "stub":
        return STUB_REPLY
    host = os.environ.get("OLLAMA_HOST", DEFAULT_HOST).rstrip("/")
    if not host.startswith("http"):
        host = "http://" + host
    model = os.environ.get("HC_GEMMA_MODEL", DEFAULT_MODEL)
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "seed": 0},
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{host}/api/generate", data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.loads(response.read().decode("utf-8")).get("response", "")
    except (urllib.error.URLError, OSError) as error:
        raise RuntimeError(
            f"Could not reach Ollama at {host}. Start it with `ollama serve` and "
            f"download the model with `ollama pull {model}`."
        ) from error


def clean_reply(text: str, max_sentences: int = 3) -> str:
    """Tidy a model reply: collapse whitespace, keep at most `max_sentences`
    sentences, and fall back to a fixed sentence if nothing usable remains."""
    if not isinstance(text, str):
        return FALLBACK_REPLY
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return FALLBACK_REPLY
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(sentences[:max_sentences])
