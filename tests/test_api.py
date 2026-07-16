"""Test de humo de la API: la aplicación arranca y responde en /health."""

from fastapi.testclient import TestClient

from jarvis.interfaces.api import create_app


def test_health_returns_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
