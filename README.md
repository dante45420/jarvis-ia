# Jarvis

Asistente virtual personal, orientado a costo mínimo y escalabilidad extrema.

La documentación viva está en `docs/` y en `CLAUDE.md`. Empieza por ahí:

- `docs/ROADMAP.md` — estado actual y próximo paso.
- `docs/VISION.md` — norte y principios.
- `docs/ARCHITECTURE.md` — stack y diseño.
- `docs/DECISIONS.md` — decisiones y su justificación.

## Estructura (monorepo)

    apps/backend    Python + FastAPI (el cerebro que orquesta todo)
    apps/web        Frontend web (React + Vite)            — Fase 3
    apps/mobile     App mobile personal (Expo/React Native) — Fase 4
    packages/shared Tipos TS compartidos entre web y mobile
    docs/           Documentación viva

## Desarrollo del backend

Requiere [uv](https://docs.astral.sh/uv/) y Docker.

    docker compose up -d db                 # Postgres + pgvector local (desde la raíz)
    cd apps/backend
    uv sync                                 # instala dependencias
    uv run pytest                           # corre los tests
    uv run uvicorn jarvis.interfaces.api:app --reload   # levanta la API
