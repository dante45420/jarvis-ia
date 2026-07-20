"""Contrato de módulos: la pieza reutilizable que todo módulo implementa.

Un módulo es una rebanada vertical (dominio + casos de uso + adaptadores) que expone
**capacidades** tipadas y descubribles. Córtex, el cerebro, consultará este registro para
saber qué puede hacer cada módulo y cómo invocarlo, sin conocer sus detalles internos.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

CapabilityHandler = Callable[[Any], Awaitable[BaseModel]]
JobHandler = Callable[[], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class Capability:
    """Operación tipada de un módulo; su esquema JSON la hace invocable por Córtex (MCP)."""

    name: str
    description: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    handler: CapabilityHandler

    async def invoke(self, raw_args: dict[str, Any]) -> dict[str, Any]:
        """Valida los argumentos, ejecuta el handler y devuelve la salida como JSON."""
        args = self.input_model.model_validate(raw_args)
        result = await self.handler(args)
        return result.model_dump(mode="json")

    def input_schema(self) -> dict[str, Any]:
        """Esquema JSON de la entrada; así Córtex sabe con qué argumentos llamar la capacidad."""
        return self.input_model.model_json_schema()


@dataclass(frozen=True, slots=True)
class ScheduledJob:
    """Un trabajo proactivo del módulo; el scheduler concreto interpreta la cadencia."""

    name: str
    cadence: str
    handler: JobHandler


@dataclass(frozen=True, slots=True)
class Module:
    """Una unidad de negocio descubrible: agrupa capacidades y trabajos programados."""

    id: str
    name: str
    description: str
    capabilities: tuple[Capability, ...] = ()
    jobs: tuple[ScheduledJob, ...] = ()

    def capability(self, name: str) -> Capability:
        """Devuelve la capacidad con ese nombre o falla si el módulo no la expone."""
        for capability in self.capabilities:
            if capability.name == name:
                return capability
        raise UnknownCapabilityError(self.id, name)


class ModuleRegistry:
    """Descubre módulos y sus capacidades; es lo que Córtex consulta para orquestar."""

    def __init__(self) -> None:
        self._modules: dict[str, Module] = {}

    def register(self, module: Module) -> None:
        """Registra un módulo; falla si su id ya está tomado."""
        if module.id in self._modules:
            raise DuplicateModuleError(module.id)
        self._modules[module.id] = module

    def get(self, module_id: str) -> Module:
        """Devuelve el módulo con ese id o falla si no existe."""
        try:
            return self._modules[module_id]
        except KeyError:
            raise UnknownModuleError(module_id) from None

    def all(self) -> list[Module]:
        """Devuelve todos los módulos registrados."""
        return list(self._modules.values())


class DuplicateModuleError(Exception):
    """Se intentó registrar dos módulos con el mismo id."""

    def __init__(self, module_id: str) -> None:
        super().__init__(f"El módulo '{module_id}' ya está registrado.")


class UnknownModuleError(Exception):
    """Se pidió un módulo que no está registrado."""

    def __init__(self, module_id: str) -> None:
        super().__init__(f"No existe un módulo con id '{module_id}'.")


class UnknownCapabilityError(Exception):
    """Se pidió una capacidad que el módulo no expone."""

    def __init__(self, module_id: str, name: str) -> None:
        super().__init__(f"El módulo '{module_id}' no expone la capacidad '{name}'.")
