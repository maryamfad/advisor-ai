import os

import app.core.tracing as tracing_module
from app.core.tracing import configure_langsmith_tracing

_TRACING_ENV_VARS = ("LANGSMITH_TRACING", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT")


def test_disabled_by_default_sets_no_env_vars(monkeypatch) -> None:
    monkeypatch.setattr(tracing_module.settings, "langsmith_tracing", False)
    for var in _TRACING_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    configure_langsmith_tracing()

    for var in _TRACING_ENV_VARS:
        assert var not in os.environ


def test_enabled_sets_tracing_project_and_api_key(monkeypatch) -> None:
    monkeypatch.setattr(tracing_module.settings, "langsmith_tracing", True)
    monkeypatch.setattr(tracing_module.settings, "langsmith_api_key", "lsv2_fake_key")
    monkeypatch.setattr(tracing_module.settings, "langsmith_project", "advisor-ai-test")
    # configure_langsmith_tracing writes real os.environ entries directly
    # (that's the whole point -- the LangSmith SDK reads them from
    # there), so clean them up ourselves rather than relying on
    # monkeypatch, which only reverts changes made through its own
    # setenv/delenv.
    for var in _TRACING_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    try:
        configure_langsmith_tracing()

        assert os.environ["LANGSMITH_TRACING"] == "true"
        assert os.environ["LANGSMITH_PROJECT"] == "advisor-ai-test"
        assert os.environ["LANGSMITH_API_KEY"] == "lsv2_fake_key"
    finally:
        for var in _TRACING_ENV_VARS:
            os.environ.pop(var, None)
