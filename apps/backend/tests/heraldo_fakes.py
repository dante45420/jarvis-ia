"""Ayudas de prueba para Heraldo: una fuente falsa, un constructor de ítems y un armador de deps."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from jarvis.adapters.in_memory_push_tokens import InMemoryPushTokenStore
from jarvis.adapters.null_embedding import NullEmbeddingProvider
from jarvis.domain.llm import Message
from jarvis.domain.notifications import PushMessage
from jarvis.domain.ports import PushTokenStore
from jarvis.modules.actions import ModuleAction
from jarvis.modules.heraldo.angles import AngleMemory
from jarvis.modules.heraldo.dissection import DissectionService
from jarvis.modules.heraldo.domain import PodcastStyle, RawItem
from jarvis.modules.heraldo.gather import GatherService
from jarvis.modules.heraldo.in_memory_angles import InMemoryAngleStore
from jarvis.modules.heraldo.in_memory_deliveries import InMemoryDeliveryStore
from jarvis.modules.heraldo.in_memory_topics import InMemoryTopicStore
from jarvis.modules.heraldo.module import HeraldoDeps
from jarvis.modules.heraldo.news_cache import InMemoryNewsCardCache
from jarvis.modules.heraldo.news_card import NewsCardService
from jarvis.modules.heraldo.podcast_service import PodcastService
from jarvis.modules.heraldo.ports import SourceQuery
from jarvis.modules.heraldo.repository import DeliveryStore, TopicStore

_DEFAULT_NOW = datetime(2026, 7, 20, tzinfo=UTC)


class FakeInbox:
    """Bandeja falsa que acumula las acciones emitidas, para verificarlas en los tests."""

    def __init__(self) -> None:
        self.actions: list[ModuleAction] = []

    async def emit(self, action: ModuleAction) -> None:
        self.actions.append(action)


class FakeCompleter:
    """Completer falso: devuelve JSON predefinido por tarea, sin red. Guarda las tareas llamadas."""

    def __init__(self, responses: dict[str, str] | None = None, default: str = "{}") -> None:
        self._responses = responses or {}
        self._default = default
        self.calls: list[str] = []
        self.prompts: list[list[Message]] = []

    async def complete(self, task: str, messages: list[Message], now: datetime) -> str:
        self.calls.append(task)
        self.prompts.append(messages)
        return self._responses.get(task, self._default)


class FakeSynthesizer:
    """TTS falso: devuelve el guion como bytes, sin red. Guarda la última voz pedida."""

    def __init__(self) -> None:
        self.last_voice: str | None = None

    async def synthesize(self, text: str, style: PodcastStyle, voice: str | None = None) -> bytes:
        self.last_voice = voice
        return text.encode()


class FakePushSender:
    """PushSender falso: acumula los envíos (tokens + mensaje) para verificarlos en los tests."""

    def __init__(self) -> None:
        self.sent: list[tuple[list[str], PushMessage]] = []

    async def send(self, tokens: list[str], message: PushMessage) -> None:
        self.sent.append((tokens, message))


class FakeAudioStorage:
    """Almacenamiento falso: guarda en memoria y devuelve una URL simbólica."""

    def __init__(self) -> None:
        self.saved: dict[str, bytes] = {}

    async def store(self, key: str, audio: bytes) -> str:
        self.saved[key] = audio
        return f"memory://{key}"


class FakeSource:
    """Fuente de prueba que devuelve ítems predefinidos, ignorando la consulta."""

    def __init__(self, name: str, items: list[RawItem]) -> None:
        self._name = name
        self._items = items

    @property
    def name(self) -> str:
        return self._name

    async def fetch(self, query: SourceQuery) -> list[RawItem]:
        return list(self._items)


def make_item(
    title: str,
    source: str,
    *,
    url: str | None = None,
    hours_ago: int = 1,
    snippet: str = "",
    now: datetime = _DEFAULT_NOW,
) -> RawItem:
    """Construye un RawItem con valores por defecto razonables para los tests."""
    slug = title.replace(" ", "-")
    return RawItem(
        url=url or f"https://{source}.example/{slug}",
        title=title,
        snippet=snippet,
        source_name=source,
        published_at=now - timedelta(hours=hours_ago),
    )


def make_deps(
    *,
    gather: GatherService | None = None,
    topics: TopicStore | None = None,
    deliveries: DeliveryStore | None = None,
    dissection: DissectionService | None = None,
    news_cards: NewsCardService | None = None,
    podcast: PodcastService | None = None,
    angles: AngleMemory | None = None,
    push: FakePushSender | None = None,
    push_tokens: PushTokenStore | None = None,
    clock: Callable[[], datetime] | None = None,
    new_id: Callable[[], str] | None = None,
) -> HeraldoDeps:
    """Arma HeraldoDeps con implementaciones en memoria por defecto para los tests."""
    return HeraldoDeps(
        gather=gather or GatherService([]),
        topics=topics or InMemoryTopicStore(),
        deliveries=deliveries or InMemoryDeliveryStore(),
        dissection=dissection or DissectionService(FakeCompleter()),
        news_cards=news_cards or NewsCardService(FakeCompleter(), InMemoryNewsCardCache()),
        podcast=podcast or PodcastService(FakeCompleter(), FakeSynthesizer(), FakeAudioStorage()),
        angles=angles or AngleMemory(NullEmbeddingProvider(), InMemoryAngleStore()),
        push=push or FakePushSender(),
        push_tokens=push_tokens or InMemoryPushTokenStore(),
        clock=clock or (lambda: _DEFAULT_NOW),
        new_id=new_id or (lambda: "id-1"),
    )
