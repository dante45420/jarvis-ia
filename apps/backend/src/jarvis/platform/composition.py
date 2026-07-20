"""Composition root: ensambla los módulos con sus adaptadores reales según la configuración.

Es el único lugar que conoce proveedores concretos. Para el carril inmediato usa Gemini directo
(evita el margen de OpenRouter cuando ya manejamos su key). Sin base de datos configurada, cae a
almacenes en memoria para poder arrancar y probar el plumbing.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine

from jarvis.adapters.audio import InMemoryAudioStorage, NullSpeechSynthesizer
from jarvis.adapters.gemini import GeminiProvider
from jarvis.adapters.memory_usage_meter import InMemoryUsageMeter
from jarvis.application.metered_completer import MeteredCompleter
from jarvis.application.metered_completion import MeteredCompletion
from jarvis.domain.pricing import PricingCatalog
from jarvis.domain.telemetry import ModelPrice
from jarvis.modules.core import Module, ModuleRegistry
from jarvis.modules.heraldo.dissection import DissectionService
from jarvis.modules.heraldo.gather import GatherService
from jarvis.modules.heraldo.in_memory_deliveries import InMemoryDeliveryStore
from jarvis.modules.heraldo.in_memory_topics import InMemoryTopicStore
from jarvis.modules.heraldo.module import HeraldoDeps, build_heraldo_module
from jarvis.modules.heraldo.news_cache import InMemoryNewsCardCache
from jarvis.modules.heraldo.news_card import NewsCardService
from jarvis.modules.heraldo.pg_deliveries import PgDeliveryStore
from jarvis.modules.heraldo.pg_topics import PgTopicStore
from jarvis.modules.heraldo.podcast_service import PodcastService
from jarvis.modules.heraldo.repository import DeliveryStore, TopicStore
from jarvis.modules.heraldo.sources.http_fetcher import HttpFeedFetcher
from jarvis.modules.heraldo.sources.rss import RssSource
from jarvis.platform.config import Settings
from jarvis.platform.db import create_session_factory


def build_registry(
    settings: Settings, client: httpx.AsyncClient, engine: AsyncEngine | None
) -> ModuleRegistry:
    """Arma el registro de módulos con sus dependencias reales."""
    registry = ModuleRegistry()
    registry.register(_build_heraldo(settings, client, engine))
    return registry


def _build_heraldo(
    settings: Settings, client: httpx.AsyncClient, engine: AsyncEngine | None
) -> Module:
    """Ensambla el módulo Heraldo inyectando proveedores y almacenes reales."""
    completer = _completer(settings, client)
    topics, deliveries = _stores(engine)
    deps = HeraldoDeps(
        gather=_gather(settings, client),
        topics=topics,
        deliveries=deliveries,
        dissection=DissectionService(completer),
        news_cards=NewsCardService(completer, InMemoryNewsCardCache()),
        podcast=PodcastService(completer, NullSpeechSynthesizer(), InMemoryAudioStorage()),
        clock=_utcnow,
        new_id=_new_id,
    )
    return build_heraldo_module(deps)


def _completer(settings: Settings, client: httpx.AsyncClient) -> MeteredCompleter:
    """Arma el Completer del carril inmediato: Gemini directo, con costo medido."""
    provider = GeminiProvider(settings.gemini_api_key, client)
    completion = MeteredCompletion(provider, _pricing(settings), InMemoryUsageMeter())
    return MeteredCompleter(completion, settings.gemini_text_model, channel="web", new_id=_new_id)


def _stores(engine: AsyncEngine | None) -> tuple[TopicStore, DeliveryStore]:
    """Elige almacenes Postgres si hay engine; si no, en memoria para arrancar sin base."""
    if engine is None:
        return InMemoryTopicStore(), InMemoryDeliveryStore()
    factory = create_session_factory(engine)
    return PgTopicStore(factory), PgDeliveryStore(factory)


def _gather(settings: Settings, client: httpx.AsyncClient) -> GatherService:
    """Arma el motor con las fuentes RSS configuradas (vacío si no hay feeds)."""
    feeds = [feed.strip() for feed in settings.heraldo_feeds.split(",") if feed.strip()]
    if not feeds:
        return GatherService([])
    return GatherService([RssSource(feeds, HttpFeedFetcher(client), _utcnow)])


def _pricing(settings: Settings) -> PricingCatalog:
    """Catálogo de precios para medir el costo del modelo de texto en uso."""
    return PricingCatalog(
        {settings.gemini_text_model: ModelPrice(input_per_million=0.30, output_per_million=2.50)}
    )


def _utcnow() -> datetime:
    """Reloj real en UTC."""
    return datetime.now(UTC)


def _new_id() -> str:
    """Genera un identificador único."""
    return uuid4().hex
