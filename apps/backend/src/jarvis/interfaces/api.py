"""API web (FastAPI). Punto de entrada del canal web; no conoce proveedores ni modelos."""

from __future__ import annotations

from fastapi import FastAPI

from jarvis.platform.logging import configure_logging


def create_app() -> FastAPI:
    """Construye la aplicación FastAPI y registra sus rutas."""
    configure_logging()
    app = FastAPI(title="Jarvis", version="0.1.0")
    register_health(app)
    return app


def register_health(app: FastAPI) -> None:
    """Registra el endpoint de salud."""

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}


app = create_app()
