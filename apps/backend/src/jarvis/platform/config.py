"""Configuración por entorno. Nada de secretos en el código."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes de la aplicación, leídos de variables de entorno o de un archivo .env."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="JARVIS_", extra="ignore")

    environment: str = "development"
    openrouter_api_key: str = ""
    gemini_api_key: str = ""
    gemini_text_model: str = "gemini-flash-latest"
    gemini_tts_model: str = "gemini-3.1-flash-tts-preview"
    gemini_tts_voice: str = "Kore"
    database_url: str = ""
    heraldo_feeds: str = ""
    tavily_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_bucket: str = "podcasts"


@lru_cache
def get_settings() -> Settings:
    """Entrega la configuración como singleton cacheado."""
    return Settings()
