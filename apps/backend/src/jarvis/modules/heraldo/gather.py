"""Motor de reunión: junta las fuentes en paralelo y entrega historias ordenadas. Cero IA."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import datetime

from jarvis.modules.heraldo.clustering import cluster_items
from jarvis.modules.heraldo.domain import Cluster, RawItem, TopicProfile
from jarvis.modules.heraldo.ports import SourceAdapter, SourceQuery
from jarvis.modules.heraldo.ranking import filter_clusters, rank_clusters


class GatherService:
    """Orquesta el pipeline determinístico: traer → agrupar → filtrar → rankear."""

    def __init__(self, sources: Sequence[SourceAdapter], similarity_threshold: float = 0.6) -> None:
        self._sources = tuple(sources)
        self._threshold = similarity_threshold

    async def gather(self, profile: TopicProfile, now: datetime) -> list[Cluster]:
        """Reúne y ordena las historias de un perfil de tema desde todas las fuentes."""
        items = await self._fetch_all(_query_for(profile))
        clusters = cluster_items(items, self._threshold)
        recent = filter_clusters(clusters, profile, now)
        return rank_clusters(recent, now)

    async def _fetch_all(self, query: SourceQuery) -> list[RawItem]:
        """Consulta todas las fuentes en paralelo y aplana sus resultados."""
        batches: list[list[RawItem]] = await asyncio.gather(
            *(source.fetch(query) for source in self._sources)
        )
        return [item for batch in batches for item in batch]


def _query_for(profile: TopicProfile) -> SourceQuery:
    """Traduce el perfil del tema en la consulta que reciben las fuentes."""
    return SourceQuery(
        subtopics=profile.subtopics,
        include_keywords=profile.include_keywords,
        recency_hours=profile.recency_hours,
    )
