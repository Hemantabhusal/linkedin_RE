from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    linkedin_cookies: str = Field(alias="LINKEDIN_COOKIES")
    linkedin_user_agent: str = Field(alias="LINKEDIN_USER_AGENT")
    linkedin_impersonate: str = Field(default="firefox", alias="LINKEDIN_IMPERSONATE")

    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=3306, alias="DB_PORT")
    db_user: str = Field(alias="DB_USER")
    db_password: str = Field(alias="DB_PASSWORD")
    db_name: str = Field(alias="DB_NAME")

    batch_size: int = Field(default=4, alias="BATCH_SIZE")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    scrape_delay_min_ms: int = Field(default=20000, alias="SCRAPE_DELAY_MIN_MS")
    scrape_delay_max_ms: int = Field(default=45000, alias="SCRAPE_DELAY_MAX_MS")
    rate_limit_cooldown_ms: int = Field(default=180000, alias="RATE_LIMIT_COOLDOWN_MS")
    request_timeout_seconds: float = Field(default=30.0, alias="REQUEST_TIMEOUT_SECONDS")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    debug_linkedin: bool = Field(default=False, alias="DEBUG_LINKEDIN")
    log_payload_samples: bool = Field(default=True, alias="LOG_PAYLOAD_SAMPLES")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

