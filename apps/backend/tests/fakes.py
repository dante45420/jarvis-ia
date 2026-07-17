"""Dobles de prueba reutilizables: un proveedor de embeddings determinístico y sin red."""

from __future__ import annotations

from jarvis.domain.embedding import BatchEmbeddingResult, EmbeddingResult

_DIMENSIONS = 32


class FakeEmbeddingProvider:
    """Embeddings determinísticos por bolsa de palabras: igual texto → igual vector."""

    async def embed(self, text: str) -> EmbeddingResult:
        return EmbeddingResult(vector=_vectorize(text), tokens=_count(text))

    async def embed_batch(self, texts: list[str]) -> BatchEmbeddingResult:
        vectors = [_vectorize(text) for text in texts]
        return BatchEmbeddingResult(vectors=vectors, tokens=sum(_count(t) for t in texts))


def _vectorize(text: str) -> list[float]:
    """Proyecta el texto en un vector fijo contando palabras por bucket (hash estable)."""
    vector = [0.0] * _DIMENSIONS
    for word in text.lower().split():
        vector[_bucket(word)] += 1.0
    return vector


def _bucket(word: str) -> int:
    """Asigna una palabra a un bucket de forma determinística entre procesos."""
    return sum(ord(char) for char in word) % _DIMENSIONS


def _count(text: str) -> int:
    """Cuenta palabras como aproximación barata de tokens."""
    return max(1, len(text.split()))
