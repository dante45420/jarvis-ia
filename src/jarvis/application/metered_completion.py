"""Caso de uso: ejecutar una completación y registrar su costo. Toda llamada de IA pasa por aquí."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from jarvis.domain.llm import LLMResult, Message
from jarvis.domain.ports import LLMProvider, UsageMeter
from jarvis.domain.pricing import PricingCatalog
from jarvis.domain.telemetry import Outcome, UsageRecord, compute_cost


@dataclass(frozen=True, slots=True)
class CompletionContext:
    """Describe una completación para la telemetría: qué modelo, para qué tarea y por qué canal."""

    model: str
    task: str
    channel: str
    request_id: str


class MeteredCompletion:
    """Envuelve un LLMProvider para que cada llamada quede registrada en la telemetría de costo."""

    def __init__(self, provider: LLMProvider, pricing: PricingCatalog, meter: UsageMeter) -> None:
        self._provider = provider
        self._pricing = pricing
        self._meter = meter

    async def run(
        self, context: CompletionContext, messages: list[Message], now: datetime
    ) -> LLMResult:
        """Ejecuta la completación, calcula el costo y emite un UsageRecord."""
        result = await self._provider.complete(context.model, messages)
        await self._meter.record(self._to_record(context, now, result))
        return result

    def _to_record(
        self, context: CompletionContext, now: datetime, result: LLMResult
    ) -> UsageRecord:
        """Traduce el resultado de la llamada en un registro de uso con su costo calculado."""
        price = self._pricing.price_for(context.model)
        cost = compute_cost(price, result.tokens_in, result.tokens_out)
        return UsageRecord(
            occurred_at=now,
            model=context.model,
            task=context.task,
            channel=context.channel,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost=cost,
            outcome=Outcome.LLM_CALL,
            request_id=context.request_id,
        )
