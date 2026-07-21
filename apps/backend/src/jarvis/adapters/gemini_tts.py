"""TTS real por Gemini directo: convierte el guion en audio WAV. Implementa SpeechSynthesizer.

Gemini devuelve PCM crudo (audio/L16) en base64; se envuelve en una cabecera WAV para que sea
reproducible tal cual. Directo a Google (sin margen de OpenRouter).
"""

from __future__ import annotations

import base64
import struct
from typing import Any

import httpx

from jarvis.modules.heraldo.domain import PodcastStyle

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
_DEFAULT_RATE = 24000


class GeminiSpeechSynthesizer:
    """Sintetiza voz con la API TTS de Gemini y devuelve un WAV listo para reproducir."""

    def __init__(self, api_key: str, client: httpx.AsyncClient, model: str, voice: str) -> None:
        self._api_key = api_key
        self._client = client
        self._model = model
        self._voice = voice

    async def synthesize(self, text: str, style: PodcastStyle, voice: str | None = None) -> bytes:
        """Convierte el guion en audio WAV con la voz pedida (o la de por defecto)."""
        response = await self._client.post(
            f"{_BASE_URL}/{self._model}:generateContent",
            json=_tts_payload(text, voice or self._voice),
            headers={"x-goog-api-key": self._api_key},
        )
        response.raise_for_status()
        pcm, rate = _extract_audio(response.json())
        return _pcm_to_wav(pcm, rate)


def _tts_payload(text: str, voice: str) -> dict[str, Any]:
    """Arma el cuerpo pidiendo salida de audio con la voz elegida."""
    return {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }


def _extract_audio(data: dict[str, Any]) -> tuple[bytes, int]:
    """Extrae el PCM (decodificado) y su frecuencia de muestreo desde la respuesta."""
    inline = data["candidates"][0]["content"]["parts"][0]["inlineData"]
    pcm = base64.b64decode(inline["data"])
    return pcm, _rate_from_mime(inline.get("mimeType", ""))


def _rate_from_mime(mime: str) -> int:
    """Lee la frecuencia de muestreo del mimeType (p. ej. 'audio/L16;rate=24000')."""
    for token in mime.split(";"):
        cleaned = token.strip()
        if cleaned.startswith("rate="):
            return int(cleaned[len("rate="):])
    return _DEFAULT_RATE


def _pcm_to_wav(pcm: bytes, sample_rate: int, channels: int = 1, bits: int = 16) -> bytes:
    """Envuelve PCM de 16 bits mono en una cabecera WAV estándar."""
    byte_rate = sample_rate * channels * bits // 8
    block_align = channels * bits // 8
    fmt = struct.pack("<IHHIIHH", 16, 1, channels, sample_rate, byte_rate, block_align, bits)
    header = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE"
    header += b"fmt " + fmt + b"data" + struct.pack("<I", len(pcm))
    return header + pcm
