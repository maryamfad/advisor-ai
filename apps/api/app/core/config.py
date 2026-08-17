from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    public_base_url: str = "http://localhost:8000"
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
