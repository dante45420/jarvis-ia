"""Adaptadores interinos de audio del podcast.

Placeholders hasta cablear el TTS real (Gemini/OpenRouter) y Supabase Storage: dejan el guion
funcionando de punta a punta sin necesitar todavía las keys de audio. Cumplen los puertos
SpeechSynthesizer y AudioStorage.
"""

from __future__ import annotations

from jarvis.modules.heraldo.domain import PodcastStyle


class NullSpeechSynthesizer:
    """TTS interino: devuelve audio vacío hasta cablear el sintetizador real."""

    async def synthesize(self, text: str, style: PodcastStyle, voice: str | None = None) -> bytes:
        return b""


class InMemoryAudioStorage:
    """Almacenamiento interino en memoria hasta cablear Supabase Storage."""

    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    async def store(self, key: str, audio: bytes) -> str:
        self._blobs[key] = audio
        return f"memory://{key}"
