"""Almacenamiento de audio en Supabase Storage. Implementa AudioStorage.

Sube el audio al bucket configurado (con upsert) y devuelve su URL pública. Requiere que el
bucket sea público para servir el audio directo.
"""

from __future__ import annotations

import httpx


class SupabaseAudioStorage:
    """Sube el audio a un bucket de Supabase y devuelve la URL pública del objeto."""

    def __init__(
        self, base_url: str, service_key: str, bucket: str, client: httpx.AsyncClient
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_key = service_key
        self._bucket = bucket
        self._client = client

    async def store(self, key: str, audio: bytes) -> str:
        """Sube el audio bajo la clave dada y devuelve su URL pública."""
        response = await self._client.post(
            f"{self._base_url}/storage/v1/object/{self._bucket}/{key}",
            content=audio,
            headers=self._headers(),
        )
        response.raise_for_status()
        return f"{self._base_url}/storage/v1/object/public/{self._bucket}/{key}"

    def _headers(self) -> dict[str, str]:
        """Cabeceras de autenticación y de subida con reemplazo (upsert)."""
        return {
            "Authorization": f"Bearer {self._service_key}",
            "Content-Type": "audio/wav",
            "x-upsert": "true",
        }
