"""Tests de la extracción determinística de hechos (sin IA)."""

from datetime import datetime

from jarvis.application.fact_extraction import extract_facts

NOW = datetime(2026, 7, 17)


def test_extracts_name() -> None:
    facts = extract_facts("dante", "Hola, me llamo Dante", NOW)
    assert any(f.predicate == "se_llama" and f.object == "Dante" for f in facts)


def test_derives_predicate_from_relation() -> None:
    facts = extract_facts("dante", "mi jefe es Ana", NOW)
    fact = next(f for f in facts if f.predicate == "jefe")
    assert fact.object == "Ana"
    assert fact.subject == "usuario"


def test_extracts_preference_without_trailing_period() -> None:
    facts = extract_facts("dante", "prefiero el café sin azúcar.", NOW)
    fact = next(f for f in facts if f.predicate == "prefiere")
    assert fact.object == "el café sin azúcar"


def test_no_facts_when_nothing_matches() -> None:
    assert extract_facts("dante", "¿qué hora es?", NOW) == []
