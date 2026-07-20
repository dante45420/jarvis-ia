"""Almacén de temas en memoria: implementación liviana para tests y wiring temprano."""

from __future__ import annotations

from jarvis.modules.heraldo.domain import Topic, TopicState


class InMemoryTopicStore:
    """Guarda los temas en un diccionario. Cumple TopicStore sin tocar la base de datos."""

    def __init__(self) -> None:
        self._topics: dict[str, Topic] = {}

    async def save(self, topic: Topic) -> None:
        self._topics[topic.id] = topic

    async def get(self, topic_id: str) -> Topic | None:
        return self._topics.get(topic_id)

    async def list_by_owner(self, owner_id: str) -> list[Topic]:
        return [topic for topic in self._topics.values() if topic.owner_id == owner_id]

    async def list_active(self, owner_id: str) -> list[Topic]:
        return [topic for topic in await self.list_by_owner(owner_id)
                if topic.state is TopicState.ACTIVE]
