"""Ensamblado del módulo Heraldo: expone sus capacidades MCP-ready para Córtex."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from jarvis.modules.core import Capability, CapabilityHandler, Module
from jarvis.modules.heraldo.dissection import DissectionService, QuestionAnswer
from jarvis.modules.heraldo.gather import GatherService
from jarvis.modules.heraldo.news_card import NewsCardService
from jarvis.modules.heraldo.repository import DeliveryStore, TopicStore
from jarvis.modules.heraldo.schemas import (
    CompileProfileInput,
    CompileProfileOutput,
    CreateTopicInput,
    CreateTopicOutput,
    DeepenStoriesInput,
    DeepenStoriesOutput,
    GatherInput,
    GatherOutput,
    ListTopicsInput,
    ListTopicsOutput,
    MarkConsumedInput,
    MarkConsumedOutput,
    ProposeQuestionsInput,
    ProposeQuestionsOutput,
    RecordDeliveryInput,
    RecordDeliveryOutput,
    build_topic,
    to_card_dto,
    to_delivery,
    to_delivery_dto,
    to_profile,
    to_seed,
    to_story,
    to_topic,
    to_topic_dto,
)

Clock = Callable[[], datetime]
IdFactory = Callable[[], str]


@dataclass(frozen=True, slots=True)
class HeraldoDeps:
    """Colaboradores que Heraldo necesita para operar; se inyectan al ensamblar el módulo."""

    gather: GatherService
    topics: TopicStore
    deliveries: DeliveryStore
    dissection: DissectionService
    news_cards: NewsCardService
    clock: Clock
    new_id: IdFactory


def build_heraldo_module(deps: HeraldoDeps) -> Module:
    """Arma el módulo Heraldo con sus capacidades, listo para registrarse."""
    return Module(
        id="herald",
        name="Heraldo",
        description="Tu vocero: podcast, noticiero y búsqueda en vivo sobre los temas que sigues.",
        capabilities=(
            _propose_questions_capability(deps),
            _compile_profile_capability(deps),
            _create_topic_capability(deps),
            _list_topics_capability(deps),
            _gather_capability(deps),
            _deepen_stories_capability(deps),
            _record_delivery_capability(deps),
            _mark_consumed_capability(deps),
        ),
    )


def _deepen_stories_capability(deps: HeraldoDeps) -> Capability:
    return Capability(
        name="deepen_stories",
        description="Profundiza historias elegidas en tarjetas por capas; IA solo en las nuevas.",
        input_model=DeepenStoriesInput,
        output_model=DeepenStoriesOutput,
        handler=_deepen_stories_handler(deps),
    )


def _propose_questions_capability(deps: HeraldoDeps) -> Capability:
    return Capability(
        name="propose_topic_questions",
        description="Genera preguntas dirigidas para acotar un tema antes de crearlo.",
        input_model=ProposeQuestionsInput,
        output_model=ProposeQuestionsOutput,
        handler=_propose_questions_handler(deps),
    )


def _compile_profile_capability(deps: HeraldoDeps) -> Capability:
    return Capability(
        name="compile_topic_profile",
        description="Compila el perfil desde tus respuestas y crea el tema.",
        input_model=CompileProfileInput,
        output_model=CompileProfileOutput,
        handler=_compile_profile_handler(deps),
    )


def _create_topic_capability(deps: HeraldoDeps) -> Capability:
    return Capability(
        name="create_topic",
        description="Crea un tema a seguir con su perfil de búsqueda. Determinístico.",
        input_model=CreateTopicInput,
        output_model=CreateTopicOutput,
        handler=_create_topic_handler(deps),
    )


def _list_topics_capability(deps: HeraldoDeps) -> Capability:
    return Capability(
        name="list_topics",
        description="Lista los temas que sigue un usuario.",
        input_model=ListTopicsInput,
        output_model=ListTopicsOutput,
        handler=_list_topics_handler(deps),
    )


def _gather_capability(deps: HeraldoDeps) -> Capability:
    return Capability(
        name="gather_stories",
        description="Reúne y ordena historias de un tema desde todas las fuentes, sin IA.",
        input_model=GatherInput,
        output_model=GatherOutput,
        handler=_gather_handler(deps),
    )


def _record_delivery_capability(deps: HeraldoDeps) -> Capability:
    return Capability(
        name="record_delivery",
        description="Registra una entrega (podcast o noticiero) recién producida por un tema.",
        input_model=RecordDeliveryInput,
        output_model=RecordDeliveryOutput,
        handler=_record_delivery_handler(deps),
    )


def _mark_consumed_capability(deps: HeraldoDeps) -> Capability:
    return Capability(
        name="mark_delivery_consumed",
        description="Marca una entrega como consumida al abrirla o reproducirla.",
        input_model=MarkConsumedInput,
        output_model=MarkConsumedOutput,
        handler=_mark_consumed_handler(deps),
    )


def _propose_questions_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: ProposeQuestionsInput) -> ProposeQuestionsOutput:
        questions = await deps.dissection.propose_questions(args.name, deps.clock())
        return ProposeQuestionsOutput(questions=questions)

    return handle


def _compile_profile_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: CompileProfileInput) -> CompileProfileOutput:
        answers = [QuestionAnswer(item.question, item.answer) for item in args.answers]
        profile = await deps.dissection.compile_profile(args.name, answers, deps.clock())
        topic = build_topic(args.owner_id, args.name, profile, args.podcast_style, deps.new_id())
        await deps.topics.save(topic)
        return CompileProfileOutput(topic=to_topic_dto(topic))

    return handle


def _deepen_stories_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: DeepenStoriesInput) -> DeepenStoriesOutput:
        seeds = [to_seed(story) for story in args.stories]
        cards = await deps.news_cards.deepen(seeds, deps.clock())
        return DeepenStoriesOutput(cards=[to_card_dto(card) for card in cards])

    return handle


def _create_topic_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: CreateTopicInput) -> CreateTopicOutput:
        topic = to_topic(args, deps.new_id())
        await deps.topics.save(topic)
        return CreateTopicOutput(topic=to_topic_dto(topic))

    return handle


def _list_topics_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: ListTopicsInput) -> ListTopicsOutput:
        found = await deps.topics.list_by_owner(args.owner_id)
        return ListTopicsOutput(topics=[to_topic_dto(topic) for topic in found])

    return handle


def _gather_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: GatherInput) -> GatherOutput:
        clusters = await deps.gather.gather(to_profile(args), deps.clock())
        return GatherOutput(stories=[to_story(cluster) for cluster in clusters])

    return handle


def _record_delivery_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: RecordDeliveryInput) -> RecordDeliveryOutput:
        delivery = to_delivery(args, deps.new_id(), deps.clock())
        await deps.deliveries.add(delivery)
        return RecordDeliveryOutput(delivery=to_delivery_dto(delivery))

    return handle


def _mark_consumed_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: MarkConsumedInput) -> MarkConsumedOutput:
        updated = await deps.deliveries.mark_consumed(args.delivery_id, deps.clock())
        dto = to_delivery_dto(updated) if updated is not None else None
        return MarkConsumedOutput(delivery=dto)

    return handle
