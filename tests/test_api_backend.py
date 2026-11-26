"""The API backends (Groq, Gemini) of the real-agent LLM wrapper, tested with a fake endpoint (no network, no key)."""
import io, json
import urllib.error
import pytest
from ereplan import realagent as ra


class _Resp(io.BytesIO):
    pass


def _ok(text):
    return _Resp(json.dumps({"model": "openai/gpt-oss-120b", "system_fingerprint": "fp_x",
                             "choices": [{"message": {"content": text}}]}).encode())


def test_groq_call_is_cached_and_sends_low_effort(tmp_path, monkeypatch):
    monkeypatch.setattr(ra, "OUT", str(tmp_path))
    monkeypatch.setitem(ra.API_PROVIDERS["groq"], "gap", 0.0)
    monkeypatch.setenv("GROQ_API_KEY", "test")
    sent = []

    def fake_urlopen(req, timeout):
        sent.append(json.loads(req.data))
        return _ok("42")
    monkeypatch.setattr(ra.urllib.request, "urlopen", fake_urlopen)
    llm = ra.LLM("groq:openai/gpt-oss-120b")
    assert llm("Calculate: 6*7", max_tokens=24, temperature=0.7, seed=1) == "42"
    assert llm("Calculate: 6*7", max_tokens=24, temperature=0.7, seed=1) == "42"   # second call from the cache
    assert len(sent) == 1
    assert sent[0]["reasoning_effort"] == "low" and sent[0]["max_completion_tokens"] == 1024
    assert sent[0]["seed"] == 1 and sent[0]["temperature"] == 0.7
    meta = json.load(open(tmp_path / "api_meta_groq_openai_gpt-oss-120b.json"))
    assert meta["seen"][0]["system_fingerprint"] == "fp_x"


def test_groq_daily_limit_stops_and_keeps_answers(tmp_path, monkeypatch):
    monkeypatch.setattr(ra, "OUT", str(tmp_path))
    monkeypatch.setitem(ra.API_PROVIDERS["groq"], "gap", 0.0)
    monkeypatch.setenv("GROQ_API_KEY", "test")
    calls = {"n": 0}

    def fake_urlopen(req, timeout):
        calls["n"] += 1
        if calls["n"] == 1:
            return _ok("7")
        raise urllib.error.HTTPError(ra.API_PROVIDERS["groq"]["url"], 429, "limit", {"retry-after": "3600"}, io.BytesIO(b""))
    monkeypatch.setattr(ra.urllib.request, "urlopen", fake_urlopen)
    llm = ra.LLM("groq:openai/gpt-oss-120b")
    assert llm("Calculate: 3+4") == "7"
    with pytest.raises(SystemExit):
        llm("Calculate: 5+5")
    saved = json.load(open(tmp_path / "llm_cache_groq_openai_gpt-oss-120b.json"))
    assert list(saved.values()) == ["7"]


def test_groq_needs_a_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("EREPLAN_REPLAY", raising=False)
    with pytest.raises(SystemExit):
        ra.LLM("groq:openai/gpt-oss-120b")


def test_gemini_uses_its_own_endpoint_and_key(tmp_path, monkeypatch):
    monkeypatch.setattr(ra, "OUT", str(tmp_path))
    monkeypatch.setitem(ra.API_PROVIDERS["gemini"], "gap", 0.0)
    monkeypatch.setenv("GEMINI_API_KEY", "g-test")
    seen = []

    def fake_urlopen(req, timeout):
        seen.append((req.full_url, req.get_header("Authorization"), json.loads(req.data)))
        return _ok("9")
    monkeypatch.setattr(ra.urllib.request, "urlopen", fake_urlopen)
    llm = ra.LLM("gemini:some-flash-lite")
    assert llm("Calculate: 4+5", temperature=0.7, seed=2) == "9"
    url, auth, body = seen[0]
    assert "generativelanguage.googleapis.com" in url and auth == "Bearer g-test"
    assert body["model"] == "some-flash-lite" and body["reasoning_effort"] == "low"
