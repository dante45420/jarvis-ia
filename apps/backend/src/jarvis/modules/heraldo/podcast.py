"""Dominio del podcast: el episodio y los puertos de voz y almacenamiento de audio."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from jarvis.modules.heraldo.domain import PodcastStyle


@dataclass(frozen=True, slots=True)
class Episode:
    """Un episodio listo: su guion, el audio ya alojado y las fuentes que lo respaldan."""

    id: str
    title: str
    script: str
    audio_url: str
    duration_minutes: int
    sources: tuple[str, ...]


@runtime_checkable
class SpeechSynthesizer(Protocol):
    """Convierte el guion en audio. Detrás vive el TTS concreto (Gemini/OpenRouter)."""

    async def synthesize(self, text: str, style: PodcastStyle, voice: str | None = None) -> bytes:
        """Devuelve el audio del guion en bytes; voice None usa la voz por defecto."""
        ...


@runtime_checkable
class AudioStorage(Protocol):
    """Aloja el audio y devuelve una URL. Detrás vive el almacenamiento concreto (Supabase)."""

    async def store(self, key: str, audio: bytes) -> str:
        """Guarda el audio bajo una clave y devuelve su URL pública."""
        ...
