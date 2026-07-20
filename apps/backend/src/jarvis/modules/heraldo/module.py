"""Ensamblado del módulo Heraldo: expone sus capacidades MCP-ready para Córtex."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from jarvis.modules.core import Capability, CapabilityHandler, Module
from jarvis.modules.heraldo.gather import GatherService
from jarvis.modules.heraldo.repository import TopicStore
from jarvis.modules.heraldo.schemas import (
    CreateTopicInput,
    CreateTopicOutput,
    GatherInput,
    GatherOutput,
    ListTopicsInput,
    ListTopicsOutput,
    to_profile,
    to_story,
    to_topic,
    to_topic_dto,
)

Clock = Callable[[], datetime]
IdFactory = Callable[[], str]


def build_heraldo_module(
    gather: GatherService, topics: TopicStore, clock: Clock, new_id: IdFactory
) -> Module:
    """Arma el módulo Heraldo con sus capacidades, listo para registrarse."""
    return Module(
        id="herald",
        name="Heraldo",
        description="Tu vocero: podcast, noticiero y búsqueda en vivo sobre los temas que sigues.",
        capabilities=(
            _create_topic_capability(topics, new_id),
            _list_topics_capability(topics),
            _gather_capability(gather, clock),
        ),
    )


def _create_topic_capability(topics: TopicStore, new_id: IdFactory) -> Capability:
    return Capability(
        name="create_topic",
        description="Crea un tema a seguir con su perfil de búsqueda. Determinístico.",
        input_model=CreateTopicInput,
        output_model=CreateTopicOutput,
        handler=_create_topic_handler(topics, new_id),
    )


def _list_topics_capability(topics: TopicStore) -> Capability:
    return Capability(
        name="list_topics",
        description="Lista los temas que sigue un usuario.",
        input_model=ListTopicsInput,
        output_model=ListTopicsOutput,
        handler=_list_topics_handler(topics),
    )


def _gather_capability(gather: GatherService, clock: Clock) -> Capability:
    return Capability(
        name="gather_stories",
        description="Reúne y ordena historias de un tema desde todas las fuentes, sin IA.",
        input_model=GatherInput,
        output_model=GatherOutput,
        handler=_gather_handler(gather, clock),
    )


def _create_topic_handler(topics: TopicStore, new_id: IdFactory) -> CapabilityHandler:
    async def handle(args: CreateTopicInput) -> CreateTopicOutput:
        topic = to_topic(args, new_id())
        await topics.save(topic)
        return CreateTopicOutput(topic=to_topic_dto(topic))

    return handle


def _list_topics_handler(topics: TopicStore) -> CapabilityHandler:
    async def handle(args: ListTopicsInput) -> ListTopicsOutput:
        found = await topics.list_by_owner(args.owner_id)
        return ListTopicsOutput(topics=[to_topic_dto(topic) for topic in found])

    return handle


def _gather_handler(gather: GatherService, clock: Clock) -> CapabilityHandler:
    async def handle(args: GatherInput) -> GatherOutput:
        clusters = await gather.gather(to_profile(args), clock())
        return GatherOutput(stories=[to_story(cluster) for cluster in clusters])

    return handle
