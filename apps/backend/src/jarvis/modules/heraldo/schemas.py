"""DTOs de entrada/salida de las capacidades de Heraldo y su traducción desde el dominio."""

from __future__ import annotations

import hashlib
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
from jarvis.modules.heraldo.news import NewsCard, StorySeed
from jarvis.modules.heraldo.normalize import canonical_url
from jarvis.modules.heraldo.podcast import Episode


class StoryDTO(BaseModel):
    """Una historia del menú: id estable, título, extracto, enlace, alcance y fuentes."""

    id: str
    title: str
    snippet: str
    url: str
    reach: int
    sources: list[str]
    latest: datetime


def story_id_for(url: str) -> str:
    """Id estable de una historia a partir de su URL canónica; sirve de clave de caché."""
    return hashlib.sha1(canonical_url(url).encode()).hexdigest()[:16]


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
    """Traduce una historia del dominio al DTO del menú, con su id estable."""
    representative = cluster.representative
    return StoryDTO(
        id=story_id_for(representative.url),
        title=representative.title,
        snippet=representative.snippet,
        url=representative.url,
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


class StorySeedInput(BaseModel):
    """Una historia seleccionada para profundizar; el cliente la reenvía desde el menú."""

    id: str
    title: str
    snippet: str = ""
    url: str
    sources: list[str] = Field(default_factory=list)


class NewsCardDTO(BaseModel):
    """Una tarjeta de noticia por capas, de lo más resumido a lo más detallado."""

    story_id: str
    hook: str
    one_line: str
    key_points: list[str]
    detail: str
    why_it_matters: str
    sources: list[str]


class DeepenStoriesInput(BaseModel):
    """Argumentos para profundizar las historias que seleccionaste (0 a todas)."""

    stories: list[StorySeedInput]


class DeepenStoriesOutput(BaseModel):
    """Las tarjetas por capas de las historias seleccionadas."""

    cards: list[NewsCardDTO]


def to_seed(data: StorySeedInput) -> StorySeed:
    """Construye la semilla de dominio a partir de la historia seleccionada."""
    return StorySeed(
        id=data.id,
        title=data.title,
        snippet=data.snippet,
        url=data.url,
        sources=tuple(data.sources),
    )


def to_card_dto(card: NewsCard) -> NewsCardDTO:
    """Traduce una tarjeta de dominio a su DTO de salida."""
    return NewsCardDTO(
        story_id=card.story_id,
        hook=card.hook,
        one_line=card.one_line,
        key_points=list(card.key_points),
        detail=card.detail,
        why_it_matters=card.why_it_matters,
        sources=list(card.sources),
    )


class EpisodeDTO(BaseModel):
    """Un episodio de podcast listo: título, guion, audio y fuentes."""

    id: str
    title: str
    script: str
    audio_url: str
    duration_minutes: int
    sources: list[str]


class ComposeEpisodeInput(BaseModel):
    """Argumentos para componer un episodio con las historias que seleccionaste."""

    stories: list[StorySeedInput]
    style: Literal["narrator", "dialogue"] = "narrator"
    minutes: int = 10
    voice: str | None = None


class VoiceDTO(BaseModel):
    """Una voz disponible para el podcast, con su carácter."""

    name: str
    vibe: str


class ListVoicesInput(BaseModel):
    """Sin argumentos: lista las voces disponibles."""


class ListVoicesOutput(BaseModel):
    """Las voces que puedes elegir para el podcast."""

    voices: list[VoiceDTO]


_GEMINI_VOICES: tuple[tuple[str, str], ...] = (
    ("Kore", "Firme"),
    ("Puck", "Animada"),
    ("Charon", "Informativa"),
    ("Aoede", "Ligera"),
    ("Leda", "Juvenil"),
    ("Orus", "Firme y grave"),
    ("Fenrir", "Enérgica"),
    ("Callirrhoe", "Relajada"),
    ("Enceladus", "Susurrante"),
    ("Iapetus", "Clara"),
    ("Umbriel", "Tranquila"),
    ("Algieba", "Suave"),
    ("Achird", "Amistosa"),
    ("Sulafat", "Cálida"),
    ("Gacrux", "Madura"),
)


def list_voices() -> list[VoiceDTO]:
    """Devuelve el catálogo curado de voces de Gemini para el podcast."""
    return [VoiceDTO(name=name, vibe=vibe) for name, vibe in _GEMINI_VOICES]


class ComposeEpisodeOutput(BaseModel):
    """El episodio recién producido."""

    episode: EpisodeDTO


def to_episode_dto(episode: Episode) -> EpisodeDTO:
    """Traduce un episodio de dominio a su DTO de salida."""
    return EpisodeDTO(
        id=episode.id,
        title=episode.title,
        script=episode.script,
        audio_url=episode.audio_url,
        duration_minutes=episode.duration_minutes,
        sources=list(episode.sources),
    )
