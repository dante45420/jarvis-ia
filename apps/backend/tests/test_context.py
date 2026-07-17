"""Tests del ensamblado de contexto con presupuesto de tokens."""

from datetime import datetime

from jarvis.application.context import ContextBudget, assemble_context, estimate_tokens
from jarvis.domain.memory import ConversationTurn, Fact, RetrievedFact

NOW = datetime(2026, 7, 17)


def _turn(role: str, content: str) -> ConversationTurn:
    return ConversationTurn(owner_id="dante", role=role, content=content, occurred_at=NOW)


def _retrieved(predicate: str, obj: str) -> RetrievedFact:
    fact = Fact("dante", "usuario", predicate, obj, NOW)
    return RetrievedFact(fact=fact, similarity=0.9)


def test_estimate_tokens_is_positive() -> None:
    assert estimate_tokens("") == 1
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 8) == 2


def test_facts_go_into_a_system_message() -> None:
    messages = assemble_context([_retrieved("se_llama", "Dante")], [], ContextBudget())
    assert messages[0].role == "system"
    assert "se_llama Dante" in messages[0].content


def test_turns_are_returned_in_chronological_order() -> None:
    newest_first = [_turn("assistant", "respuesta"), _turn("user", "pregunta")]
    messages = assemble_context([], newest_first, ContextBudget())
    assert [m.role for m in messages] == ["user", "assistant"]


def test_working_budget_drops_oldest_turns() -> None:
    turns = [_turn("user", "x" * 40), _turn("user", "y" * 40)]
    messages = assemble_context([], turns, ContextBudget(working_tokens=10))
    assert len(messages) == 1
