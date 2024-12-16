from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    GITHUB_TOKEN: str
    OPENAI_KEY: str
    OPENAI_MODEL: str

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()
