"""DTOs de entrada/salida de las capacidades de Heraldo y su traducción desde el dominio."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from jarvis.modules.heraldo.delivery import Delivery, DeliveryKind
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


class ProposeQuestionsInput(BaseModel):
    """Argumentos para pedir las preguntas de disección de un tema."""

    name: str


class ProposeQuestionsOutput(BaseModel):
    """Las preguntas dirigidas que Jarvis hace para acotar el tema."""

    questions: list[str]


class QAItem(BaseModel):
    """Una pregunta de disección con la respuesta del usuario."""

    question: str
    answer: str


class CompileProfileInput(BaseModel):
    """Argumentos para compilar el perfil y crear el tema desde las respuestas."""

    owner_id: str
    name: str
    podcast_style: Literal["narrator", "dialogue"] = "narrator"
    answers: list[QAItem]


class CompileProfileOutput(BaseModel):
    """El tema recién creado a partir de la disección."""

    topic: TopicDTO


def build_topic(
    owner_id: str, name: str, profile: TopicProfile, style: str, topic_id: str
) -> Topic:
    """Construye un tema activo a partir de un perfil ya compilado."""
    return Topic(
        id=topic_id,
        owner_id=owner_id,
        name=name,
        profile=profile,
        podcast_style=PodcastStyle(style),
        state=TopicState.ACTIVE,
    )


class DeliveryDTO(BaseModel):
    """Una entrega en su forma de salida, con su marca de consumo."""

    id: str
    topic_id: str
    kind: str
    created_at: datetime
    consumed: bool


class RecordDeliveryInput(BaseModel):
    """Argumentos para registrar una entrega recién producida por un tema."""

    topic_id: str
    kind: Literal["podcast", "news"]


class RecordDeliveryOutput(BaseModel):
    """Resultado de registrar una entrega."""

    delivery: DeliveryDTO


class MarkConsumedInput(BaseModel):
    """Argumentos para marcar una entrega como consumida."""

    delivery_id: str


class MarkConsumedOutput(BaseModel):
    """Resultado de marcar una entrega: la entrega actualizada, o none si no existe."""

    delivery: DeliveryDTO | None


def to_delivery(data: RecordDeliveryInput, delivery_id: str, now: datetime) -> Delivery:
    """Construye una entrega de dominio no consumida a partir de los argumentos."""
    return Delivery(
        id=delivery_id,
        topic_id=data.topic_id,
        kind=DeliveryKind(data.kind),
        created_at=now,
    )


def to_delivery_dto(delivery: Delivery) -> DeliveryDTO:
    """Traduce una entrega de dominio a su DTO de salida."""
    return DeliveryDTO(
        id=delivery.id,
        topic_id=delivery.topic_id,
        kind=delivery.kind.value,
        created_at=delivery.created_at,
        consumed=delivery.is_consumed,
    )
