"""Extracción determinística de hechos desde un mensaje. Cero IA: el camino más barato (D-0008)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from jarvis.domain.memory import Fact

SUBJECT = "usuario"


@dataclass(frozen=True, slots=True)
class _Rule:
    """Una regla de extracción: patrón y predicado (o None para derivarlo del grupo 'rel')."""

    regex: re.Pattern[str]
    predicate: str | None


_RULES: list[_Rule] = [
    _Rule(re.compile(r"\bme llamo\s+(?P<obj>[^\s,.;]+)", re.IGNORECASE), "se_llama"),
    _Rule(re.compile(r"\bmi\s+(?P<rel>\w+)\s+es\s+(?P<obj>.+)", re.IGNORECASE), None),
    _Rule(re.compile(r"\bprefiero\s+(?P<obj>.+)", re.IGNORECASE), "prefiere"),
    _Rule(re.compile(r"\brecuerda que\s+(?P<obj>.+)", re.IGNORECASE), "nota"),
]


def extract_facts(owner_id: str, text: str, now: datetime) -> list[Fact]:
    """Aplica las reglas al texto y devuelve los hechos encontrados (sin IA)."""
    facts = [_from_rule(rule, text, owner_id, now) for rule in _RULES]
    return [fact for fact in facts if fact is not None]


def _from_rule(rule: _Rule, text: str, owner_id: str, now: datetime) -> Fact | None:
    """Intenta un match de la regla y construye el hecho; None si no aplica."""
    match = rule.regex.search(text)
    if match is None:
        return None
    return _build_fact(rule, match, owner_id, now)


def _build_fact(rule: _Rule, match: re.Match[str], owner_id: str, now: datetime) -> Fact:
    """Arma el hecho a partir del match, derivando el predicado si la regla no lo fija."""
    predicate = rule.predicate or match.group("rel").lower()
    obj = match.group("obj").strip().rstrip(".")
    return Fact(owner_id=owner_id, subject=SUBJECT, predicate=predicate, object=obj, created_at=now)
