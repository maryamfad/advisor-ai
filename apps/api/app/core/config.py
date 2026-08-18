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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
