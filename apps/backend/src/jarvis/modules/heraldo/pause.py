"""Políticas de pausa por tema. Determinísticas y por tema: pausar uno no afecta a los demás.

Hay dos políticas según el tipo de entrega:
- Podcast (estricta): si quedó una entrega sin consumir, deja de generar.
- Noticias (por ventana): siguen llegando salvo que pases 3 días sin responder ninguna.
Al pausar, Jarvis deja una acción en la Bandeja para que decidas retomar o descartar.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from enum import StrEnum

from jarvis.modules.actions import ActionInbox, ModuleAction
from jarvis.modules.heraldo.delivery import Delivery
from jarvis.modules.heraldo.domain import Topic, TopicState

_NEWS_SILENCE_WINDOW = timedelta(days=3)


class GenerationDecision(StrEnum):
    """Qué hacer al llegar el momento de generar la próxima entrega de un tema."""

    GENERATE = "generate"
    PAUSE = "pause"
    HOLD = "hold"


def decide_generation(state: TopicState, pending: Delivery | None) -> GenerationDecision:
    """Podcast (estricta): pausa si quedó algo sin consumir; espera si ya está pausado."""
    if state is TopicState.PAUSED:
        return GenerationDecision.HOLD
    if pending is not None and not pending.is_consumed:
        return GenerationDecision.PAUSE
    return GenerationDecision.GENERATE


def decide_news_generation(
    state: TopicState, last_response: datetime | None, now: datetime
) -> GenerationDecision:
    """Noticias (por ventana): siguen generando salvo 3 días sin ninguna respuesta.

    `last_response` es la referencia: la última vez que respondiste una noticia (cualquier
    respuesta cuenta) o, si nunca respondiste, cuándo empezó a acumularse contenido sin respuesta.
    None significa que no hay nada acumulado ni pendiente: se genera.
    """
    if state is TopicState.PAUSED:
        return GenerationDecision.HOLD
    if last_response is None:
        return GenerationDecision.GENERATE
    if now - last_response > _NEWS_SILENCE_WINDOW:
        return GenerationDecision.PAUSE
    return GenerationDecision.GENERATE


def pause(topic: Topic) -> Topic:
    """Deja el tema en pausa."""
    return replace(topic, state=TopicState.PAUSED)


def resume(topic: Topic) -> Topic:
    """Reactiva un tema pausado tras tu decisión."""
    return replace(topic, state=TopicState.ACTIVE)


class PauseController:
    """Evalúa si un tema debe generar y, al pausarlo, avisa a la Bandeja."""

    def __init__(self, inbox: ActionInbox) -> None:
        self._inbox = inbox

    async def evaluate(
        self, topic: Topic, pending: Delivery | None, now: datetime
    ) -> GenerationDecision:
        """Devuelve la decisión de generación y emite la acción de pausa cuando corresponde."""
        decision = decide_generation(topic.state, pending)
        if decision is GenerationDecision.PAUSE:
            await self._inbox.emit(_pause_action(topic, now))
        return decision


def _pause_action(topic: Topic, now: datetime) -> ModuleAction:
    """Arma la acción que se deja en la Bandeja cuando un tema se pausa."""
    return ModuleAction(
        owner_id=topic.owner_id,
        module_id="herald",
        kind="topic_paused",
        subject=topic.name,
        body=f"Pausé '{topic.name}': tienes una entrega sin ver. ¿La retomas o la descartas?",
        created_at=now,
    )
