"""Dominio de Heraldo: el vocero que sigue tus temas (podcast, noticiero y búsqueda en vivo).

Todo el dominio es puro: no conoce fuentes concretas, ni IA, ni base de datos. El "alcance"
(reach) de una historia sale solo del clustering — cuántas fuentes independientes la cubren —,
sin gastar un token de IA.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TopicState(StrEnum):
    """Estado de seguimiento de un tema; la pausa evita generar contenido no consumido."""

    ACTIVE = "active"
    PAUSED = "paused"


class PodcastStyle(StrEnum):
    """Estilo del audio del podcast, configurable por tema."""

    NARRATOR = "narrator"
    DIALOGUE = "dialogue"


@dataclass(frozen=True, slots=True)
class RawItem:
    """Un ítem crudo traído por una fuente, ya normalizado a un formato común."""

    url: str
    title: str
    snippet: str
    source_name: str
    published_at: datetime


@dataclass(frozen=True, slots=True)
class Cluster:
    """Una historia: varios ítems de fuentes distintas que cuentan lo mismo."""

    representative: RawItem
    members: tuple[RawItem, ...]

    @property
    def reach(self) -> int:
        """Alcance: cuántas fuentes independientes cubren la historia. La señal contra el ruido."""
        return len({item.source_name for item in self.members})

    @property
    def latest(self) -> datetime:
        """Momento más reciente en que alguna fuente publicó la historia."""
        return max(item.published_at for item in self.members)


@dataclass(frozen=True, slots=True)
class TopicProfile:
    """Resultado de diseccionar un tema: qué buscar, qué filtrar y con qué exigencia de alcance."""

    subtopics: tuple[str, ...]
    include_keywords: tuple[str, ...]
    exclude_keywords: tuple[str, ...]
    reach_threshold: int
    recency_hours: int


@dataclass(frozen=True, slots=True)
class Topic:
    """Un tema que sigues, con su perfil de búsqueda, estilo de podcast y estado de seguimiento."""

    id: str
    owner_id: str
    name: str
    profile: TopicProfile
    podcast_style: PodcastStyle
    state: TopicState
