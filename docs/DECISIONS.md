# Bitácora de decisiones — Jarvis

Registro de decisiones estructurales y su justificación. Se lee antes de cambiar algo
de fondo; se agrega una entrada nueva por cada decisión que condicione el diseño.
Formato: cada entrada con contexto, decisión, alternativas descartadas y estado.

---

## D-0001 — Stack base: Python + FastAPI, Postgres + pgvector, OpenRouter
**Estado:** aceptada · Fase 0

**Contexto.** Se necesita un backend orientado a orquestación de IA, costo mínimo y
escalabilidad, con nube desde el inicio pero lo más barata posible.

**Decisión.**
- Backend Python 3.12+ / FastAPI async; gestor `uv`.
- Una sola base: PostgreSQL con `pgvector` para relacional + vectorial (evita sumar
  una base vectorial dedicada y su costo/operación).
- LLM vía OpenRouter, siempre detrás del puerto `LLMProvider`.

**Alternativas descartadas.**
- TypeScript full-stack: ecosistema IA/orquestación menos maduro que Python.
- Base vectorial dedicada (Pinecone/Qdrant/Weaviate): más costo y más servicios; pgvector
  alcanza y sobra para la escala inicial y se puede migrar detrás del puerto `VectorStore`.

---

## D-0002 — Arquitectura hexagonal + monolito modular
**Estado:** aceptada · Fase 0

**Contexto.** Escalabilidad extrema exigida, pero operar microservicios desde el día 1 es
caro y prematuro.

**Decisión.** Monolito modular con puertos y adaptadores. Dominio puro sin dependencias de
infraestructura. Se parte en servicios solo cuando la escala lo exija; el desacoplamiento
por puertos hace esa migración barata.

**Alternativas descartadas.** Microservicios desde el inicio (costo operacional y complejidad
sin retorno a esta escala).

---

## D-0003 — Pipeline costo-primero: determinístico antes que IA
**Estado:** aceptada · Fase 0

**Contexto.** El ahorro de tokens es prioridad #1.

**Decisión.** Todo request pasa por una cadena que intenta cerrarse antes del LLM: reglas
determinísticas → caché semántico → router de modelo barato → contexto acotado por RAG con
presupuesto de tokens → LLM con salida estructurada. Detalle en `ARCHITECTURE.md`.

**Alternativas descartadas.** Enviar todo directo a un LLM "capaz" por defecto (simple pero
caro y no escalable en costo).

---

## D-0004 — Canales como adaptadores; web primero, Telegram después
**Estado:** aceptada · Fase 0

**Contexto.** La interacción principal es web, pero se anticipa Telegram u otros canales.

**Decisión.** La lógica del asistente no conoce el canal. Cada canal es un `ChannelAdapter`.
Web se construye primero; Telegram entra después sin tocar el núcleo y con políticas propias
de contexto (hilos largos son más difíciles de retomar en chat).

**Alternativas descartadas.** Acoplar la lógica a la web (haría cara y riesgosa la extensión
a otros canales).

---

## D-0005 — Entidad `UsageRecord` + puerto `UsageMeter` para telemetría de costo
**Estado:** aceptada · Fase 0

**Contexto.** El dashboard de costo (requisito del usuario) necesita desglosar el gasto de
IA por modelo, por tarea y por día, con revelación progresiva.

**Decisión.** Cada llamada de IA (o llamada evitada) emite un `UsageRecord` con dimensiones
`occurred_at`, `model`, `task`, `channel`, `tokens_in/out`, `cost`, `outcome`, `request_id`,
detrás del puerto `UsageMeter`. Las agregaciones se resuelven en SQL, no en la app. Detalle
en `ARCHITECTURE.md`.

**Alternativas descartadas.** Loguear costo solo como texto (no permite desglose ni dashboard);
agregaciones en memoria en la app (más caro y menos escalable que SQL).

---

## D-0006 — Despliegue: Render (backend) + Vercel (frontend) + Supabase (Postgres+pgvector)
**Estado:** aceptada · Fase 0

