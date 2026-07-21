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
> **Adaptador RSS/Atom listo** (D-0018): `parse_feed` puro (feedparser, testeable sin red) +
> `HttpFeedFetcher` (httpx) tras `FeedFetcher`; resiliente a feeds caídos. Ya alimenta al motor.
>
> **Máquina de pausa por tema lista** (pura): `decide_generation` (GENERATE/PAUSE/HOLD) +
> `PauseController` que avisa a la Bandeja vía el puerto `ActionInbox`.
>
> **Persistencia de temas y entregas lista y verificada contra Postgres real.** Puertos
> `TopicStore` y `DeliveryStore` (in-memory + Postgres), migraciones `0002`/`0003`, capacidades
> `create_topic`, `list_topics`, `record_delivery`, `mark_delivery_consumed`. `Base` declarativa en
> `platform/orm.py`. Módulo ensamblado con `HeraldoDeps`. **61 tests + 7 de integración** (verdes con
> DB), ruff + mypy strict OK.
>
> **Scheduler determinístico listo** (`TopicScheduler`): recorre temas activos, consulta la última
> entrega y aplica `PauseController`; devuelve los temas a generar y pausa los que tienen pendiente.
> Test confirma que pausar un tema no bloquea a otro. **65 tests + 7 de integración**, todo verde.
>
> **Disección interactiva** (D-0020, primer uso de IA) y **productor del noticiero** (D-0021/D-0022)
> listos. `deepen_stories` arma tarjetas por capas con **IA perezosa** (solo lo seleccionado),
> **batching inteligente** (`plan_batches`: troceo por ítems/tokens-in/tokens-out) y **caché por
> hash**. Puerto `Completer` + `MeteredCompleter` (todo costo medido). **10 capacidades MCP-ready**,
> **85 tests + 7 de integración**, ruff + mypy strict en verde.
>
> **Módulo Heraldo completo y cableado** (D-0023): productor de podcast (`compose_episode`) listo,
> composition root + API genérica (`GET /modules`, `POST /modules/{id}/capabilities/{name}`), y
> adaptador **Gemini directo** para el carril inmediato. El app arranca y expone las **9 capacidades**.
> **94 tests + 7 de integración**, ruff + mypy strict en verde. Audio con adaptadores interinos.
>
> **🚀 DESPLEGADO Y VIVO EN PRODUCCIÓN** (jul-2026): backend en Render + Supabase (DB+Storage) +
> Gemini. Verificado en vivo: `/health`, `/modules`, disección con Gemini real, y `create_topic`/
> `list_topics` escribiendo y leyendo de Supabase. URL: jarvis-backend-cs90.onrender.com. Modelo de
> texto por defecto: `gemini-flash-latest` (el `2.5-flash` quedó deprecado). Falta: frontend, probar
> el audio (compose_episode con TTS), configurar feeds reales, y las mejoras (selector de modelo, etc.).
>
> **Audio real + deploy listos** (D-0024): TTS por Gemini directo (PCM→WAV) + Supabase Storage;
> Dockerfile + `render.yaml` + `docs/DEPLOY.md`; imagen Docker verificada (build + boot + endpoints).
> **98 tests + 7 de integración**, ruff + mypy strict en verde. Heraldo está **listo para producción**.
>
> **Próximo paso:** desplegar siguiendo `docs/DEPLOY.md` (Render + Supabase) y probar en vivo con las
> keys. Luego: **frontend web** (`apps/web` → Vercel) para consumir la API; **ruteo por urgencia**
> ("ya"/"económico", D-0017); **selector de modelo dinámico** (`ModelRouter`, ver `mejoras_importantes.md`);
> más fuentes (Tavily/X/newsletters) + libro mayor. Memoria: consolidación (episodic) y decaimiento.

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
- [x] Adaptador de fuente **RSS/Atom** (feedparser) tras `SourceAdapter`: parseo puro + descarga httpx.
- [x] Adaptador **Tavily** (búsqueda web real del tema) tras `SourceAdapter`; se cablea con
      `JARVIS_TAVILY_API_KEY`. Fundamenta el contenido en fuentes reales.
