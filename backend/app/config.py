from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = "dummy-key-for-dev"
    sonnet_model: str = "claude-sonnet-4-5-20250514"
    haiku_model: str = "claude-haiku-4-5-20251001"
    cors_origins: list[str] = ["http://localhost:5173", "https://*.up.railway.app"]

    model_config = {"env_file": ".env"}


settings = Settings()
