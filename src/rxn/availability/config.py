"""Configuration for rxn-availability."""

from functools import lru_cache
from typing import Optional

from pydantic import FilePath
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Setting class."""

    # database configuration path
    database_config_path: Optional[FilePath] = None

    model_config = SettingsConfigDict(env_prefix="RXN_")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings.

    Returns:
        rxn-availability settings.
    """
    return Settings()  # type:ignore
