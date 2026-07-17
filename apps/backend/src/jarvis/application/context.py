"""Ensamblado del contexto con presupuesto fijo de tokens. Recorte determinístico, sin IA."""

from __future__ import annotations

from dataclasses import dataclass

from jarvis.domain.llm import Message
from jarvis.domain.memory import ConversationTurn, RetrievedFact


@dataclass(frozen=True, slots=True)
class ContextBudget:
    """Topes de tokens por sección del contexto (ver D-0008)."""

    facts_tokens: int = 300
    working_tokens: int = 1500


def estimate_tokens(text: str) -> int:
    """Estima tokens de forma barata (~4 chars/token). Sirve para presupuestar, no para facturar."""
    return max(1, (len(text) + 3) // 4)


def assemble_context(
    facts: list[RetrievedFact], turns: list[ConversationTurn], budget: ContextBudget
) -> list[Message]:
    """Arma el contexto por prioridad: ficha de hechos y luego los turnos recientes que quepan."""
    messages: list[Message] = []
    ficha = _facts_message(facts, budget.facts_tokens)
    if ficha is not None:
        messages.append(ficha)
    messages.extend(_fit_turns(turns, budget.working_tokens))
    return messages


def _facts_message(facts: list[RetrievedFact], cap: int) -> Message | None:
    """Construye un mensaje de sistema con los hechos que caben en el tope de tokens."""
    lines: list[str] = []
    used = 0
    for retrieved in facts:
        line = f"- {retrieved.fact.as_text()}"
        used += estimate_tokens(line)
        if used > cap:
            break
        lines.append(line)
    if not lines:
        return None
    return Message(role="system", content="Sobre el usuario:\n" + "\n".join(lines))


def _fit_turns(turns: list[ConversationTurn], cap: int) -> list[Message]:
    """Toma los turnos más recientes que caben en el tope y los devuelve en orden cronológico."""
    kept: list[ConversationTurn] = []
    used = 0
    for turn in turns:
        used += estimate_tokens(turn.content)
        if used > cap:
            break
        kept.append(turn)
    kept.reverse()
    return [Message(role=turn.role, content=turn.content) for turn in kept]
