"""Scheduler de Heraldo: por cada tema activo decide generar o pausar. Cero IA.

Es el orquestador determinístico del carril asíncrono: consulta la última entrega de cada tema
y aplica la política de pausa. Los temas que quedan para generar los consume el generador (aún
por construir); los que tienen algo pendiente se pausan y avisan a la Bandeja.
"""

from __future__ import annotations

from datetime import datetime

from jarvis.modules.heraldo.domain import Topic
from jarvis.modules.heraldo.pause import GenerationDecision, PauseController, pause
from jarvis.modules.heraldo.repository import DeliveryStore, TopicStore


class TopicScheduler:
    """Planifica la generación: recorre los temas activos y resuelve cada uno."""

    def __init__(
        self, topics: TopicStore, deliveries: DeliveryStore, controller: PauseController
    ) -> None:
        self._topics = topics
        self._deliveries = deliveries
        self._controller = controller

    async def topics_to_generate(self, owner_id: str, now: datetime) -> list[Topic]:
        """Devuelve los temas activos que deben generar ahora; pausa los que tienen pendiente."""
        active = await self._topics.list_active(owner_id)
        planned = [await self._plan(topic, now) for topic in active]
        return [topic for topic in planned if topic is not None]

    async def _plan(self, topic: Topic, now: datetime) -> Topic | None:
        """Resuelve un tema: lo devuelve si toca generar, o lo pausa y devuelve None."""
        latest = await self._deliveries.latest_for_topic(topic.id)
        decision = await self._controller.evaluate(topic, latest, now)
        if decision is GenerationDecision.PAUSE:
            await self._topics.save(pause(topic))
            return None
        return topic if decision is GenerationDecision.GENERATE else None
