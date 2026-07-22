"""Tests del compilador de onboarding: formulario → prompt ordenado. Puro, sin red ni IA."""

from __future__ import annotations

from jarvis.modules.heraldo.onboarding import (
    Objective,
    OnboardingForm,
    Style,
    TopicQuestion,
    compile_instruction,
    form_from_dict,
    form_to_dict,
)


def _form(**overrides: object) -> OnboardingForm:
    base = {
        "objective": Objective.LEARN_SKILL,
        "style": Style(),
        "questions": (TopicQuestion("¿Qué nivel tienes?", "Principiante"),),
    }
    base.update(overrides)
    return OnboardingForm(**base)  # type: ignore[arg-type]


def test_compiles_ordered_blocks_in_expected_order() -> None:
    text = compile_instruction(_form(), "IA para emprender")
    assert text.index("Tema:") < text.index("APRENDER")
    assert text.index("Estilo:") < text.index("Lo que busca el oyente")
    assert "ÁNGULO NUEVO" in text


def test_other_objective_uses_free_note() -> None:
    form = _form(objective=Objective.OTHER, objective_note="quiero reírme un rato")
    text = compile_instruction(form, "Humor")
    assert "quiero reírme un rato" in text


def test_style_switches_toggle_directives() -> None:
    off = Style(chilean_casual=False, backed_with_data=False, direct=False, with_examples=False)
    text = compile_instruction(_form(style=off), "Tema")
    assert "Estilo:" not in text

    on = Style(with_examples=True)
    text = compile_instruction(_form(style=on), "Tema")
    assert "ejemplos concretos" in text


def test_empty_answers_are_skipped() -> None:
    form = _form(questions=(TopicQuestion("¿Nivel?", "  "),))
    text = compile_instruction(form, "Tema")
    assert "Lo que busca el oyente" not in text


def test_covered_angles_are_listed_to_avoid_repetition() -> None:
    text = compile_instruction(_form(), "Tema", covered_angles=("El rol del criterio",))
    assert "NO los repitas" in text
    assert "El rol del criterio" in text


def test_form_survives_a_dict_roundtrip() -> None:
    form = _form(
        objective=Objective.MENTAL_HEALTH,
        style=Style(with_examples=True, direct=False),
        objective_note="tranquilidad",
    )
    restored = form_from_dict(form_to_dict(form))
    assert restored == form
