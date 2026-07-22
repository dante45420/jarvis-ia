"""AngleStore en memoria: para arrancar sin base y para los tests. Similitud por coseno real."""

from __future__ import annotations

from jarvis.modules.heraldo.angles import EpisodeAngle
from jarvis.platform.vectors import cosine_similarity


class InMemoryAngleStore:
    """Guarda los ángulos en una lista y los recupera por similitud de coseno dentro del tema."""

    def __init__(self) -> None:
        self._angles: list[EpisodeAngle] = []

    async def add(self, angle: EpisodeAngle) -> None:
        """Agrega el ángulo a la memoria."""
        self._angles.append(angle)

    async def similar(self, topic_id: str, embedding: list[float], k: int) -> list[str]:
        """Devuelve los k resúmenes del tema más parecidos al vector, del más al menos similar."""
        ranked = sorted(self._of_topic(topic_id, embedding), key=lambda pair: pair[0], reverse=True)
        return [summary for _, summary in ranked[:k]]

    def _of_topic(self, topic_id: str, embedding: list[float]) -> list[tuple[float, str]]:
        """Puntúa los ángulos del tema por similitud con el vector de consulta."""
        return [
            (cosine_similarity(embedding, angle.embedding), angle.summary)
            for angle in self._angles
            if angle.topic_id == topic_id
        ]
