"""Onboarding de un tema: formulario (partes fijas + preguntas de IA) y su compilación.

El formulario tiene partes **fijas** (objetivo, estilo, cadencia) que no gastan IA, y un
slot de **preguntas específicas del tema** que sí genera la IA. Todo se compila de forma
determinística en un prompt ordenado que guía la generación del podcast/noticiero.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class Objective(StrEnum):
    """Para qué quiere el oyente este tema; orienta el tono y el fin del contenido."""

    LEARN_SKILL = "learn_skill"
    MENTAL_HEALTH = "mental_health"
    STAY_INFORMED = "stay_informed"
    OTHER = "other"


_OBJECTIVE_DIRECTIVE: dict[Objective, str] = {
    Objective.LEARN_SKILL: (
        "El oyente quiere APRENDER una habilidad: entrega técnicas concretas y pasos "
        "accionables que pueda practicar, no generalidades."
    ),
    Objective.MENTAL_HEALTH: (
        "El fin es el bienestar del oyente: tono cálido y cuidadoso, sin diagnósticos ni "
        "promesas; prioriza calma, perspectiva y hábitos sostenibles."
    ),
    Objective.STAY_INFORMED: (
        "El oyente quiere MANTENERSE INFORMADO: prioriza lo nuevo, relevante y verificable; "
        "cero relleno."
    ),
    Objective.OTHER: "",
}


_CASUAL = "Habla en chileno cercano pero no exagerado (tuteo, sin modismos forzados)."
_BACKED = "Respalda cada afirmación con datos, fuentes o ejemplos verificables."
_DIRECT = "Ve al grano: sin introducciones largas ni relleno."
_EXAMPLES = "Ilustra las ideas con ejemplos concretos y casos reales."


@dataclass(frozen=True, slots=True)
class Style:
    """Switches de tono/estilo del formulario; cada uno activa una directiva concreta."""

    chilean_casual: bool = True
    backed_with_data: bool = True
    direct: bool = True
    with_examples: bool = False

    def directives(self) -> tuple[str, ...]:
        """Traduce los switches activos en instrucciones de estilo para el guion."""
        rules = (
            (self.chilean_casual, _CASUAL),
            (self.backed_with_data, _BACKED),
            (self.direct, _DIRECT),
            (self.with_examples, _EXAMPLES),
        )
        return tuple(rule for active, rule in rules if active)


@dataclass(frozen=True, slots=True)
class TopicQuestion:
    """Una pregunta específica del tema (generada por IA) con la respuesta del oyente."""

    question: str
    answer: str


@dataclass(frozen=True, slots=True)
class OnboardingForm:
    """El formulario completo de un tema: objetivo, estilo y las respuestas del oyente."""

    objective: Objective
    style: Style
    questions: tuple[TopicQuestion, ...] = ()
    objective_note: str = ""


def form_to_dict(form: OnboardingForm) -> dict[str, Any]:
    """Serializa el formulario a un dict simple, listo para persistir como JSON."""
    return {
        "objective": form.objective.value,
        "objective_note": form.objective_note,
        "style": {
            "chilean_casual": form.style.chilean_casual,
            "backed_with_data": form.style.backed_with_data,
            "direct": form.style.direct,
            "with_examples": form.style.with_examples,
        },
        "questions": [{"question": q.question, "answer": q.answer} for q in form.questions],
    }


def form_from_dict(data: dict[str, Any]) -> OnboardingForm:
    """Reconstruye el formulario desde su forma persistida."""
    style = data.get("style", {})
    questions = tuple(TopicQuestion(q["question"], q["answer"]) for q in data.get("questions", []))
    return OnboardingForm(
        objective=Objective(data["objective"]),
        style=Style(**style) if style else Style(),
        questions=questions,
        objective_note=data.get("objective_note", ""),
    )


def objective_line(form: OnboardingForm) -> str:
    """Arma la línea de objetivo, usando la nota libre cuando el objetivo es 'otro'."""
    base = _OBJECTIVE_DIRECTIVE[form.objective]
    if form.objective is Objective.OTHER:
        return f"Objetivo del oyente: {form.objective_note.strip() or 'no especificado'}."
    return base


def compile_instruction(
    form: OnboardingForm, topic_name: str, covered_angles: tuple[str, ...] = ()
) -> str:
    """Compila el formulario en un prompt ordenado que guía la generación del contenido."""
    blocks = [
        f"Tema: {topic_name}.",
        objective_line(form),
        _style_block(form.style),
        _answers_block(form.questions),
        _fresh_angle_block(covered_angles),
    ]
    return "\n".join(block for block in blocks if block)


def _style_block(style: Style) -> str:
    """Renderiza las directivas de estilo activas como un bloque numerado breve."""
    directives = style.directives()
    if not directives:
        return ""
    lines = "\n".join(f"- {rule}" for rule in directives)
    return f"Estilo:\n{lines}"


def _answers_block(questions: tuple[TopicQuestion, ...]) -> str:
    """Renderiza el contexto que dio el oyente al responder las preguntas del tema."""
    answered = [item for item in questions if item.answer.strip()]
    if not answered:
        return ""
    lines = "\n".join(f"- {item.question} → {item.answer.strip()}" for item in answered)
    return f"Lo que busca el oyente (sus respuestas):\n{lines}"


def _fresh_angle_block(covered_angles: tuple[str, ...]) -> str:
    """Instruye tratar un ángulo nuevo, listando lo ya cubierto para no repetirlo."""
    base = (
        "Enseña un ÁNGULO NUEVO del tema, como un experto que cada vez muestra una faceta "
        "distinta con otra técnica o conocimiento. No repitas ideas ya tratadas."
    )
    if not covered_angles:
        return base
    covered = "\n".join(f"- {angle}" for angle in covered_angles)
    return f"{base}\nÁngulos ya tratados (NO los repitas):\n{covered}"
