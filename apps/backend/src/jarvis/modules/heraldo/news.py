"""Dominio del noticiero: la tarjeta por capas y la semilla que la origina.

La tarjeta va de lo mínimo a lo detallado para revelarse por capas al apretar (pensada para poca
lectura). Las fuentes son determinísticas (vienen de la semilla), no las inventa la IA.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StorySeed:
    """Lo mínimo para profundizar una historia: su referencia y su contenido crudo."""

    id: str
    title: str
    snippet: str
    url: str
    sources: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NewsCard:
    """Una noticia lista para leer por capas, de lo más resumido a lo más detallado."""

    story_id: str
    hook: str
    one_line: str
    key_points: tuple[str, ...]
    detail: str
    why_it_matters: str
    sources: tuple[str, ...]
