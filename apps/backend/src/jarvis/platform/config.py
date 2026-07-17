"""Configuración por entorno. Nada de secretos en el código."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes de la aplicación, leídos de variables de entorno o de un archivo .env."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="JARVIS_", extra="ignore")

    environment: str = "development"
    openrouter_api_key: str = ""
    database_url: str = ""


@lru_cache
def get_settings() -> Settings:
    """Entrega la configuración como singleton cacheado."""
    return Settings()
