"""Tests del contrato de módulos: capacidades invocables y registro."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from jarvis.modules.core import (
    Capability,
    DuplicateModuleError,
    Module,
    ModuleRegistry,
    UnknownCapabilityError,
    UnknownModuleError,
)


class _Doubling(BaseModel):
    value: int


class _Doubled(BaseModel):
    result: int


async def _double(args: _Doubling) -> _Doubled:
    return _Doubled(result=args.value * 2)


def _demo_module() -> Module:
    capability = Capability(
        name="double",
        description="Duplica un número.",
        input_model=_Doubling,
        output_model=_Doubled,
        handler=_double,
    )
    return Module(
        id="demo", name="Demo", description="Módulo de prueba.", capabilities=(capability,)
    )


async def test_capability_validates_input_and_runs_handler() -> None:
    capability = _demo_module().capability("double")
    assert await capability.invoke({"value": 3}) == {"result": 6}


def test_capability_exposes_mcp_ready_input_schema() -> None:
    schema = _demo_module().capability("double").input_schema()
    assert schema["properties"]["value"]["type"] == "integer"


def test_registry_registers_and_recovers_modules() -> None:
    registry = ModuleRegistry()
    module = _demo_module()
    registry.register(module)
    assert registry.get("demo") is module
    assert registry.all() == [module]


def test_registry_rejects_duplicate_ids() -> None:
    registry = ModuleRegistry()
    registry.register(_demo_module())
    with pytest.raises(DuplicateModuleError):
        registry.register(_demo_module())


def test_registry_raises_on_unknown_module() -> None:
    with pytest.raises(UnknownModuleError):
        ModuleRegistry().get("missing")


def test_module_raises_on_unknown_capability() -> None:
    with pytest.raises(UnknownCapabilityError):
        _demo_module().capability("missing")
