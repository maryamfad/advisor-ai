import pytest
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

import app.services.chat_model as chat_model_module
from app.services.chat_model import build_chat_model


def test_anthropic_is_the_default_provider(monkeypatch) -> None:
    monkeypatch.setattr(chat_model_module.settings, "chat_model_provider", "anthropic")
    monkeypatch.setattr(chat_model_module.settings, "anthropic_api_key", "fake-key")

    assert isinstance(build_chat_model(), ChatAnthropic)


def test_anthropic_without_key_raises(monkeypatch) -> None:
    monkeypatch.setattr(chat_model_module.settings, "chat_model_provider", "anthropic")
    monkeypatch.setattr(chat_model_module.settings, "anthropic_api_key", None)

    with pytest.raises(RuntimeError, match="No anthropic_api_key"):
        build_chat_model()


def test_openai_provider_returns_chat_openai(monkeypatch) -> None:
    monkeypatch.setattr(chat_model_module.settings, "chat_model_provider", "openai")
    monkeypatch.setattr(chat_model_module.settings, "openai_api_key", "fake-key")

    assert isinstance(build_chat_model(), ChatOpenAI)


def test_openai_without_key_raises(monkeypatch) -> None:
    monkeypatch.setattr(chat_model_module.settings, "chat_model_provider", "openai")
    monkeypatch.setattr(chat_model_module.settings, "openai_api_key", None)

    with pytest.raises(RuntimeError, match="No openai_api_key"):
        build_chat_model()


def test_ollama_provider_returns_chat_ollama_without_needing_a_key(
    monkeypatch,
) -> None:
    monkeypatch.setattr(chat_model_module.settings, "chat_model_provider", "ollama")

    assert isinstance(build_chat_model(), ChatOllama)
