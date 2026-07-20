"""DTOs de entrada/salida de las capacidades de Heraldo y su traducción desde el dominio."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from jarvis.modules.heraldo.domain import Cluster, TopicProfile


class StoryDTO(BaseModel):
    """Una historia lista para mostrar: título, enlace, alcance y sus fuentes."""

    title: str
    url: str
    reach: int
    sources: list[str]
    latest: datetime


class GatherInput(BaseModel):
    """Argumentos de la capacidad gather_stories: el perfil de búsqueda del tema."""

    subtopics: list[str]
    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    reach_threshold: int = 1
    recency_hours: int = 48


class GatherOutput(BaseModel):
    """Resultado de gather_stories: las historias ya filtradas y ordenadas."""

    stories: list[StoryDTO]


def to_profile(data: GatherInput) -> TopicProfile:
    """Construye el perfil de dominio a partir de los argumentos de la capacidad."""
    return TopicProfile(
        subtopics=tuple(data.subtopics),
        include_keywords=tuple(data.include_keywords),
        exclude_keywords=tuple(data.exclude_keywords),
        reach_threshold=data.reach_threshold,
        recency_hours=data.recency_hours,
    )


def to_story(cluster: Cluster) -> StoryDTO:
    """Traduce una historia del dominio al DTO de salida."""
    return StoryDTO(
        title=cluster.representative.title,
        url=cluster.representative.url,
        reach=cluster.reach,
        sources=sorted({member.source_name for member in cluster.members}),
        latest=cluster.latest,
    )
