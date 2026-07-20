"""Ensamblado del módulo Heraldo: expone sus capacidades MCP-ready para Córtex."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from jarvis.modules.core import Capability, CapabilityHandler, Module
from jarvis.modules.heraldo.gather import GatherService
from jarvis.modules.heraldo.schemas import GatherInput, GatherOutput, to_profile, to_story

Clock = Callable[[], datetime]


def build_heraldo_module(gather: GatherService, clock: Clock) -> Module:
    """Arma el módulo Heraldo con sus capacidades, listo para registrarse."""
    capability = Capability(
        name="gather_stories",
        description="Reúne y ordena historias de un tema desde todas las fuentes, sin IA.",
        input_model=GatherInput,
        output_model=GatherOutput,
        handler=_gather_handler(gather, clock),
    )
    return Module(
        id="herald",
        name="Heraldo",
        description="Tu vocero: podcast, noticiero y búsqueda en vivo sobre los temas que sigues.",
        capabilities=(capability,),
    )


def _gather_handler(gather: GatherService, clock: Clock) -> CapabilityHandler:
    """Crea el handler de gather_stories inyectándole el motor y el reloj."""

    async def handle(args: GatherInput) -> GatherOutput:
        clusters = await gather.gather(to_profile(args), clock())
        return GatherOutput(stories=[to_story(cluster) for cluster in clusters])

    return handle
