from types import SimpleNamespace

import pytest

from documind import llm


def _settings(**overrides):
    values = {
        "ollama_base_url": "http://ollama.test",
        "chat_model": "test-model",
        "num_ctx": 8192,
        "max_output_tokens": 128,
        "temperature": 0.2,
        "llm_retries": 2,
        "llm_retry_backoff_s": 0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_stream_chat_retries_before_first_token(monkeypatch):
    attempts = 0

    class Client:
        def __init__(self, host):
            assert host == "http://ollama.test"

        def chat(self, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise ConnectionError("warming up")
            return iter([{"message": {"content": "ready"}}])

    monkeypatch.setattr(llm.ollama, "Client", Client)
    monkeypatch.setattr(llm, "get_settings", lambda: _settings())

    assert list(llm.stream_chat([{"role": "user", "content": "hi"}])) == ["ready"]
    assert attempts == 2


def test_stream_chat_does_not_retry_after_partial_output(monkeypatch):
    class Client:
        def __init__(self, host):
            pass

        def chat(self, **kwargs):
            def stream():
                yield {"message": {"content": "partial"}}
                raise ConnectionError("connection dropped")

            return stream()

    monkeypatch.setattr(llm.ollama, "Client", Client)
    monkeypatch.setattr(llm, "get_settings", lambda: _settings())

    with pytest.raises(ConnectionError):
        list(llm.stream_chat([{"role": "user", "content": "hi"}]))
