"""Test de la medición de costo de embeddings: cada lote emite un UsageRecord."""

from datetime import datetime

from jarvis.adapters.memory_usage_meter import InMemoryUsageMeter
from jarvis.adapters.metered_embedding import MeteredEmbeddingProvider
from jarvis.domain.pricing import PricingCatalog
from jarvis.domain.telemetry import ModelPrice, Outcome
from tests.fakes import FakeEmbeddingProvider

NOW = datetime(2026, 7, 17)


def _metered(meter: InMemoryUsageMeter) -> MeteredEmbeddingProvider:
    pricing = PricingCatalog({"bge": ModelPrice(input_per_million=0.01, output_per_million=0.0)})
    return MeteredEmbeddingProvider(
        FakeEmbeddingProvider(), model="bge", pricing=pricing, meter=meter, clock=lambda: NOW
    )


async def test_batch_embed_records_total_tokens() -> None:
    meter = InMemoryUsageMeter()
    result = await _metered(meter).embed_batch(["hola mundo", "otro texto"])
    assert len(meter.records) == 1
    record = meter.records[0]
    assert record.tokens_in == result.tokens
    assert record.outcome == Outcome.LLM_CALL
    assert record.task == "embed_memory"


async def test_single_embed_is_metered() -> None:
    meter = InMemoryUsageMeter()
    await _metered(meter).embed("hola")
    assert len(meter.records) == 1
