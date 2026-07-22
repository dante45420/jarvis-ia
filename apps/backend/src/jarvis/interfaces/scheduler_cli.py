"""CLI del tick del scheduler: lo corre el cron de Render por hora. Avisa por push, cero IA.

Arma el registro con los adaptadores reales (misma raíz de composición que la API) e invoca la
capacidad `run_scheduler_tick` de Heraldo para el dueño configurado. No gasta IA: solo revisa la
cadencia y manda las notificaciones que tocan.
"""

from __future__ import annotations

import asyncio

import httpx

from jarvis.platform.composition import build_registry
from jarvis.platform.config import get_settings
from jarvis.platform.db import create_engine
from jarvis.platform.logging import configure_logging


async def _run() -> None:
    """Arma los recursos, corre el tick y los cierra."""
    configure_logging()
    settings = get_settings()
    engine = create_engine(settings.database_url) if settings.database_url else None
    async with httpx.AsyncClient(timeout=60.0) as client:
        capability = build_registry(settings, client, engine).get("herald").capability(
            "run_scheduler_tick"
        )
        await capability.invoke({"owner_id": settings.scheduler_owner_id})
    if engine is not None:
        await engine.dispose()


def main() -> None:
    """Punto de entrada del cron."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
