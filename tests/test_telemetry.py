"""Tests del cálculo de costo: la lógica determinística que sostiene el dashboard."""

from jarvis.domain.telemetry import ModelPrice, compute_cost


def test_compute_cost_sums_input_and_output() -> None:
    price = ModelPrice(input_per_million=0.15, output_per_million=0.60)
    cost = compute_cost(price, tokens_in=1_000_000, tokens_out=1_000_000)
    assert cost == 0.75


def test_compute_cost_is_zero_without_tokens() -> None:
    price = ModelPrice(input_per_million=0.15, output_per_million=0.60)
    assert compute_cost(price, tokens_in=0, tokens_out=0) == 0.0


def test_compute_cost_scales_with_partial_tokens() -> None:
    price = ModelPrice(input_per_million=1.0, output_per_million=2.0)
    cost = compute_cost(price, tokens_in=500_000, tokens_out=250_000)
    assert cost == 1.0
