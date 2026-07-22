"""Ensamblado del módulo Heraldo: expone sus capacidades MCP-ready para Córtex."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from jarvis.domain.notifications import PushMessage, PushToken
from jarvis.domain.ports import PushSender, PushTokenStore
from jarvis.modules.core import Capability, CapabilityHandler, Module
from jarvis.modules.heraldo.angles import AngleMemory
from jarvis.modules.heraldo.cadence import is_due
from jarvis.modules.heraldo.dissection import DissectionService, QuestionAnswer
from jarvis.modules.heraldo.domain import PodcastStyle, Topic
from jarvis.modules.heraldo.gather import GatherService
from jarvis.modules.heraldo.news_card import NewsCardService
from jarvis.modules.heraldo.onboarding import compile_instruction
from jarvis.modules.heraldo.podcast_service import PodcastService
from jarvis.modules.heraldo.repository import DeliveryStore, TopicStore
from jarvis.modules.heraldo.schemas import (
    CompileProfileInput,
    CompileProfileOutput,
    ComposeEpisodeInput,
    ComposeEpisodeOutput,
    CreateTopicInput,
    CreateTopicOutput,
    DeepenStoriesInput,
    DeepenStoriesOutput,
    DueTopicDTO,
    DueTopicsInput,
    DueTopicsOutput,
    GatherInput,
    GatherOutput,
    ListTopicsInput,
    ListTopicsOutput,
    ListVoicesInput,
    ListVoicesOutput,
    MarkConsumedInput,
    MarkConsumedOutput,
    ProposeQuestionsInput,
    ProposeQuestionsOutput,
    RecordDeliveryInput,
    RecordDeliveryOutput,
    RegisterPushTokenInput,
    RegisterPushTokenOutput,
    RunSchedulerTickInput,
    RunSchedulerTickOutput,
    StorySeedInput,
    build_onboarding_form,
    build_topic,
    list_voices,
    to_card_dto,
    to_delivery,
    to_delivery_dto,
    to_episode_dto,
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
    podcast: PodcastService
    angles: AngleMemory
    push: PushSender
    push_tokens: PushTokenStore
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
            _compose_episode_capability(deps),
            _list_voices_capability(deps),
            _record_delivery_capability(deps),
            _mark_consumed_capability(deps),
            _due_topics_capability(deps),
            _register_push_token_capability(deps),
            _run_scheduler_tick_capability(deps),
        ),
    )


def _due_topics_capability(deps: HeraldoDeps) -> Capability:
    return Capability(
        name="due_topics",
        description="Lista los temas cuyo podcast toca generar ahora según su cadencia. Cero IA.",
        input_model=DueTopicsInput,
        output_model=DueTopicsOutput,
        handler=_due_topics_handler(deps),
    )


def _register_push_token_capability(deps: HeraldoDeps) -> Capability:
    return Capability(
        name="register_push_token",
        description="Registra el token de push de un dispositivo para avisar al usuario.",
        input_model=RegisterPushTokenInput,
        output_model=RegisterPushTokenOutput,
        handler=_register_push_token_handler(deps),
    )


def _run_scheduler_tick_capability(deps: HeraldoDeps) -> Capability:
    return Capability(
        name="run_scheduler_tick",
        description="Revisa la cadencia y avisa por push los podcasts que tocan. Cero IA.",
        input_model=RunSchedulerTickInput,
        output_model=RunSchedulerTickOutput,
        handler=_run_scheduler_tick_handler(deps),
    )


def _list_voices_capability(deps: HeraldoDeps) -> Capability:
    return Capability(
        name="list_voices",
        description="Lista las voces disponibles para elegir en el podcast.",
        input_model=ListVoicesInput,
        output_model=ListVoicesOutput,
        handler=_list_voices_handler(deps),
    )


def _compose_episode_capability(deps: HeraldoDeps) -> Capability:
    return Capability(
        name="compose_episode",
        description="Compone un episodio desde las historias elegidas: guion, voz y audio.",
        input_model=ComposeEpisodeInput,
        output_model=ComposeEpisodeOutput,
        handler=_compose_episode_handler(deps),
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
        onboarding = build_onboarding_form(
            args.objective, args.objective_note, args.style, args.answers
        )
        topic = build_topic(
            args.owner_id, args.name, profile, args.podcast_style, deps.new_id(),
            args.cadence.to_cadence(), onboarding,
        )
        await deps.topics.save(topic)
        return CompileProfileOutput(topic=to_topic_dto(topic))

    return handle


def _deepen_stories_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: DeepenStoriesInput) -> DeepenStoriesOutput:
        seeds = [to_seed(story) for story in args.stories]
        instruction = await _news_instruction(deps, args.topic_id)
        cards = await deps.news_cards.deepen(seeds, deps.clock(), instruction)
        return DeepenStoriesOutput(cards=[to_card_dto(card) for card in cards])

    return handle


def _compose_episode_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: ComposeEpisodeInput) -> ComposeEpisodeOutput:
        seeds = [to_seed(story) for story in args.stories]
        topic = await _load_topic(deps, args.topic_id)
        instruction = await _podcast_instruction(deps, topic, args.stories)
        episode = await deps.podcast.compose(
            seeds, PodcastStyle(args.style), args.minutes, deps.clock(), deps.new_id(),
            args.voice, instruction,
        )
        await _remember_angle(deps, topic, episode.angle)
        return ComposeEpisodeOutput(episode=to_episode_dto(episode))

    return handle


async def _load_topic(deps: HeraldoDeps, topic_id: str | None) -> Topic | None:
    """Carga el tema si vino un id; None si el pedido no está ligado a un tema guardado."""
    return await deps.topics.get(topic_id) if topic_id else None


async def _podcast_instruction(
    deps: HeraldoDeps, topic: Topic | None, stories: list[StorySeedInput]
) -> str:
    """Compila la instrucción del podcast con el onboarding y los ángulos ya tratados del tema."""
    if topic is None or topic.onboarding is None:
        return ""
    covered = await deps.angles.covered(topic.id, _seeds_query(stories))
    return compile_instruction(topic.onboarding, topic.name, covered)


async def _news_instruction(deps: HeraldoDeps, topic_id: str | None) -> str:
    """Compila la instrucción del noticiero con el onboarding del tema, si lo hay."""
    topic = await _load_topic(deps, topic_id)
    if topic is None or topic.onboarding is None:
        return ""
    return compile_instruction(topic.onboarding, topic.name)


async def _remember_angle(deps: HeraldoDeps, topic: Topic | None, angle: str) -> None:
    """Guarda el ángulo del episodio para no repetirlo la próxima vez, si el tema está guardado."""
    if topic is not None:
        await deps.angles.remember(topic.id, angle, deps.clock())


def _seeds_query(stories: list[StorySeedInput]) -> str:
    """Texto de consulta para recuperar ángulos: los títulos y extractos de las historias."""
    return " ".join(f"{story.title} {story.snippet}" for story in stories)


def _due_topics_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: DueTopicsInput) -> DueTopicsOutput:
        now = deps.clock()
        active = await deps.topics.list_active(args.owner_id)
        due = [topic for topic in active if await _is_topic_due(deps, topic, now)]
        return DueTopicsOutput(topics=[DueTopicDTO(topic_id=t.id, name=t.name) for t in due])

    return handle


async def _is_topic_due(deps: HeraldoDeps, topic: Topic, now: datetime) -> bool:
    """Indica si al tema le toca generar podcast ahora, según su cadencia y última entrega."""
    latest = await deps.deliveries.latest_for_topic(topic.id)
    latest_at = latest.created_at if latest is not None else None
    return is_due(topic.cadence, latest_at, now)


def _register_push_token_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: RegisterPushTokenInput) -> RegisterPushTokenOutput:
        token = PushToken(args.owner_id, args.token, args.platform, deps.clock())
        await deps.push_tokens.save(token)
        return RegisterPushTokenOutput(ok=True)

    return handle


def _run_scheduler_tick_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: RunSchedulerTickInput) -> RunSchedulerTickOutput:
        now = deps.clock()
        active = await deps.topics.list_active(args.owner_id)
        due = [topic for topic in active if await _is_topic_due(deps, topic, now)]
        notified = await _notify_due(deps, args.owner_id, due)
        return RunSchedulerTickOutput(notified=notified, topics=[topic.name for topic in due])

    return handle


async def _notify_due(deps: HeraldoDeps, owner_id: str, due: list[Topic]) -> int:
    """Avisa por push cada podcast que toca; devuelve cuántos se avisaron (0 sin dispositivos)."""
    if not due:
        return 0
    tokens = [item.token for item in await deps.push_tokens.list_for_owner(owner_id)]
    if not tokens:
        return 0
    for topic in due:
        await deps.push.send(tokens, _due_message(topic))
    return len(due)


def _due_message(topic: Topic) -> PushMessage:
    """Arma el aviso que pide tu aprobación para generar el podcast del tema."""
    return PushMessage(
        title="Jarvis",
        body=f"¿Generamos hoy tu podcast de {topic.name}?",
        data={"topic_id": topic.id, "name": topic.name, "action": "approve_podcast"},
    )


def _list_voices_handler(deps: HeraldoDeps) -> CapabilityHandler:
    async def handle(args: ListVoicesInput) -> ListVoicesOutput:
        return ListVoicesOutput(voices=list_voices())

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
