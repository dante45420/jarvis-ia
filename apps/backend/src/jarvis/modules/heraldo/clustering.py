"""Agrupa ítems que cuentan la misma historia. De aquí sale el alcance, sin IA."""

from __future__ import annotations

from jarvis.modules.heraldo.domain import Cluster, RawItem
from jarvis.modules.heraldo.normalize import canonical_url, title_tokens


def cluster_items(items: list[RawItem], similarity_threshold: float) -> list[Cluster]:
    """Agrupa ítems por URL canónica o títulos similares en historias (clusters)."""
    groups: list[list[RawItem]] = []
    for item in items:
        _place_item(item, groups, similarity_threshold)
    return [_to_cluster(group) for group in groups]


def _place_item(item: RawItem, groups: list[list[RawItem]], threshold: float) -> None:
    """Ubica el ítem en un grupo existente si encaja; si no, abre uno nuevo."""
    for group in groups:
        if _belongs(item, group[0], threshold):
            group.append(item)
            return
    groups.append([item])


def _belongs(item: RawItem, representative: RawItem, threshold: float) -> bool:
    """Indica si el ítem pertenece al grupo: misma URL canónica o título suficientemente similar."""
    if canonical_url(item.url) == canonical_url(representative.url):
        return True
    return _title_similarity(item.title, representative.title) >= threshold


def _title_similarity(first: str, second: str) -> float:
    """Similitud de Jaccard entre los tokens de dos títulos."""
    return _jaccard(title_tokens(first), title_tokens(second))


def _jaccard(first: frozenset[str], second: frozenset[str]) -> float:
    """Índice de Jaccard entre dos conjuntos; 0 si alguno está vacío."""
    if not first or not second:
        return 0.0
    return len(first & second) / len(first | second)


def _to_cluster(group: list[RawItem]) -> Cluster:
    """Construye un cluster tomando como representante el ítem más reciente del grupo."""
    representative = max(group, key=lambda item: item.published_at)
    return Cluster(representative=representative, members=tuple(group))
