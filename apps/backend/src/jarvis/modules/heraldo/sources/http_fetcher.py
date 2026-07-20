"""Descarga de feeds por HTTP con httpx: la única pieza con red del adaptador RSS."""

from __future__ import annotations

import httpx


class HttpFeedFetcher:
    """Descarga el contenido de un feed reutilizando un cliente httpx async compartido."""

    def __init__(self, client: httpx.AsyncClient, timeout: float = 10.0) -> None:
        self._client = client
        self._timeout = timeout

    async def __call__(self, url: str) -> str:
        """Trae el texto del feed, siguiendo redirecciones y fallando en errores HTTP."""
        response = await self._client.get(url, timeout=self._timeout, follow_redirects=True)
        response.raise_for_status()
        return response.text