**Contexto.** Nube desde el inicio, costo mínimo, sin sacrificar escalabilidad ni proactividad.

**Decisión.**
- Frontend estático en **Vercel** (free).
- Backend containerizado en **Render**, instancia chica *always-on* pagada (~US$7/mes) para
  evitar cold starts que romperían la proactividad.
- Postgres + pgvector en **Supabase** (free tier): además de la base, aporta storage y auth
  que probablemente usaremos más adelante, todo detrás de nuestros puertos.

**Razón.** Costo base acotado (~US$7/mes + OpenRouter variable). Backend en Docker detrás de
puertos ⇒ portable, sin lock-in. Sobra para la escala de un asistente personal.

**Alternativas descartadas.** Render free tier para el backend (se duerme, mata proactividad);
Neon (válido, pero Supabase suma storage/auth en el mismo free tier); Fly.io/Railway.

---

## D-0007 — Embeddings vía OpenRouter con `baai/bge-m3` (1024 dims)
**Estado:** aceptada · Fase 1

**Contexto.** Se necesita un proveedor de embeddings barato y confiable para RAG. Idealmente
sin sumar proveedores ni keys nuevos.

**Decisión.** OpenRouter expone un endpoint de embeddings OpenAI-compatible
(`/api/v1/embeddings`), con el mismo key que el chat. Se usa `baai/bge-m3` por defecto
(1024 dims, multilingüe, ~US$0.01/M tokens), detrás del puerto `EmbeddingProvider`. La
dimensión del vector (1024) fija la columna de pgvector. Cada llamada se mide como costo.

**Alternativas descartadas.** OpenAI text-embedding-3-small o Google text-embedding-004
(sumaban un proveedor y key aparte); modelo local (consume RAM de la instancia Render chica).
Todas siguen disponibles: basta cambiar el adaptador, porque el dominio depende del puerto.
Nota: cambiar de modelo con otra dimensión obliga a re-embeber lo ya guardado.

## D-0008 — Modelo de memoria: log ≠ memoria, con presupuestos separados y hechos graph-ready
**Estado:** aceptada · Fase 1

**Contexto.** La memoria es lo que hace a Jarvis personal y también el mayor riesgo de costo.
Hay que decidir qué entra, cómo se inyecta y cómo se registra sin gastar tokens de más.

**Decisión.** Se separan tres presupuestos que no deben confundirse:
- **Guardar** (log crudo de turnos en Postgres) = SQL, $0 en tokens. Nunca se inyecta entero.
- **Escribir memoria** = ascender del log a memoria recuperable. Vía escalera de lo barato a
  lo caro: (1) señales explícitas por regex, (2) eventos estructurados a tablas propias,
  (3) heurística de salience, (4) extractor LLM **solo por lotes, modelo barato, sobre una
  ventana** — nunca mensaje por mensaje. Resumen **rodante y jerárquico** (resume turnos
  nuevos + resumen anterior, no todo el historial) ⇒ costo de escritura acotado.
- **Inyectar** = armar contexto con **presupuesto fijo de tokens**, recorte determinístico por
  prioridad: system → ficha del usuario (~300 tok) → working (~8 turnos) → RAG top-k (k=5 con
  umbral) → resumen episódico. La recuperación es búsqueda en pgvector (cero IA).

**Hechos graph-ready (D-0008b).** Los hechos durables se modelan como
`sujeto–predicado–objeto + tiempo`, detrás de un puerto `MemoryStore`. Hoy viven en Postgres;
mañana un adaptador de grafo temporal (Graphiti/Zep) se alimenta del mismo pipeline de
consolidación, sin reescritura. Ver D-0012.

**Mejoras incluidas.** Dedup por similitud antes de escribir; decaimiento/olvido
(`last_accessed`, `access_count`, archivado de lo viejo no usado); caché semántico antes de
recuperar. Cada embedding y consolidación emite `UsageRecord` ⇒ el costo de la memoria es visible.

**Knobs por defecto (calibrables):** working ~8 turnos / ~1–2k tok; RAG k=5 con umbral;
ficha ~300 tok; consolidación al cerrar sesión + umbral de tokens en sesiones largas.

