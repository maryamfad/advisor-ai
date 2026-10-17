from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    # The risk-questionnaire "shareable link" is built from this --
    # it must point at the frontend (which serves
    # /risk-questionnaire/{token}), not this API's own origin.
    public_base_url: str = "http://localhost:5173"
    # Vite falls back to 5174, 5175, ... when 5173 is already taken (a
    # second `npm run dev`, a leftover process), so allow a small range
    # of dev ports rather than requiring 5173 specifically.
    cors_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ]
    # Optional -- fetch_daily_prices() raises a clear
    # MarketDataUnavailableError if this isn't set, rather than the
    # app failing to start without one.
    market_data_api_key: str | None = None
    market_data_base_url: str = "https://api.twelvedata.com"
    # Optional -- run_agent_turn() raises a clear error if this isn't
    # set, rather than the app failing to start without one.
    anthropic_api_key: str | None = None
    ai_agent_model: str = "claude-sonnet-5"
    ai_agent_max_tool_iterations: int = 6

    # Which chat model backs the AI assistant -- see
    # app/services/chat_model.py. Ollama's tool-calling is best-effort
    # only (see the README's limitations section), not validated or
    # guarded specially here.
    chat_model_provider: Literal["anthropic", "openai", "ollama"] = "anthropic"
    ollama_base_url: str = "http://localhost:11434"

    # Optional -- used for policy-document embeddings (RAG). Routes
    # that ingest a document raise a clear error if this isn't set,
    # same pattern as anthropic_api_key above.
    openai_api_key: str | None = None
    embedding_model_name: str = "text-embedding-3-small"
    pgvector_collection_name: str = "insurance_policy_chunks"

    # Where uploaded client documents are saved on disk. Not meant to
    # be a production file-storage design -- just enough so ingestion
    # has real bytes to read.
    document_storage_dir: str = "./data/documents"

    # Off by default -- LangSmith tracing of the agent graph. These
    # are read from .env (like every other setting here) and copied
    # into real process env vars by app.core.tracing, since that's
    # where the LangSmith SDK itself looks for them.
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "advisor-ai"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
