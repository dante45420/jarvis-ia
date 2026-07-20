"""Tests del protocolo de batching: trocea por cantidad, tokens de entrada y de salida."""

from __future__ import annotations

from jarvis.application.batching import BatchLimits, ItemCost, plan_batches


def _cost(item: tuple[int, int]) -> ItemCost:
    return ItemCost(input_tokens=item[0], output_tokens=item[1])


def test_single_batch_when_within_limits() -> None:
    limits = BatchLimits(max_items=10, max_input_tokens=1000, max_output_tokens=1000)
    batches = plan_batches([(100, 100), (100, 100)], _cost, limits)
    assert batches == [[(100, 100), (100, 100)]]


def test_splits_by_item_count() -> None:
    limits = BatchLimits(max_items=2, max_input_tokens=9999, max_output_tokens=9999)
    batches = plan_batches([(1, 1), (1, 1), (1, 1)], _cost, limits)
    assert [len(batch) for batch in batches] == [2, 1]


def test_splits_by_input_tokens() -> None:
    limits = BatchLimits(max_items=99, max_input_tokens=250, max_output_tokens=9999)
    batches = plan_batches([(100, 10), (100, 10), (100, 10)], _cost, limits)
    assert [len(batch) for batch in batches] == [2, 1]


def test_splits_by_output_tokens_the_tightest_cap() -> None:
    limits = BatchLimits(max_items=99, max_input_tokens=9999, max_output_tokens=250)
    batches = plan_batches([(10, 100), (10, 100), (10, 100)], _cost, limits)
    assert [len(batch) for batch in batches] == [2, 1]


def test_oversized_item_gets_its_own_batch() -> None:
    limits = BatchLimits(max_items=99, max_input_tokens=50, max_output_tokens=9999)
    batches = plan_batches([(500, 10), (10, 10)], _cost, limits)
    assert [len(batch) for batch in batches] == [1, 1]


def test_empty_input_yields_no_batches() -> None:
    limits = BatchLimits(max_items=5, max_input_tokens=100, max_output_tokens=100)
    assert plan_batches([], _cost, limits) == []
