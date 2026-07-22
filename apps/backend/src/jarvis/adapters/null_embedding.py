"""EmbeddingProvider interino: sin key de OpenRouter no embebe. Permite arrancar sin gastar red.

Devuelve vectores vacíos: la memoria de ángulos degrada a "recuerda algunos ya tratados" sin
poder ordenarlos por similitud, pero nunca falla ni gasta. En producción se usa el real.
"""

from __future__ import annotations

from jarvis.domain.embedding import BatchEmbeddingResult, EmbeddingResult


class NullEmbeddingProvider:
    """Implementa EmbeddingProvider devolviendo vectores vacíos y costo cero."""

    async def embed(self, text: str) -> EmbeddingResult:
        """Devuelve un embedding vacío sin gastar red."""
        return EmbeddingResult(vector=[], tokens=0)

    async def embed_batch(self, texts: list[str]) -> BatchEmbeddingResult:
        """Devuelve un embedding vacío por cada texto, sin gastar red."""
        return BatchEmbeddingResult(vectors=[[] for _ in texts], tokens=0)
