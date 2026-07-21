"""API web (FastAPI). Expone las capacidades de los módulos de forma genérica (estilo MCP).

No conoce proveedores ni modelos: descubre módulos del registro e invoca sus capacidades por
nombre. El cableado concreto vive en el composition root.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from jarvis.modules.core import (
    Capability,
    Module,
    ModuleRegistry,
    UnknownCapabilityError,
    UnknownModuleError,
)
from jarvis.platform.composition import build_registry
from jarvis.platform.config import get_settings
from jarvis.platform.db import create_engine
from jarvis.platform.logging import configure_logging


def create_app(registry: ModuleRegistry | None = None) -> FastAPI:
    """Construye la app; con un registro inyectado (tests) omite el arranque de recursos."""
    configure_logging()
    app = FastAPI(title="Jarvis", version="0.1.0", lifespan=None if registry else _lifespan)
    if registry is not None:
        app.state.registry = registry
    register_health(app)
    register_modules(app)
    return app


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Crea los recursos con red/DB al arrancar y los cierra al apagar."""
    settings = get_settings()
    engine = create_engine(settings.database_url) if settings.database_url else None
    async with httpx.AsyncClient(timeout=180.0) as client:
        app.state.registry = build_registry(settings, client, engine)
        yield
    if engine is not None:
        await engine.dispose()


def register_health(app: FastAPI) -> None:
    """Registra el endpoint de salud."""

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}


def register_modules(app: FastAPI) -> None:
    """Registra el descubrimiento de módulos y la invocación de capacidades."""

    @app.get("/modules")
    async def list_modules() -> list[dict[str, Any]]:
        registry: ModuleRegistry = app.state.registry
        return [_describe_module(module) for module in registry.all()]

    @app.post("/modules/{module_id}/capabilities/{name}")
    async def invoke(module_id: str, name: str, body: dict[str, Any]) -> dict[str, Any]:
        capability = _resolve(app.state.registry, module_id, name)
        return await _invoke(capability, body)


def _resolve(registry: ModuleRegistry, module_id: str, name: str) -> Capability:
    """Ubica la capacidad pedida o responde 404 si el módulo o la capacidad no existen."""
    try:
        return registry.get(module_id).capability(name)
    except (UnknownModuleError, UnknownCapabilityError) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


async def _invoke(capability: Capability, body: dict[str, Any]) -> dict[str, Any]:
    """Ejecuta la capacidad validando la entrada; 422 si los argumentos no calzan."""
    try:
        return await capability.invoke(body)
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=error.errors()) from error


def _describe_module(module: Module) -> dict[str, Any]:
    """Describe un módulo y sus capacidades con su esquema de entrada (MCP-ready)."""
    return {
        "id": module.id,
        "name": module.name,
        "description": module.description,
        "capabilities": [_describe_capability(cap) for cap in module.capabilities],
    }


def _describe_capability(capability: Capability) -> dict[str, Any]:
    """Describe una capacidad con su nombre, descripción y esquema JSON de entrada."""
    return {
        "name": capability.name,
        "description": capability.description,
        "input_schema": capability.input_schema(),
    }


app = create_app()
