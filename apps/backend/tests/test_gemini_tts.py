"""Test del TTS de Gemini: pide audio, decodifica el PCM y lo envuelve en WAV. Sin red real."""

from __future__ import annotations

import base64
import json

import httpx

from jarvis.adapters.gemini_tts import GeminiSpeechSynthesizer
from jarvis.modules.heraldo.domain import PodcastStyle

_PCM = b"\x01\x02\x03\x04"


def _response() -> dict[str, object]:
    inline = {"mimeType": "audio/L16;rate=24000", "data": base64.b64encode(_PCM).decode()}
    return {"candidates": [{"content": {"parts": [{"inlineData": inline}]}}]}


async def test_synthesize_requests_audio_and_wraps_pcm_in_wav() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_response())

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        synth = GeminiSpeechSynthesizer("k", client, "gemini-2.5-flash-preview-tts", "Kore")
        audio = await synth.synthesize("hola", PodcastStyle.NARRATOR)

    assert audio[:4] == b"RIFF"
    assert audio[8:12] == b"WAVE"
    assert audio.endswith(_PCM)
    body = captured["body"]
    assert isinstance(body, dict)
    config = body["generationConfig"]
    assert config["responseModalities"] == ["AUDIO"]
    assert config["speechConfig"]["voiceConfig"]["prebuiltVoiceConfig"]["voiceName"] == "Kore"
