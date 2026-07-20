# Roadmap — Jarvis

Fases y **estado actual**. Este es el primer archivo a leer al retomar una sesión.

## Estado actual

> **Fase 0 — Fundaciones.** Base documental + scaffolding hexagonal listos y verificados
> (ruff + mypy strict + pytest en verde). Existe: capas `domain/application/adapters/
> interfaces/platform`, puertos del dominio, entidad `UsageRecord` con cálculo de costo
> testeado, config por entorno, logging estructurado, API `/health`, docker-compose con pgvector.
>
> **En Fase 1 ya existe:** adaptador `OpenRouterProvider` (LLMProvider) con tests sin red;
> caso de uso `MeteredCompletion` que registra un `UsageRecord` por llamada; catálogo de
> precios `PricingCatalog`; `InMemoryUsageMeter`. Loop de costo cerrado a nivel de código.
>
> También existe: `OpenRouterEmbeddingProvider` (`bge-m3`, 1024 dims) con tokens medidos,
> y el tipo `EmbeddingResult`. Chat y embeddings comparten adaptador y key.
>
> **Repo reorganizado a monorepo** (D-0013): el backend vive en `apps/backend`; existen
> `apps/web`, `apps/mobile`, `packages/shared` (placeholders). Comandos de backend se corren
> desde `apps/backend`. Diseño de memoria (D-0008), módulos (D-0009), frontend/mobile (D-0010),
> batching (D-0011) y cerebro Córtex (D-0012) ya documentados.
>
> **Memoria (primer trozo) LISTA y verificada contra Postgres real** (docker, puerto configurable
> vía `JARVIS_DB_PORT`): dominio de memoria, extracción determinística de hechos, contexto con
> presupuesto, adaptador in-memory (unit) y pgvector (integración), Alembic con índice HNSW.
> Persistencia con SQLAlchemy 2.0 async, esquema con `owner_id`.
>
> **Módulos arrancados (Fase 5).** Contrato de módulos MCP-ready listo (`jarvis/modules/core.py`:
> `Capability`/`Module`/`ScheduledJob`/`ModuleRegistry`, D-0015). Primer módulo **Heraldo**
> (id `herald`, D-0016/D-0017): motor determinístico completo (normalizar URL → clustering con
> alcance → filtro por recencia/keywords/alcance → ranking) y capacidad `gather_stories`
> end-to-end. Todo sin IA, sin red. **39 tests verdes + 2 skip**, ruff + mypy strict en verde.
>
> **Próximo paso (Heraldo):** adaptadores de fuente reales tras `SourceAdapter` (RSS primero, luego
> Tavily/X/newsletters) + libro mayor de fuentes; disección interactiva del tema (LLM, 1 vez);
> persistencia de temas + máquina de pausa por tema; resumen por lote + plantillas de noticiero;
> guion + TTS por Gemini Batch. Pendiente de memoria: consolidación (episodic) y decaimiento.

## Fases

### Fase 0 — Fundaciones ✅
- [x] Documentación fundacional (visión, arquitectura, reglas, decisiones).
- [x] Scaffolding: layout hexagonal, `uv`, ruff/mypy/pytest, Docker, config por entorno.
- [x] Puertos del dominio definidos como interfaces (los que dependen de entidades futuras van en Fase 1).
- [x] Puerto `UsageMeter` + entidad `UsageRecord` con cálculo de costo testeado.

### Fase 1 — Núcleo conversacional + memoria ⏳ (en curso)
- [x] Adaptador `LLMProvider` sobre OpenRouter (detrás del puerto).
- [x] Caso de uso `MeteredCompletion` + `PricingCatalog` + `InMemoryUsageMeter` (costo por llamada).
- [x] `EmbeddingProvider` sobre OpenRouter (`bge-m3`, 1024 dims), con tokens medidos; `embed_batch`.
- [x] `MemoryStore` sobre pgvector (SQLAlchemy async + Alembic, índice HNSW). Test de integración real.
- [x] Memoria (working + semantic con RAG): guardar turnos, hechos determinísticos (regex),
      dedup por similitud, contexto con presupuesto de tokens. `MeteredEmbeddingProvider` mide el costo.
- [ ] Consolidación por LLM (episodic) + decaimiento/olvido (campos ya en el esquema).
- [ ] Pipeline costo-primero: reglas → caché → router → contexto acotado → LLM.
- [ ] `ModelRouter` con política de selección de modelo más barato capaz.
- [ ] `SemanticCache`.
- [ ] API web mínima + canal web.
- [ ] Tests de dominio y casos de uso.

### Fase 2 — Tareas y recordatorios
- [ ] Dominio de tareas; disparo proactivo (jobs async).
- [ ] Manejo determinístico de intenciones de tarea (sin LLM cuando se pueda).

### Fase 3 — Frontend web (dashboard + chat)
- [ ] UI limpia con revelación progresiva; nada bloquea la primera pintura (skeletons, streaming).
- [ ] Dashboard de costo (Bóveda) con desglose por niveles.
- [ ] Bandeja de Jarvis (human-in-the-loop).

### Fase 4 — App mobile (Expo/React Native)
- [ ] Hub central + tabbar por módulo; offline-first.
- [ ] Equivalentes mobile de Bóveda y Bandeja.

### Fase 5 — Módulo Heraldo (podcast + noticiero + búsqueda en vivo) ⏳ (en curso)
- [x] Contrato de módulos MCP-ready (`Capability`/`Module`/`ScheduledJob`/`ModuleRegistry`).
- [x] Motor agregador determinístico (normalizar → clustering/alcance → filtro → ranking).
- [x] Capacidad `gather_stories` end-to-end con tests, sin IA ni red.
- [ ] Adaptadores de fuente reales tras `SourceAdapter` (RSS → Tavily → X → newsletters).
- [ ] Libro mayor de fuentes: costo por fuente + aporte (ítems, únicos, al output final).
- [ ] Disección interactiva del tema (LLM, 1 vez) → `TopicProfile`.
- [ ] Persistencia de temas + máquina de pausa por tema (acción a la Bandeja).
- [ ] Resumen por lote (Gemini Batch) + plantillas de noticiero por tema.
- [ ] Guion del podcast (narrador/diálogo) + TTS por Gemini Batch; audio en almacenamiento.

### Fase 6+ — Cerebro Córtex y grafo temporal
- [ ] Orquestador conversacional sobre módulos; memoria de grafo (Graphiti) si se justifica.

### Futuro (no comprometido)
- Canal Telegram como adaptador, con políticas propias de contexto.
- Integraciones: correo, calendario.

## Cómo actualizar este archivo
Al cerrar un avance: mueve los checks, y reescribe el bloque **Estado actual** con el
próximo paso concreto. Ese bloque es lo que permite retomar sin releer el repo.
