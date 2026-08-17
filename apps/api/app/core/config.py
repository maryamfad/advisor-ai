from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    public_base_url: str = "http://localhost:8000"
    # Optional -- fetch_daily_prices() raises a clear
    # MarketDataUnavailableError if this isn't set, rather than the
    # app failing to start without one.
    market_data_api_key: str | None = None
    market_data_base_url: str = "https://api.twelvedata.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
