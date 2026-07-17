"""Decorador que mide el costo de los embeddings. Mismo puerto EmbeddingProvider, con telemetría."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from jarvis.domain.embedding import BatchEmbeddingResult, EmbeddingResult
from jarvis.domain.ports import EmbeddingProvider, UsageMeter
from jarvis.domain.pricing import PricingCatalog
from jarvis.domain.telemetry import Outcome, UsageRecord, compute_cost

Clock = Callable[[], datetime]


class MeteredEmbeddingProvider:
    """Envuelve un EmbeddingProvider para registrar el costo de cada llamada de embedding."""

    def __init__(
        self,
        inner: EmbeddingProvider,
        model: str,
        pricing: PricingCatalog,
        meter: UsageMeter,
        clock: Clock,
        channel: str = "system",
        task: str = "embed_memory",
    ) -> None:
        self._inner = inner
        self._model = model
        self._pricing = pricing
        self._meter = meter
        self._clock = clock
        self._channel = channel
        self._task = task

    async def embed(self, text: str) -> EmbeddingResult:
        """Embebe un texto y registra su costo."""
        result = await self._inner.embed(text)
        await self._meter.record(self._to_record(result.tokens))
        return result

    async def embed_batch(self, texts: list[str]) -> BatchEmbeddingResult:
        """Embebe varios textos en una llamada y registra el costo total del lote."""
        result = await self._inner.embed_batch(texts)
        await self._meter.record(self._to_record(result.tokens))
        return result

    def _to_record(self, tokens: int) -> UsageRecord:
        """Arma el registro de uso de un embedding (solo tokens de entrada)."""
        price = self._pricing.price_for(self._model)
        return UsageRecord(
            occurred_at=self._clock(),
            model=self._model,
            task=self._task,
            channel=self._channel,
            tokens_in=tokens,
            tokens_out=0,
            cost=compute_cost(price, tokens, 0),
            outcome=Outcome.LLM_CALL,
            request_id="",
        )
