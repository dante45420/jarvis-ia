"""Tipos base de embeddings, independientes del proveedor."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    """Resultado de un embedding: el vector y los tokens consumidos (insumo del costo)."""

    vector: list[float]
    tokens: int


@dataclass(frozen=True, slots=True)
class BatchEmbeddingResult:
    """Resultado de embeber varios textos de una vez: los vectores en orden y los tokens totales."""

    vectors: list[list[float]]
    tokens: int