- [x] Prompts con **sustancia** (ideas no obvias, respaldadas) y **registro chileno moderado**
      (compartido en `prompts.py`); voz del podcast **seleccionable** (`list_voices` + param `voice`);
      duración configurable y más precisa (piso de palabras + ~160 ppm).
- [ ] Más fuentes (X → newsletters) tras el mismo puerto.
- [ ] Libro mayor de fuentes: costo por fuente + aporte (ítems, únicos, al output final).
- [x] **Disección interactiva del tema** (primer uso de IA, D-0020): capacidades
      `propose_topic_questions` + `compile_topic_profile`; 2 llamadas medidas, salida JSON.
      Puerto `Completer` + adaptador `MeteredCompleter` (costo registrado).
- [x] Máquina de **pausa por tema** (pura, cero IA): pausa al haber 1 entrega sin consumir
      (consumido = abrir/reproducir), independiente entre temas, deja acción en la Bandeja.
- [x] Persistencia de **temas** (puerto `TopicStore`; adaptadores in-memory y Postgres) +
      migración `0002` + capacidades `create_topic`/`list_topics`. Verificado contra Postgres real.
- [x] Persistencia de **entregas** (`Delivery`): puerto `DeliveryStore` (in-memory + Postgres),
      migración `0003`, capacidades `record_delivery`/`mark_delivery_consumed`. Verificado con DB real.
- [x] Scheduler determinístico (`TopicScheduler`): por cada tema activo consulta la última entrega
      y aplica `PauseController` → devuelve los temas a generar y pausa los que tienen pendiente.
- [x] Política de pausa de **noticias** por ventana (`decide_news_generation`, 3 días sin respuesta;
      cualquier respuesta reinicia). Distinta de la estricta del podcast (D-0021).
- [x] Menú de opciones: `gather_stories` da candidatos con **id estable** (hash de URL) + extracto.
- [x] **Noticiero: tarjeta por capas** (`deepen_stories`): IA perezosa (solo lo seleccionado),
      **batching inteligente** (troceo por ítems/tokens-in/tokens-out, D-0022) y **caché por hash**.
      Fuentes determinísticas; capas hook→línea→puntos→detalle→porqué.
- [x] **Podcast** (`compose_episode`): selección → guion en lote (narrador/diálogo, largo por
      duración) → TTS → audio alojado. Puertos `SpeechSynthesizer` y `AudioStorage`.
- [x] **Cableado real** (D-0023): composition root (`platform/composition.py`) + API genérica de
      capacidades (`GET /modules`, `POST /modules/{id}/capabilities/{name}`). Adaptador **Gemini
      directo** (LLMProvider) para el carril inmediato. App arranca y expone las 9 capacidades.
- [x] **Audio real**: TTS por Gemini directo (PCM→WAV) + Supabase Storage (URL pública). La
      composition usa los reales con keys, interinos si no.
- [x] **Deploy listo** (D-0024): Dockerfile + `render.yaml` (root `apps/backend`) + `docs/DEPLOY.md`.
      Imagen verificada (build + boot + `/health` + `/modules`). Migraciones al arrancar.
- [ ] Ruteo por urgencia seleccionable: "ya" (Gemini directo) vs "económico" (Gemini Batch 50%).
- [ ] Guion del podcast (narrador/diálogo) + TTS por Gemini Batch; audio en almacenamiento.

### Fase 6+ — Cerebro Córtex y grafo temporal
- [ ] Orquestador conversacional sobre módulos; memoria de grafo (Graphiti) si se justifica.

### Futuro (no comprometido)
- Canal Telegram como adaptador, con políticas propias de contexto.
- Integraciones: correo, calendario.

## Cómo actualizar este archivo
Al cerrar un avance: mueve los checks, y reescribe el bloque **Estado actual** con el
próximo paso concreto. Ese bloque es lo que permite retomar sin releer el repo.
