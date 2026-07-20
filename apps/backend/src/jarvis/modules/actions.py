"""Acciones de módulo hacia el usuario: la semilla mínima de la Bandeja de Jarvis.

Cuando un módulo necesita que decidas algo (p. ej. Heraldo pausó un tema), emite una
ModuleAction. El detalle de la Bandeja (orden, filtros) se define más adelante; por ahora solo
fijamos el contrato para no acoplar los módulos a su implementación.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ModuleAction:
    """Algo que un módulo deja para que el usuario lo revise o decida."""

    owner_id: str
    module_id: str
    kind: str
    subject: str
    body: str
    created_at: datetime


@runtime_checkable
class ActionInbox(Protocol):
    """Recibe las acciones que los módulos dejan al usuario."""

    async def emit(self, action: ModuleAction) -> None:
        """Registra una acción para que el usuario la vea y decida."""
        ...