**Alternativas descartadas.** Resumir turno por turno con LLM (costo lineal en tokens);
inyectar historial completo (costo explosivo); solo vectorial sin hechos graph-ready (deuda
para el cerebro futuro); montar el grafo desde ya (prematuro, infra antes del chat básico).

---

## D-0009 — Reglas de módulos: un módulo = un "trabajo" del usuario
**Estado:** aceptada · Fase 2+

**Contexto.** El producto será "muchas apps en una". Se necesita un criterio claro para no caer
ni en god-modules ni en fragmentación.

**Decisión.** Un **módulo** = un job-to-be-done con su propio dominio de datos y su identidad de
tabbar (se siente como app propia). Reglas:
- **Mismo módulo** si comparte trabajo *y* datos (ej.: podcast + noticiero = módulo de
  aprendizaje "Oráculo": el trabajo es "mantenme informado con audio curado").
- **Módulo nuevo** solo si cambia el trabajo *y* el modelo mental *y* los datos.
- **Anti-god-module:** si el tabbar del módulo necesita >~5 acciones no relacionadas, se parte.
- **Anti-fragmentación:** si dos módulos comparten datos y el usuario salta constante entre
  ellos, son uno.
- Cada módulo es un **slice vertical** (dominio + casos de uso + adaptadores + API + UI) y
  **expone sus capacidades como funciones tipadas** (tool-calling / MCP-ready) para que el
  cerebro futuro (D-0012) las invoque sin trabajo extra.
- Nombres **simples y épicos**, una palabra. Propuestos: Oráculo (aprendizaje), Bóveda
  (contabilidad), Córtex (cerebro). La Bandeja es sistema, no módulo (ver D-0010).

**Alternativas descartadas.** Módulos por feature técnica (fragmenta); un mega-módulo con
todo (god-module, mata la cohesión).

---

## D-0010 — Frontend web + app mobile: rendimiento percibido y arquitectura de tabbar
**Estado:** aceptada · Fase 3

**Contexto.** Se quiere UI limpia y profesional, carga rapidísima que no bloquee, y una app
mobile personal, offline-first y modular ("muchas apps en una").

**Decisión.**
- **Nada bloquea la primera pintura:** shell instantáneo → skeletons → datos por streaming.
  Módulos con lazy loading (un chunk por módulo). UI optimista + feedback inmediato; sin
  spinners que congelen. Presupuesto de rendimiento medido como métrica de salud.
- **Animación barata:** solo `transform`/`opacity` (GPU); librería `motion` para lo declarativo,
  CSS para lo micro. Si una animación toca layout o cuesta RAM, no va.
- **Paleta:** base neutra (2–3 grises + fondo) + **un** color de acento, con modo claro/oscuro.
- **Mobile:** Expo (React Native), comparte modelo y código con la web. **Hub central**: el
  ícono central del tabbar siempre vuelve al Hub; cada módulo reemplaza el tabbar por el suyo.
  **Offline-first:** cada módulo declara el mínimo que necesita sin señal y sincroniza al volver.
- **Piezas transversales (sistema, no módulos):** contabilidad de IA (igual que web) y
  **Bandeja de Jarvis** (human-in-the-loop): ítems que requieren aprobación/respuesta,
  ordenables por módulo (luego por hora) o por hora de llegada, filtrables por ambos. Es el
  canal por donde el cerebro futuro pedirá permiso; contrato común "ítem que requiere al usuario".

**Alternativas descartadas.** Flutter/nativo (otro lenguaje, duplica trabajo para un solo
usuario); animaciones JS pesadas; multi-acento (más caro de mantener consistente).

---

## D-0011 — Batching obligatorio siempre que se pueda
**Estado:** aceptada · Fase 1

**Contexto.** Prioridad #1 es el ahorro. Muchas operaciones agrupables se pagan de más si se
hacen una por una.

