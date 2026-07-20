"""Test del MeteredCompleter: devuelve el texto y registra el costo de cada llamada."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.adapters.memory_usage_meter import InMemoryUsageMeter
from jarvis.application.metered_completer import MeteredCompleter
from jarvis.application.metered_completion import MeteredCompletion
from jarvis.domain.llm import LLMResult, Message
from jarvis.domain.pricing import PricingCatalog
from jarvis.domain.telemetry import ModelPrice

NOW = datetime(2026, 7, 20, tzinfo=UTC)


class _StubProvider:
    async def complete(self, model: str, messages: list[Message]) -> LLMResult:
        return LLMResult(text='{"questions": []}', tokens_in=100, tokens_out=50)


def _completer(meter: InMemoryUsageMeter) -> MeteredCompleter:
    pricing = PricingCatalog({"m": ModelPrice(input_per_million=1.0, output_per_million=2.0)})
    completion = MeteredCompletion(_StubProvider(), pricing, meter)
    return MeteredCompleter(completion, model="m", channel="web", new_id=lambda: "r1")


async def test_returns_text_and_records_usage() -> None:
    meter = InMemoryUsageMeter()
    text = await _completer(meter).complete("dissect_questions", [Message("user", "hola")], NOW)
    assert text == '{"questions": []}'
    assert len(meter.records) == 1
    assert meter.records[0].task == "dissect_questions"
    assert meter.records[0].cost == 0.0002
