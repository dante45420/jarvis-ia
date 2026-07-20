"""Filtra y ordena historias según el perfil del tema. Puro código, cero IA."""

from __future__ import annotations

from datetime import datetime

from jarvis.modules.heraldo.domain import Cluster, TopicProfile


def filter_clusters(clusters: list[Cluster], profile: TopicProfile, now: datetime) -> list[Cluster]:
    """Deja solo las historias recientes, con alcance suficiente y que calzan con las keywords."""
    return [cluster for cluster in clusters if _passes(cluster, profile, now)]


def _passes(cluster: Cluster, profile: TopicProfile, now: datetime) -> bool:
    """Aplica los tres filtros del perfil a una historia."""
    return (
        _is_recent(cluster, profile.recency_hours, now)
        and cluster.reach >= profile.reach_threshold
        and _matches_keywords(cluster, profile)
    )


def _is_recent(cluster: Cluster, recency_hours: int, now: datetime) -> bool:
    """Indica si la historia cae dentro de la ventana de recencia."""
    return _hours_since(cluster.latest, now) <= recency_hours


def _matches_keywords(cluster: Cluster, profile: TopicProfile) -> bool:
    """Descarta lo que trae una keyword excluida; exige alguna incluida si hay lista."""
    text = _cluster_text(cluster)
    if any(keyword.lower() in text for keyword in profile.exclude_keywords):
        return False
    if not profile.include_keywords:
        return True
    return any(keyword.lower() in text for keyword in profile.include_keywords)


def _cluster_text(cluster: Cluster) -> str:
    """Texto representativo de la historia para buscar keywords."""
    item = cluster.representative
    return f"{item.title} {item.snippet}".lower()


def rank_clusters(clusters: list[Cluster], now: datetime) -> list[Cluster]:
    """Ordena las historias de mayor a menor relevancia: primero alcance, luego frescura."""
    return sorted(clusters, key=lambda cluster: _score(cluster, now), reverse=True)


def _score(cluster: Cluster, now: datetime) -> float:
    """Puntaje = alcance (peso fuerte) más un bono de recencia que decae con las horas."""
    return cluster.reach + _recency_factor(cluster, now)


def _recency_factor(cluster: Cluster, now: datetime) -> float:
    """Bono en (0, 1] que decae a medida que la historia envejece."""
    return 1 / (1 + _hours_since(cluster.latest, now))


def _hours_since(moment: datetime, now: datetime) -> float:
    """Horas transcurridas entre un momento y ahora."""
    return (now - moment).total_seconds() / 3600