**Decisión.** Regla dura: **toda operación agrupable se agrupa** — embeddings (OpenRouter acepta
array en `input`), consolidaciones de memoria, notificaciones a la Bandeja, escrituras a DB.
Nada de una llamada por ítem si puede ser una por lote. Se mide en el dashboard.

**Alternativas descartadas.** Procesar ítem por ítem por simplicidad (viola Prioridad #1).

---

## D-0012 — Cerebro/orquestador (Córtex): modelo Claude vía OpenRouter, módulos como herramientas
**Estado:** propuesta (diseño a futuro, se implementa en fase posterior) · Fase 5+

**Contexto.** El norte es una secretaria virtual con la que conversas y que decide qué módulo
activar, te entrega reportes, etc. Debe poder implementarse de forma natural, no como parche.

**Decisión de diseño (para no cerrar puertas).**
- **Córtex = orquestador que llama a los módulos como herramientas tipadas** (por eso D-0009
  exige que cada módulo exponga capacidades MCP-ready desde el primer día).
- **Motor del runtime:** modelo Claude potente **vía OpenRouter** (mismo gateway/key, medible,
  dentro de términos), reservado solo para razonar/orquestar; ruteo a cheapest-capable para el
  resto. Todo detrás del puerto `LLMProvider`.
- **Suscripción Claude:** se usa para *construir* Jarvis (Claude Code), **no** como motor del
  Jarvis desplegado. Los términos priorizan uso interactivo, no un backend autónomo 24/7
  (reverificar términos vigentes antes de apoyarse en ello). Si cambian, es swap de adaptador.
- **Memoria del cerebro:** los hechos graph-ready de D-0008 alimentan a Córtex; el grafo
  temporal (Graphiti) entra cuando se justifique.

**Alternativas descartadas.** Acoplar Córtex a un proveedor concreto (rompe el puerto); usar la
suscripción como motor del backend desplegado (fuera de términos / riesgoso).

---

## D-0013 — Monorepo con carpetas por app (backend / web / mobile / shared)
**Estado:** aceptada · Fase 1

**Contexto.** Entran web (React/Vite) y mobile (Expo/RN) junto al backend (Python/FastAPI). Hay
que decidir cómo se organiza el código.

**Decisión.** **Un solo repositorio (monorepo)** con carpetas por app:
`apps/backend`, `apps/web`, `apps/mobile`, y `packages/shared` para tipos TS compartidos
(contratos de API, modelos de módulo) entre web y mobile. `docs/` y `CLAUDE.md` en la raíz;
`docker-compose.yml` en la raíz orquesta todo. Cada app conserva su propio build/deploy/deps.

**Razón.** Web y mobile son TS/React ⇒ contratos definidos una vez en `shared`. Cambios
atómicos backend+clientes en un commit. Menos fricción para retomar. El aislamiento se mantiene
por app; monorepo es organización, no acoplamiento.

**Alternativas descartadas.** Repos separados (duplican tipos o exigen paquete versionado y PRs
coordinados; solo valen con equipos o releases independientes, que no aplican a un dev solo).

---

## D-0014 — Persistencia: SQLAlchemy 2.0 async + Alembic; multiusuario-ready con owner_id
**Estado:** aceptada · Fase 1

**Contexto.** La memoria necesita persistencia en Postgres+pgvector, con esquema evolucionable y
lista para escalar. Aunque hoy es de un solo usuario, la visión exige no impedir multiusuario.

**Decisión.**
- **SQLAlchemy 2.0 async** (con `asyncpg`) como capa de acceso, **Alembic** para migraciones
  versionadas. Todo detrás del puerto `MemoryStore`; el dominio no conoce SQLAlchemy.
- **`owner_id` en todas las filas** (log y hechos) desde el día 1. Hoy es una constante; habilitar
  multiusuario no exigirá migrar datos ni reescribir queries.
- **Índice HNSW** con `vector_cosine_ops` sobre la columna `VECTOR(1024)`.
- Tests: fakes en memoria para dominio/casos de uso; test de integración del adaptador pgvector
  contra Postgres real (docker-compose, puerto configurable con `JARVIS_DB_PORT`; se salta si no
  hay `JARVIS_TEST_DATABASE_URL`). Runtime real siempre Postgres en servidor, nunca SQLite.

**Alternativas descartadas.** asyncpg puro (migraciones y mapeo a mano); SQLModel (menos maduro
en async); IVFFlat (HNSW da mejor calidad/latencia a esta escala); single-user sin owner_id
(migración cara si algún día se abre a multiusuario).

---

## D-0015 — Contrato de módulos: capacidades tipadas MCP-ready + registro
**Estado:** aceptada · Fase 5

**Contexto.** Los módulos (D-0009) deben ser descubribles y orquestables por Córtex sin que
este conozca sus detalles. Hay que fijar el contrato común antes del primer módulo.

**Decisión.** Un módulo es una rebanada vertical que expone `Capability` (nombre, descripción,
modelos Pydantic de entrada/salida y handler async) con `input_schema()` en JSON — **MCP-ready
desde el día uno**. `Module` agrupa capacidades y `ScheduledJob` (trabajos proactivos); un
`ModuleRegistry` los descubre. Vive en `jarvis/modules/core.py`. Córtex invocará capacidades
por su esquema, sin acoplarse a la implementación.

**Alternativas descartadas.** Handlers sueltos sin esquema (no orquestables por IA); acoplar
módulos a FastAPI (rompe hexagonal; la API es solo otro invocador de capacidades).

---

## D-0016 — Módulo Heraldo: motor único agregador + dos carriles (async/sync)
**Estado:** aceptada · Fase 5

**Contexto.** El primer módulo (aprendizaje continuo) combina podcast programado, noticiero y
búsqueda en vivo. Los tres piden lo mismo: reunir contenido de calidad de varias fuentes.

**Decisión.** **Un solo motor agregador determinístico** alimenta a los tres consumidores.
Pipeline sin IA: ingesta → normalizar URL → clustering (el **alcance = nº de fuentes
independientes** sale del clustering) → filtrar (recencia, keywords, alcance) → rankear.
Dos carriles: **asíncrono** (podcast + noticiero programado, todo por lote) y **síncrono**
(en vivo, solo cuando se pide). La IA se reserva a 3 puntos: disección del tema (1 vez),
resumen de clusters (por lote, con caché por hash) y guion del podcast. Nombre del módulo:
**Heraldo** (id `herald`).

**Alternativas descartadas.** Un pipeline por consumidor (duplica ingesta y dedup); resumir
cada ítem en vez de cada cluster (más tokens); medir alcance con IA (el clustering lo da gratis).

---

## D-0017 — Proveedores de Heraldo: Gemini Batch TTS, Tavily en vivo, podcast por tema
**Estado:** aceptada · Fase 5

**Contexto.** Hay que elegir voz del podcast, motor de búsqueda en vivo y formato, minimizando
costo. Precios verificados en jul-2026.

**Decisión.**
- **Voz:** Gemini Flash TTS por **Batch API (50% off, asíncrono)** — los podcasts se generan por
  adelantado, así que el lote calza perfecto (~$0.075 por episodio de 10 min). Por verificar
  antes de cablear: que Batch acepte salida TTS; el puerto tendrá `synthesize_batch` con caída a
  TTS interactivo sin cambiar el diseño.
- **En vivo:** Tavily (agrega fuentes y extrae en una llamada; 1.000 consultas gratis/mes),
  detrás de un puerto de fuente.
- **Podcast configurable por tema:** narrador o diálogo dos-voces (Gemini soporta multi-speaker).
- **Fuentes primera ola:** RSS/APIs gratis + Tavily + X + newsletters, todas tras el puerto
  `SourceAdapter`, con **libro mayor de fuentes**: costo (vía `UsageRecord`) y aporte
  determinístico (ítems, ítems únicos, ítems al output final) para decidir si una fuente paga vale.

**Alternativas descartadas.** ElevenLabs (10x más caro para uso personal); OpenAI TTS (bueno pero
sin lote a 50%); Brave como motor en vivo primario (sin tier gratis desde feb-2026); medir el
valor de una fuente con IA (las métricas de aporte son determinísticas).

---

## D-0018 — Parseo de feeds con feedparser
**Estado:** aceptada · Fase 5

**Contexto.** El adaptador RSS debe leer la realidad desordenada de RSS 2.0, RSS 1.0 y Atom, con
variantes de fecha y encoding. Escribir eso a mano es frágil.

**Decisión.** Usar **feedparser** (estándar de facto en Python) para parsear. Queda aislado en
`sources/rss.py`: `parse_feed(xml, fallback, now)` es puro y no toca la red (testeable con
fixtures); la descarga vive en `HttpFeedFetcher` (httpx), inyectable tras `FeedFetcher`.

**Alternativas descartadas.** Parseo a mano con lxml/ElementTree (reinventa el manejo de las
variantes y fechas, sin ganancia real).

---

## D-0019 — Distribución de la app móvil sin App Store (personal)
**Estado:** aceptada · Fase 4 (dirección, aún no implementada)

**Contexto.** La app móvil es personal y no se publicará en la App Store. Duda: cómo lograr 100%
de funcionalidad y cuál es la mejor vía de instalación. El usuario ya tiene cuenta de Apple
Developer ($99/año).

**Decisión.** Mantener la cuenta de Apple Developer y distribuir **fuera** de la App Store:
- **iOS:** EAS Build + **TestFlight interno** (sin revisión, auto-actualiza, build válido 90 días;
  re-subida vía `EAS Submit`, automatizable). Alternativa: build ad-hoc/`.ipa` en equipos
  registrados (válido ~1 año). Se descarta el Apple ID gratis (re-firma cada 7 días, sin push).
- **Android:** EAS Build → APK sideload (sin cuenta ni caducidad).
- **OTA:** **Expo Updates** para empujar cambios JS/assets por aire; solo cambios nativos exigen
  rebuild. La app es cliente delgado (backend en Render), así que la mayor parte se actualiza en
  servidor.

**Razón.** La App Store es canal + revisión, no una puerta a capacidades: push, background, etc.
se habilitan por *entitlements*, disponibles con la cuenta de desarrollador sin publicar. Así se
obtiene funcionalidad nativa completa sin listado público ni fricción de revisión.

**Alternativas descartadas.** PWA como canal principal (iOS limita background/push y offline real);
Apple ID gratis (caducidad de 7 días); publicar en App Store (revisión y exposición innecesarias
para uso personal).

---

## D-0020 — Disección interactiva del tema: 2 llamadas medidas con salida estructurada
**Estado:** aceptada · Fase 5

**Contexto.** Crear un tema no debe quedar vago. El usuario quiere que Jarvis le pregunte, pero
la prioridad es ahorrar tokens. Es el primer uso de IA de Heraldo.

**Decisión.** Flujo de **dos llamadas acotadas** (capacidades separadas, sin estado en el
servidor entre ellas): `propose_topic_questions` genera 3-5 preguntas dirigidas; el cliente las
responde; `compile_topic_profile` compila un `TopicProfile` y crea el tema. Salida **siempre JSON**
(validada con Pydantic, tolerante a envoltorios), nunca prosa. La llamada pasa por el puerto
`Completer`, cuyo adaptador real `MeteredCompleter` (en `application/`) enruta por
`MeteredCompletion` → **todo costo queda medido**. El modelo concreto se fija en el ensamblado
(cheapest-capable); el `ModelRouter`/caché del pipeline costo-primero se conectará aquí cuando
exista (aún pendiente en Fase 1).

**Alternativas descartadas.** Conversación libre paso a paso (muchas llamadas + estado, más caro);
solo un borrador sin preguntar (no cumple el "que me pregunte"); prosa libre (no parseable,
más tokens). Proponer fuentes en esta versión (requiere descubrimiento de feeds; se difiere).

---

## Decisiones abiertas (pendientes)
- **Umbral y estrategia del caché semántico** (similitud mínima para considerar "equivalente").
- **Disparo exacto de la consolidación** (episodic) y política de decaimiento/olvido.
