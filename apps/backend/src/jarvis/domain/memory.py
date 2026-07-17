"""Entidades de memoria: el log crudo y los hechos durables graph-ready (S-P-O + tiempo)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ConversationTurn:
    """Un turno del log de conversación. Fuente de verdad; nunca se inyecta entero al prompt."""

    owner_id: str
    role: str
    content: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class Fact:
    """Hecho durable del usuario, modelado graph-ready: sujeto–predicado–objeto + tiempo."""

    owner_id: str
    subject: str
    predicate: str
    object: str
    created_at: datetime

    def as_text(self) -> str:
        """Representación textual del hecho, usada para embeber y deduplicar."""
        return f"{self.subject} {self.predicate} {self.object}"


@dataclass(frozen=True, slots=True)
class EmbeddedFact:
    """Un hecho junto a su vector, listo para persistir en el almacén vectorial."""

    fact: Fact
    embedding: list[float]


@dataclass(frozen=True, slots=True)
class RetrievedFact:
    """Un hecho recuperado por similitud, con su puntaje respecto de la consulta."""

    fact: Fact
    similarity: float
