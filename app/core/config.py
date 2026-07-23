from functools import lru_cache

from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    name: str = "Education Platform API"
    version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()