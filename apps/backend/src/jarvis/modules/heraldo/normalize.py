"""Normalización determinística de URLs y títulos, base para detectar duplicados sin IA."""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

_TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "mc_")


def canonical_url(url: str) -> str:
    """Normaliza una URL para comparar: baja el host, quita tracking y la barra final."""
    parts = urlsplit(url.strip())
    host = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    query = _strip_tracking(parts.query)
    return urlunsplit((parts.scheme.lower(), host, path, query, ""))


def _strip_tracking(query: str) -> str:
    """Descarta parámetros de tracking y ordena el resto para que sea estable."""
    if not query:
        return ""
    kept = [param for param in query.split("&") if not _is_tracking(param)]
    return "&".join(sorted(kept))


def _is_tracking(param: str) -> bool:
    """Indica si un parámetro es de tracking según su nombre."""
    key = param.split("=", 1)[0].lower()
    return key.startswith(_TRACKING_PREFIXES)


def title_tokens(title: str) -> frozenset[str]:
    """Devuelve el conjunto de palabras del título normalizado, para medir similitud."""
    return frozenset(_normalize_title(title).split())


def _normalize_title(title: str) -> str:
    """Baja a minúsculas, deja solo alfanumérico y espacios, y colapsa espacios."""
    lowered = title.lower()
    cleaned = "".join(char if char.isalnum() or char.isspace() else " " for char in lowered)
    return " ".join(cleaned.split())
