# Roadmap — Jarvis

Fases y **estado actual**. Este es el primer archivo a leer al retomar una sesión.

## Estado actual

> **Fase 0 — Fundaciones.** Base documental + scaffolding hexagonal listos y verificados
> (ruff + mypy strict + pytest en verde). Existe: capas `domain/application/adapters/
> interfaces/platform`, puertos del dominio, entidad `UsageRecord` con cálculo de costo
> testeado, config por entorno, logging estructurado, API `/health`, docker-compose con pgvector.
>
> **Próximo paso concreto (Fase 1):** adaptador `LLMProvider` sobre OpenRouter detrás del
> puerto, con emisión de `UsageRecord` por llamada. Luego embeddings + memoria + pipeline.

## Fases

### Fase 0 — Fundaciones ✅
- [x] Documentación fundacional (visión, arquitectura, reglas, decisiones).
- [x] Scaffolding: layout hexagonal, `uv`, ruff/mypy/pytest, Docker, config por entorno.
- [x] Puertos del dominio definidos como interfaces (los que dependen de entidades futuras van en Fase 1).
- [x] Puerto `UsageMeter` + entidad `UsageRecord` con cálculo de costo testeado.

### Fase 1 — Núcleo conversacional + memoria
- [ ] Adaptador `LLMProvider` sobre OpenRouter (detrás del puerto).
- [ ] `EmbeddingProvider` + `VectorStore` (pgvector).
- [ ] Sistema de memoria (working, episodic, semantic) con RAG.
- [ ] Pipeline costo-primero: reglas → caché → router → contexto acotado → LLM.
- [ ] `ModelRouter` con política de selección de modelo más barato capaz.
- [ ] `SemanticCache`.
- [ ] API web mínima + canal web.
- [ ] Tests de dominio y casos de uso.

### Fase 2 — Tareas y recordatorios
- [ ] Dominio de tareas; disparo proactivo (jobs async).
- [ ] Manejo determinístico de intenciones de tarea (sin LLM cuando se pueda).

### Fase 3 — Frontend (dashboard + chat)
- [ ] UI limpia con revelación progresiva.
- [ ] Vista de costo/uso (transparencia del ahorro).

### Fase 4 — Podcast automatizado
- [ ] Por especificar con el usuario.

### Futuro (no comprometido)
- Canal Telegram como adaptador, con políticas propias de contexto.
- Integraciones: correo, calendario.

## Cómo actualizar este archivo
Al cerrar un avance: mueve los checks, y reescribe el bloque **Estado actual** con el
próximo paso concreto. Ese bloque es lo que permite retomar sin releer el repo.
