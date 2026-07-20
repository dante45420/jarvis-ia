"""Adaptador reutilizable: ejecuta una completación medida y devuelve solo el texto.

Es el puente entre los módulos (que solo quieren "pídele texto a un LLM") y la telemetría de
costo. Cada llamada queda registrada vía MeteredCompletion, cumpliendo la regla de que ninguna
llamada de IA escapa a la medición.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from jarvis.application.metered_completion import CompletionContext, MeteredCompletion
from jarvis.domain.llm import Message


class MeteredCompleter:
    """Envuelve MeteredCompletion fijando modelo y canal; expone un complete simple que da texto."""

    def __init__(
        self,
        completion: MeteredCompletion,
        model: str,
        channel: str,
        new_id: Callable[[], str],
    ) -> None:
        self._completion = completion
        self._model = model
        self._channel = channel
        self._new_id = new_id

    async def complete(self, task: str, messages: list[Message], now: datetime) -> str:
        """Ejecuta la completación medida para una tarea y devuelve el texto del modelo."""
        context = CompletionContext(
            model=self._model, task=task, channel=self._channel, request_id=self._new_id()
        )
        result = await self._completion.run(context, messages, now)
        return result.text
