"""Disección interactiva del tema: el primer uso de IA de Heraldo, en dos llamadas acotadas.

Flujo: (1) el modelo genera preguntas dirigidas para acotar el tema; (2) con tus respuestas,
compila un TopicProfile estructurado. Salida siempre en JSON, nunca prosa. El costo se mide en la
capa del Completer, que enruta por la telemetría.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from jarvis.domain.llm import Message
from jarvis.modules.heraldo.domain import TopicProfile
from jarvis.modules.heraldo.jsonio import extract_json_object


@dataclass(frozen=True, slots=True)
class QuestionAnswer:
    """Una pregunta de disección y la respuesta del usuario."""

    question: str
    answer: str


@runtime_checkable
class Completer(Protocol):
    """Pide texto a un LLM para una tarea; la implementación real mide el costo."""

    async def complete(self, task: str, messages: list[Message], now: datetime) -> str:
        """Devuelve la respuesta del modelo como texto."""
        ...


class DissectionService:
    """Convierte un tema vago en un perfil de búsqueda concreto, preguntando lo justo."""

    def __init__(self, completer: Completer) -> None:
        self._completer = completer

    async def propose_questions(self, topic_name: str, now: datetime) -> list[str]:
        """Genera preguntas dirigidas para acotar el tema."""
        prompt = _questions_prompt(topic_name)
        text = await self._completer.complete("dissect_questions", prompt, now)
        return _QuestionsDraft.model_validate_json(extract_json_object(text)).questions

    async def compile_profile(
        self, topic_name: str, answers: list[QuestionAnswer], now: datetime
    ) -> TopicProfile:
        """Compila el perfil del tema a partir de las respuestas."""
        text = await self._completer.complete(
            "dissect_profile", _profile_prompt(topic_name, answers), now
        )
        return _to_profile(_ProfileDraft.model_validate_json(extract_json_object(text)))


class _QuestionsDraft(BaseModel):
    """Forma esperada de la respuesta del modelo al proponer preguntas."""

    questions: list[str] = Field(default_factory=list)


class _ProfileDraft(BaseModel):
    """Forma esperada de la respuesta del modelo al compilar el perfil."""

    subtopics: list[str] = Field(default_factory=list)
    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    reach_threshold: int = 1
    recency_hours: int = 48


def _to_profile(draft: _ProfileDraft) -> TopicProfile:
    """Traduce el borrador del modelo a un TopicProfile de dominio."""
    return TopicProfile(
        subtopics=tuple(draft.subtopics),
        include_keywords=tuple(draft.include_keywords),
        exclude_keywords=tuple(draft.exclude_keywords),
        reach_threshold=draft.reach_threshold,
        recency_hours=draft.recency_hours,
    )


def _questions_prompt(topic_name: str) -> list[Message]:
    """Arma el prompt que pide preguntas dirigidas para acotar el tema."""
    system = (
        "Diseñas perfiles de temas para un noticiero y podcast personal. Genera entre 3 y 5 "
        "preguntas breves, en español chileno (tuteo), que necesitas para acotar el tema y que "
        'no quede vago. Responde SOLO con JSON: {"questions": ["...", "..."]}.'
    )
    return [Message("system", system), Message("user", f"Tema: {topic_name}")]


def _profile_prompt(topic_name: str, answers: list[QuestionAnswer]) -> list[Message]:
    """Arma el prompt que compila el perfil a partir de las respuestas."""
    system = (
        "Con el tema y las respuestas, arma un perfil de búsqueda específico para maximizar el "
        "valor del contenido. Responde SOLO con JSON con las claves: subtopics (lista de strings), "
        "include_keywords (lista), exclude_keywords (lista), reach_threshold (entero: cuántas "
        "fuentes deben cubrir una noticia para incluirla), recency_hours (entero)."
    )
    return [Message("system", system), Message("user", _answers_block(topic_name, answers))]


def _answers_block(topic_name: str, answers: list[QuestionAnswer]) -> str:
    """Renderiza el tema y el par pregunta/respuesta como texto para el modelo."""
    lines = [f"Tema: {topic_name}", "Respuestas:"]
    lines += [f"- {item.question} -> {item.answer}" for item in answers]
    return "\n".join(lines)
