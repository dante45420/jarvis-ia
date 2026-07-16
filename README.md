# Jarvis

Asistente virtual personal, orientado a costo mínimo y escalabilidad extrema.

La documentación viva está en `docs/` y en `CLAUDE.md`. Empieza por ahí:

- `docs/ROADMAP.md` — estado actual y próximo paso.
- `docs/VISION.md` — norte y principios.
- `docs/ARCHITECTURE.md` — stack y diseño.
- `docs/DECISIONS.md` — decisiones y su justificación.

## Desarrollo

Requiere [uv](https://docs.astral.sh/uv/) y Docker.

    uv sync                                              # instala dependencias
    docker compose up -d db                              # Postgres + pgvector local
    uv run pytest                                        # corre los tests
    uv run uvicorn jarvis.interfaces.api:app --reload    # levanta la API
