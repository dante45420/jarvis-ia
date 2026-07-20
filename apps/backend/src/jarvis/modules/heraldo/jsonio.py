"""Utilidad para rescatar el objeto JSON de una respuesta del modelo, tolerando envoltorios."""

from __future__ import annotations


def extract_json_object(text: str) -> str:
    """Recorta el objeto JSON del texto, ignorando prosa o cercas de código alrededor."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return text
    return text[start : end + 1]
