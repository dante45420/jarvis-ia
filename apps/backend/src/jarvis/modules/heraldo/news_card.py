"""Productor de tarjetas de noticias: IA perezosa, en lote y con caché.

Solo se resumen las historias que elegiste profundizar, todas en UNA sola llamada (batching), y
lo ya resumido se sirve del caché. La IA solo escribe las capas de texto; las fuentes son
determinísticas y vienen de la semilla.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from pydantic import BaseModel, Field

from jarvis.application.batching import BatchLimits, ItemCost, plan_batches
from jarvis.application.context import estimate_tokens
from jarvis.domain.llm import Message
from jarvis.modules.heraldo.dissection import Completer
from jarvis.modules.heraldo.jsonio import extract_json_object
from jarvis.modules.heraldo.news import NewsCard, StorySeed
from jarvis.modules.heraldo.news_cache import NewsCardCache

# Cada tarjeta genera una respuesta acotada (gancho + línea + 3 bullets + detalle + porqué).
_OUTPUT_TOKENS_PER_CARD = 220
_DEFAULT_LIMITS = BatchLimits(max_items=8, max_input_tokens=6000, max_output_tokens=2000)


class NewsCardService:
    """Convierte historias en tarjetas por capas, gastando IA solo en las nuevas."""

    def __init__(
        self, completer: Completer, cache: NewsCardCache, limits: BatchLimits = _DEFAULT_LIMITS
    ) -> None:
        self._completer = completer
        self._cache = cache
        self._limits = limits

    async def deepen(self, seeds: list[StorySeed], now: datetime) -> list[NewsCard]:
        """Devuelve las tarjetas de las historias, resumiendo en lote solo las que faltan."""
        cached = await self._cache.get_many([seed.id for seed in seeds])
        missing = [seed for seed in seeds if seed.id not in cached]
        fresh = await self._summarize_all(missing, now) if missing else []
        await self._cache.put_many(fresh)
        return _in_input_order(seeds, {**cached, **{card.story_id: card for card in fresh}})

    async def _summarize_all(self, seeds: list[StorySeed], now: datetime) -> list[NewsCard]:
        """Trocea las historias faltantes en lotes seguros y los resume en paralelo."""
        batches = plan_batches(seeds, _seed_cost, self._limits)
        results = await asyncio.gather(*(self._summarize(batch, now) for batch in batches))
        return [card for batch_cards in results for card in batch_cards]

    async def _summarize(self, seeds: list[StorySeed], now: datetime) -> list[NewsCard]:
        """Resume un lote de historias en una sola llamada y arma sus tarjetas."""
        text = await self._completer.complete("news_card", _cards_prompt(seeds), now)
        drafts = _CardsDraft.model_validate_json(extract_json_object(text)).cards
        seeds_by_id = {seed.id: seed for seed in seeds}
        return [_to_card(draft, seeds_by_id[draft.story_id])
                for draft in drafts if draft.story_id in seeds_by_id]


def _seed_cost(seed: StorySeed) -> ItemCost:
    """Estima el costo de una historia: tokens de entrada (su texto) y de salida (su tarjeta)."""
    return ItemCost(
        input_tokens=estimate_tokens(f"{seed.title} {seed.snippet}"),
        output_tokens=_OUTPUT_TOKENS_PER_CARD,
    )


class _CardDraft(BaseModel):
    """Las capas de texto de una tarjeta, tal como las devuelve el modelo."""

    story_id: str
    hook: str = ""
    one_line: str = ""
    key_points: list[str] = Field(default_factory=list)
    detail: str = ""
    why_it_matters: str = ""


class _CardsDraft(BaseModel):
    """El lote de tarjetas que devuelve el modelo en una llamada."""

    cards: list[_CardDraft] = Field(default_factory=list)


def _to_card(draft: _CardDraft, seed: StorySeed) -> NewsCard:
    """Combina las capas de texto del modelo con las fuentes determinísticas de la semilla."""
    return NewsCard(
        story_id=draft.story_id,
        hook=draft.hook,
        one_line=draft.one_line,
        key_points=tuple(draft.key_points),
        detail=draft.detail,
        why_it_matters=draft.why_it_matters,
        sources=seed.sources,
    )


def _in_input_order(seeds: list[StorySeed], by_id: dict[str, NewsCard]) -> list[NewsCard]:
    """Devuelve las tarjetas en el orden en que llegaron las historias."""
    return [by_id[seed.id] for seed in seeds if seed.id in by_id]


def _cards_prompt(seeds: list[StorySeed]) -> list[Message]:
    """Arma el prompt que pide, en lote, una tarjeta por capas para cada historia."""
    system = (
        "Resumes noticias para alguien con déficit de atención: quiere leer poquísimo y luego "
        "profundizar por capas. En español chileno (tuteo). Para cada historia entrega capas de "
        "menor a mayor detalle. Responde SOLO con JSON: "
        '{"cards": [{"story_id": "...", "hook": "titular corto y llamativo", '
        '"one_line": "la esencia en una línea", "key_points": ["3 micro-bullets"], '
        '"detail": "un párrafo corto", "why_it_matters": "por qué te importa"}]}. '
        "Usa exactamente el story_id que te doy."
    )
    return [Message("system", system), Message("user", _seeds_block(seeds))]


def _seeds_block(seeds: list[StorySeed]) -> str:
    """Renderiza las historias como texto compacto para el modelo."""
    return "\n".join(f"[{seed.id}] {seed.title}: {seed.snippet}" for seed in seeds)
