"""Tests de la cadencia: cuándo toca generar según frecuencia, hora y última entrega. Puro."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.modules.heraldo.cadence import Cadence, Frequency, is_due


def _at(day: int, hour: int) -> datetime:
    return datetime(2026, 7, day, hour, tzinfo=UTC)


def test_period_days_maps_from_frequency() -> None:
    assert Cadence(Frequency.DAILY).period_days == 1
    assert Cadence(Frequency.WEEKLY).period_days == 7
    assert Cadence(Frequency.EVERY_N_DAYS, every_days=3).period_days == 3


def test_not_due_outside_the_chosen_hour() -> None:
    assert not is_due(Cadence(hour=8), None, _at(20, 7))


def test_due_at_the_chosen_hour_when_never_delivered() -> None:
    assert is_due(Cadence(hour=8), None, _at(20, 8))


def test_not_due_before_period_elapses() -> None:
    cadence = Cadence(Frequency.EVERY_N_DAYS, every_days=3, hour=8)
    assert not is_due(cadence, _at(19, 8), _at(20, 8))


def test_due_once_period_elapses() -> None:
    cadence = Cadence(Frequency.EVERY_N_DAYS, every_days=3, hour=8)
    assert is_due(cadence, _at(17, 8), _at(20, 8))
