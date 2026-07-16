"""Test del caso de uso: cada completación queda registrada con su costo en la telemetría."""

from datetime import datetime

from jarvis.adapters.memory_usage_meter import InMemoryUsageMeter
from jarvis.application.metered_completion import CompletionContext, MeteredCompletion
from jarvis.domain.llm import LLMResult, Message
from jarvis.domain.pricing import PricingCatalog
from jarvis.domain.telemetry import ModelPrice, Outcome


class _StubProvider:
    """LLMProvider de prueba con un resultado fijo."""

    async def complete(self, model: str, messages: list[Message]) -> LLMResult:
        return LLMResult(text="ok", tokens_in=1000, tokens_out=2000)


async def test_run_records_cost_and_returns_result() -> None:
    meter = InMemoryUsageMeter()
    pricing = PricingCatalog({"m": ModelPrice(input_per_million=1.0, output_per_million=2.0)})
    use_case = MeteredCompletion(_StubProvider(), pricing, meter)
    context = CompletionContext(model="m", task="chat", channel="web", request_id="r1")

    result = await use_case.run(context, [Message("user", "hola")], datetime(2026, 7, 16))

    assert result.text == "ok"
    assert len(meter.records) == 1
    record = meter.records[0]
    assert record.cost == 0.005
    assert record.outcome == Outcome.LLM_CALL
    assert record.task == "chat"
    assert record.model == "m"
