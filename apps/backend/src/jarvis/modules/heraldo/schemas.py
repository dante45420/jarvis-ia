"""DTOs de entrada/salida de las capacidades de Heraldo y su traducción desde el dominio."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from jarvis.modules.heraldo.domain import (
    Cluster,
    PodcastStyle,
    Topic,
    TopicProfile,
    TopicState,
)


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


class TopicDTO(BaseModel):
    """Un tema en su forma de salida: lo mínimo para listarlo y mostrar su estado."""

    id: str
    name: str
    state: str
    podcast_style: str


class CreateTopicInput(BaseModel):
    """Argumentos para crear un tema con su perfil de búsqueda explícito."""

    owner_id: str
    name: str
    subtopics: list[str]
    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    reach_threshold: int = 1
    recency_hours: int = 48
    podcast_style: Literal["narrator", "dialogue"] = "narrator"


class CreateTopicOutput(BaseModel):
    """Resultado de crear un tema."""

    topic: TopicDTO


class ListTopicsInput(BaseModel):
    """Argumentos para listar los temas de un usuario."""

    owner_id: str


class ListTopicsOutput(BaseModel):
    """Resultado de listar temas."""

    topics: list[TopicDTO]


def to_topic(data: CreateTopicInput, topic_id: str) -> Topic:
    """Construye un tema de dominio activo a partir de los argumentos de creación."""
    profile = TopicProfile(
        subtopics=tuple(data.subtopics),
        include_keywords=tuple(data.include_keywords),
        exclude_keywords=tuple(data.exclude_keywords),
        reach_threshold=data.reach_threshold,
        recency_hours=data.recency_hours,
    )
    return Topic(
        id=topic_id,
        owner_id=data.owner_id,
        name=data.name,
        profile=profile,
        podcast_style=PodcastStyle(data.podcast_style),
        state=TopicState.ACTIVE,
    )


def to_topic_dto(topic: Topic) -> TopicDTO:
    """Traduce un tema de dominio a su DTO de salida."""
    return TopicDTO(
        id=topic.id,
        name=topic.name,
        state=topic.state.value,
        podcast_style=topic.podcast_style.value,
    )
