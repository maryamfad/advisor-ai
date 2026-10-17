"""Copies AdvisorAI's own .env-based settings into the process
environment variables the LangSmith SDK reads directly (it has no
API of its own to configure this programmatically -- see
langsmith.utils.get_env_var). A no-op, and no behavior change, unless
langsmith_tracing is explicitly turned on."""

import os

from app.core.config import settings


def configure_langsmith_tracing() -> None:
    if not settings.langsmith_tracing:
        return

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    if settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
