"""Protocolo de batching inteligente: agrupa ítems por llamada sin marear al modelo.

Batching obligatorio (D-0011), pero no ingenuo: meter demasiados ítems degrada la calidad y puede
reventar el contexto. Se trocea respetando tres topes por proveedor/modelo — máximo de ítems
(calidad), de tokens de entrada (contexto) y de tokens de salida (el más apretado, cada ítem
genera respuesta) —; lo que sobra va en otro lote.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ItemCost:
    """Costo estimado de un ítem: lo que aporta al prompt y lo que hará generar."""

    input_tokens: int
    output_tokens: int


@dataclass(frozen=True, slots=True)
class BatchLimits:
    """Topes de un lote para un proveedor/modelo: cantidad, tokens de entrada y de salida."""

    max_items: int
    max_input_tokens: int
    max_output_tokens: int


def plan_batches[T](
    items: list[T], cost: Callable[[T], ItemCost], limits: BatchLimits
) -> list[list[T]]:
    """Trocea los ítems en lotes que respetan los topes de cantidad, entrada y salida."""
    batches: list[list[T]] = []
    current: list[T] = []
    used = ItemCost(0, 0)
    for item in items:
        item_cost = cost(item)
        if current and _would_overflow(len(current), used, item_cost, limits):
            batches.append(current)
            current, used = [], ItemCost(0, 0)
        current.append(item)
        used = _add(used, item_cost)
    if current:
        batches.append(current)
    return batches


def _add(used: ItemCost, item: ItemCost) -> ItemCost:
    """Acumula el costo de un ítem al del lote en curso."""
    return ItemCost(used.input_tokens + item.input_tokens, used.output_tokens + item.output_tokens)


def _would_overflow(count: int, used: ItemCost, item: ItemCost, limits: BatchLimits) -> bool:
    """Indica si sumar un ítem más pasaría alguno de los tres topes del lote."""
    return (
        count >= limits.max_items
        or used.input_tokens + item.input_tokens > limits.max_input_tokens
        or used.output_tokens + item.output_tokens > limits.max_output_tokens
    )
