"""Test del almacenamiento en Supabase: sube el audio y devuelve la URL pública. Sin red real."""

from __future__ import annotations

import httpx

from jarvis.adapters.supabase_storage import SupabaseAudioStorage


async def test_store_uploads_and_returns_public_url() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        captured["content"] = request.content
        return httpx.Response(200, json={"Key": "podcasts/episodes/ep.wav"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        storage = SupabaseAudioStorage("https://x.supabase.co", "svc", "podcasts", client)
        url = await storage.store("episodes/ep.wav", b"AUDIO")

    assert url == "https://x.supabase.co/storage/v1/object/public/podcasts/episodes/ep.wav"
    assert captured["url"] == "https://x.supabase.co/storage/v1/object/podcasts/episodes/ep.wav"
    assert captured["auth"] == "Bearer svc"
    assert captured["content"] == b"AUDIO"
