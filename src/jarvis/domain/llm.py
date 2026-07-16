"""Tipos base de interacción con modelos de lenguaje, independientes del proveedor."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Message:
    """Un mensaje de la conversación: rol (system/user/assistant) y contenido."""

    role: str
    content: str


@dataclass(frozen=True, slots=True)
class LLMResult:
    """Resultado de una completación: el texto y los tokens consumidos (insumo del costo)."""

    text: str
    tokens_in: int
    tokens_out: int
