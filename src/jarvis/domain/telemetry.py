"""Telemetría de costo: el registro base que alimenta el dashboard de gasto en IA."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Outcome(StrEnum):
    """Cómo se resolvió un request, para medir cuánto se ahorró evitando el LLM."""

    LLM_CALL = "llm_call"
    CACHE_HIT = "cache_hit"
    DETERMINISTIC = "deterministic"


@dataclass(frozen=True, slots=True)
class ModelPrice:
    """Precio de un modelo, en USD por millón de tokens."""

    input_per_million: float
    output_per_million: float


@dataclass(frozen=True, slots=True)
class UsageRecord:
    """Un evento de uso de IA; la unidad que el dashboard agrega por modelo, tarea y día."""

    occurred_at: datetime
    model: str
    task: str
    channel: str
    tokens_in: int
    tokens_out: int
    cost: float
    outcome: Outcome
    request_id: str


def compute_cost(price: ModelPrice, tokens_in: int, tokens_out: int) -> float:
    """Calcula el costo en USD a partir del precio del modelo y los tokens consumidos."""
    input_cost = price.input_per_million * tokens_in / 1_000_000
    output_cost = price.output_per_million * tokens_out / 1_000_000
    return round(input_cost + output_cost, 6)
