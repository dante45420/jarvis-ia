"""Tests de la API genérica de módulos: descubrimiento e invocación de capacidades."""

from __future__ import annotations

from fastapi.testclient import TestClient

from jarvis.interfaces.api import create_app
from jarvis.modules.core import ModuleRegistry
from jarvis.modules.heraldo.dissection import DissectionService
from jarvis.modules.heraldo.gather import GatherService
from jarvis.modules.heraldo.module import build_heraldo_module
from tests.heraldo_fakes import FakeCompleter, FakeSource, make_deps, make_item


def _client() -> TestClient:
    gather = GatherService([FakeSource("A", [make_item("Ley de IA aprobada", "A")]),
                            FakeSource("B", [make_item("Ley de IA aprobada", "B")])])
    dissection = DissectionService(FakeCompleter({"dissect_questions": '{"questions": ["q1"]}'}))
    registry = ModuleRegistry()
    registry.register(build_heraldo_module(make_deps(gather=gather, dissection=dissection)))
    return TestClient(create_app(registry=registry))


def test_list_modules_exposes_heraldo_capabilities() -> None:
    response = _client().get("/modules")
    assert response.status_code == 200
    module = response.json()[0]
    assert module["id"] == "herald"
    names = [capability["name"] for capability in module["capabilities"]]
    assert "gather_stories" in names
    assert module["capabilities"][0]["input_schema"]["type"] == "object"


def test_invoke_gather_stories_returns_ranked_json() -> None:
    response = _client().post(
        "/modules/herald/capabilities/gather_stories",
        json={"subtopics": ["ia"], "reach_threshold": 2},
    )
    assert response.status_code == 200
    assert response.json()["stories"][0]["reach"] == 2


def test_invoke_unknown_capability_returns_404() -> None:
    response = _client().post("/modules/herald/capabilities/ghost", json={})
    assert response.status_code == 404


def test_invoke_unknown_module_returns_404() -> None:
    response = _client().post("/modules/nope/capabilities/x", json={})
    assert response.status_code == 404


def test_invoke_invalid_args_returns_422() -> None:
    response = _client().post("/modules/herald/capabilities/gather_stories", json={})
    assert response.status_code == 422
