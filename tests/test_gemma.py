"""Unit tests for the shared Gemma call (components/gemma.py)."""
import io
import json
import urllib.error

import pytest

from components import gemma


def test_stub_mode(monkeypatch):
    monkeypatch.setenv("HC_LLM", "stub")
    assert gemma.generate("anything") == gemma.STUB_REPLY


def test_sends_prompt_to_ollama(monkeypatch):
    monkeypatch.delenv("HC_LLM", raising=False)
    monkeypatch.setenv("OLLAMA_HOST", "http://example:1234")
    monkeypatch.setenv("HC_GEMMA_MODEL", "gemma3:1b")
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["body"] = json.loads(request.data)
        return io.BytesIO(json.dumps({"response": "Hello."}).encode())

    monkeypatch.setattr(gemma.urllib.request, "urlopen", fake_urlopen)
    assert gemma.generate("Say hello") == "Hello."
    assert seen["url"] == "http://example:1234/api/generate"
    assert seen["body"]["model"] == "gemma3:1b"
    assert seen["body"]["prompt"] == "Say hello"
    assert seen["body"]["stream"] is False
    assert seen["body"]["options"]["temperature"] == 0


def test_unreachable_server_raises_helpful_error(monkeypatch):
    monkeypatch.delenv("HC_LLM", raising=False)

    def refuse(request, timeout):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(gemma.urllib.request, "urlopen", refuse)
    with pytest.raises(RuntimeError, match="ollama serve"):
        gemma.generate("hello")


def test_non_string_prompt_raises():
    with pytest.raises(ValueError):
        gemma.generate(None)
