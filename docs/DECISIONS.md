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
- Backend Python 3.14+ / FastAPI async; gestor `uv`.
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

## D-0017 — Proveedores de Heraldo: TTS por OpenRouter, Tavily en vivo, podcast por tema
**Estado:** aceptada · Fase 5 · **revisada** (jul-2026: OpenRouter ya soporta TTS)

**Contexto.** Hay que elegir voz del podcast, motor de búsqueda en vivo y formato, minimizando
costo. Al verificar precios (jul-2026) se confirmó que **OpenRouter ya expone un endpoint
`/audio/speech`** (compatible con OpenAI) con modelos TTS, incluido **Gemini 3.1 Flash TTS**.

**Decisión.**
- **Carril inmediato = Gemini directo:** como ya manejamos la key de Gemini, para lo inmediato se
  llama **directo a Google**, no por OpenRouter, para no pagar su margen. OpenRouter queda como
  **escape** para modelos no-Gemini o cuando salga más barato. Ambas keys en `.env`.
- **Ruteo por urgencia (seleccionable por pedido):** el usuario elige el modo por cada generación:
  **"ya"** (interactivo, Gemini directo — para lo que quiere al momento) o **"económico"** (Gemini
  **Batch API**, 50% off, asíncrono ~24h — para lo pre-generado). Regla: *siempre que se pueda usar
  Gemini Batch, se usa* (50% off), salvo que OpenRouter tenga algo más barato incluyendo ese 50% a
  calidad aceptable, o que el usuario pida el resultado inmediato. **OpenRouter no tiene modo
  batch**; el batch va por la API directa de Google. Todo tras el puerto `Completer`/TTS.
- **Voz:** TTS detrás del puerto; hoy hay adaptadores interinos (`NullSpeechSynthesizer`,
  `InMemoryAudioStorage`) para que el guion fluya de punta a punta; el TTS real (Gemini/OpenRouter)
  y Supabase Storage se cablean como slice aparte con las keys.
- **En vivo:** Tavily (agrega fuentes y extrae en una llamada; 1.000 consultas gratis/mes),
  detrás de un puerto de fuente.
- **Podcast configurable por tema:** narrador o diálogo dos-voces.
- **Fuentes primera ola:** RSS/APIs gratis + Tavily + X + newsletters, todas tras el puerto
  `SourceAdapter`, con **libro mayor de fuentes**: costo (vía `UsageRecord`) y aporte
  determinístico (ítems, ítems únicos, ítems al output final) para decidir si una fuente paga vale.

**Alternativas descartadas.** Gemini Batch directo como primera opción (segundo proveedor/key +
orquestación de lote para ~$0.075 de ahorro por episodio; no vale la complejidad inicial, se deja
para cuando el volumen lo pida); ElevenLabs (10x más caro); Brave como motor en vivo primario
(sin tier gratis desde feb-2026); medir el valor de una fuente con IA (es determinístico).

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

## D-0021 — Noticiero: IA perezosa, tarjeta por capas y pausa por ventana
**Estado:** aceptada · Fase 5

**Contexto.** El noticiero debe entregar valor con mínimo gasto de IA y mínima fricción de
lectura (el usuario tiene déficit de atención: prefiere leer muy poco e interactuar). Su regla de
pausa difiere del podcast.

**Decisión.**
- **IA perezosa por selección (menú de opciones):** el motor **ofrece X noticias candidatas** sin
  IA (titular + extracto crudo + alcance + fuentes; cada una con id estable = hash de la URL). Tú
  **seleccionas de 0 a todas** las que quieres profundizar. Solo las seleccionadas gastan IA para
  armar su tarjeta por capas (cacheada por hash). Las no elegidas: **cero IA**. Expandir capas
  luego es gratis (client-side). El **mismo mecanismo aplica al podcast**: se ofrecen candidatos y
  eliges cuáles profundizar antes de generar el episodio (no todo se convierte en podcast).
- **Tarjeta por capas (revelación progresiva):** 1) gancho/titular llamativo (siempre visible),
  2) en una línea, 3) tres puntos clave, 4) detalle, 5) por qué importa + fuentes copiables. El
  backend produce todas las capas de una; el cliente las revela al apretar.
- **Pausa por ventana (≠ podcast):** las noticias **siguen llegando** aunque no respondas; se
  detienen solo tras **3 días sin ninguna respuesta**; **cualquier** respuesta (interesa o no)
  cuenta y reinicia la ventana. Implementado en `decide_news_generation` (política pura, aparte de
  la estricta `decide_generation` del podcast). Consumo/engagement de noticias = responder;
  del podcast = abrir/reproducir. Ambos reusan `Delivery.consumed_at` como marca de engagement.

**Alternativas descartadas.** Resumir todas las noticias con IA (gasta en lo que no te interesa);
tarjeta de un bloque largo (mala para déficit de atención); una llamada por capa al expandir (más
tokens sin ganancia); misma regla de pausa que el podcast (el usuario la quiere más laxa).

---

## D-0022 — Protocolo de batching inteligente (troceo por 3 topes) + IA perezosa con caché
**Estado:** aceptada · Fase 5

**Contexto.** Batching obligatorio (D-0011), pero meter demasiados ítems en una llamada degrada
la calidad, hace alucinar y puede reventar el contexto. El tope de **salida** suele ser el más
apretado (cada ítem genera respuesta). El límite seguro depende del proveedor/modelo.

**Decisión.**
- **`plan_batches` (en `application/batching.py`)** trocea una lista en lotes respetando **tres
  topes** por proveedor/modelo (`BatchLimits`): máximo de ítems, de **tokens de entrada** y de
  **tokens de salida**. Cada ítem declara su `ItemCost(input_tokens, output_tokens)`. Los lotes se
  procesan en paralelo. Reutilizable por cualquier operación batcheable.
- **IA perezosa + caché:** solo se procesa lo que el usuario elige; el resultado se cachea por id
  (hash de la URL en el caso de noticias) para no reprocesar. Primer uso: `NewsCardService`
  (tarjetas del noticiero) con `max_items=8`, `max_input=6000`, `max_output=2000` por defecto.

**Alternativas descartadas.** Batching ingenuo sin tope (alucina / revienta contexto); contar solo
tokens de entrada (el output es el cuello de botella); un límite global fijo (depende del proveedor).

---

## D-0023 — Composition root + API genérica de capacidades (estilo MCP)
**Estado:** aceptada · Fase 5

**Contexto.** El módulo se ensamblaba solo en tests. Para correrlo de verdad falta el punto que
inyecta proveedores reales y una forma de invocar capacidades por HTTP.

**Decisión.**
- **Composition root** en `platform/composition.py`: único lugar que conoce proveedores concretos.
  `build_registry(settings, client, engine)` arma el `ModuleRegistry`. Heraldo usa Gemini directo
  (carril inmediato) tras `MeteredCompleter`; almacenes Postgres si hay `DATABASE_URL`, en memoria
  si no (arranca sin base); fuentes RSS desde `JARVIS_HERALDO_FEEDS`.
- **API genérica** en `interfaces/api.py`: `GET /modules` describe módulos y capacidades con su
  esquema JSON (descubrimiento MCP-ready); `POST /modules/{id}/capabilities/{name}` valida e
  invoca (404 si no existe, 422 si los argumentos no calzan). La API no conoce proveedores.
- Recursos con red/DB (httpx, engine) viven en el **lifespan** de FastAPI; `create_app(registry=…)`
  permite inyectar un registro con fakes en los tests.

**Alternativas descartadas.** Un endpoint por capacidad (no escala; el registro ya las describe);
armar proveedores dentro de la API (rompe hexagonal); exigir Postgres para arrancar (fricción para
probar el plumbing).

---

## D-0024 — Deploy: Render (Docker) + Supabase, monorepo con roots por servicio
**Estado:** aceptada · Fase 5

**Contexto.** Hay que dejar el backend corriendo en producción sin perder velocidad y sin separar
el repo.

**Decisión.** **Monorepo** con raíz por servicio (no afecta rapidez: cada build empaqueta solo su
carpeta). Backend en **Render** vía Docker (`apps/backend/Dockerfile`, `dockerContext: apps/backend`,
`render.yaml` en la raíz); corre `alembic upgrade head` al arrancar y luego uvicorn; health `/health`.
Base y audio en **Supabase** (Postgres+pgvector vía `DATABASE_URL` directo al puerto 5432; bucket
público `podcasts`). Secretos por variables de entorno (`sync: false`). Frontend en **Vercel** con
*Root Directory* `apps/web` cuando exista. Runbook en `docs/DEPLOY.md`. Imagen Docker verificada
localmente (build + boot + `/health` + `/modules`).

**Alternativas descartadas.** Un repo por instancia (el monorepo con roots no impacta velocidad);
pooler de Supabase (6543) para el backend persistente (problemas de prepared statements con asyncpg);
migraciones a mano en cada deploy (el arranque del contenedor las aplica idempotente).

---

## D-0025 — Selección de modelo por tarea: catálogo dinámico, ranking gratis-primero, default fijo
**Estado:** aceptada · Fase 5/3 (backend + frontend)

**Contexto.** El usuario quiere cambiar fácil el modelo por (módulo, tarea) **desde el frontend**,
viendo **solo modelos capaces** ("que cumplan la pega"), aprovechar modelos gratis nuevos sin
buscarlos, y sin usar un "gratis" que en realidad ya es pagado.

**Decisión.**
- **Catálogo dinámico:** `ModelCatalog` (puerto) + adaptador que refresca a diario desde `/models`
  de OpenRouter (id, nombre, precio, contexto, modalidad, si es gratis) más entradas manuales de los
  proveedores gestionados (Gemini). El **precio se lee en vivo del catálogo**, nunca un flag "gratis"
  cacheado: gratis = precio actual $0; si sube, el modelo **baja solo** en el ranking.
- **Filtro "cumple la pega":** cada tarea declara su `ModelRequirement` (modalidad texto/tts/embedding,
  si exige JSON/estructurado, contexto mínimo). Solo se muestran los modelos capaces.
- **Ranking (gratis-primero):** capaz → gratis primero (por precio actual) → más barato → gama de
  calidad curada. Diseñado para incorporar luego un **puntaje de calidad** de la eval por tarea.
- **Default = modelo fijo por tarea** que el usuario define (predecible, sin auto-switch silencioso);
  el frontend muestra el ranking para switchear manual. Persistido en `ModelOverride` (DB, por
  owner/módulo/tarea). `ModelResolver` decide en cada llamada; el `Completer`/adaptadores usan ese
  modelo+proveedor.
- **Eval por tarea (diseñar para ello desde ya, construir después):** harness que corre un set de
  prueba por tipo de tarea, **manual y de bajo costo**, puntúa la calidad de cada modelo capaz y
  alimenta la dimensión de calidad del ranking. La arquitectura no debe requerir rehacerse para esto.
- **API:** `GET /models?task=…` (capaces + metadata + precio en vivo), `GET/PUT` del override por
  tarea. **Frontend:** selector por tarea con badge de gratis, precio y contexto.

**Alternativas descartadas.** Flag "gratis" cacheado (peligroso: un modelo puede dejar de ser
gratis); auto-switch silencioso por defecto (el usuario quiere control y predecibilidad); eval con
IA en cada request (caro; la eval es manual y puntual); mostrar todos los modelos (ruido: solo los
capaces).

---

## D-0026 — Cada módulo lleva su propia configuración transversal
**Estado:** aceptada · Fase 5/3 (backend + frontend)

**Contexto.** El usuario quiere gobernar cada módulo por separado: elegir modelos, ver el gasto
**de ese módulo** y otros ajustes que son transversales al módulo (fuentes, carril, topes). No un
panel global difuso, sino una superficie de configuración por módulo.

**Decisión.**
- Todo módulo expone una **superficie de configuración propia** con tres bloques mínimos:
  1. **Modelos por tarea** — reutiliza el selector de [[D-0025]] (ranking gratis-primero, precio en
     vivo, default fijo) filtrado a las tareas que declara el módulo.
  2. **Gasto del módulo** — costo agregado **atribuido a ese módulo** (por tarea/fuente), con **tope
     configurable** por módulo. La medición ya existe por request; se etiqueta con `module_id` para
     poder agrupar.
  3. **Ajustes transversales del módulo** — fuentes (con su ledger de "¿vale lo que cuesta?"), carril
     por defecto (ya/económico), y lo específico del dominio.
- El contrato `Module` gana la capacidad de **declarar su config** (tareas con `ModelRequirement`,
  fuentes, topes) de forma que el frontend la renderice genéricamente. Mismo patrón para todo módulo
  futuro: config transversal derivada del contrato, no hecha a mano por módulo.
- La atribución de costo se apoya en la medición existente (`MeteredCompletion`/`MeteredCompleter`),
  agregando `module_id`/`task` a lo que ya se registra.

**Alternativas descartadas.** Panel de configuración global único (mezcla módulos, no escala);
config hardcodeada por módulo en el frontend (rompe el patrón genérico y duplica trabajo por módulo).

---

## D-0027 — App móvil: caparazón de módulos con hub central fijo (Expo)
**Estado:** aceptada · Fase 4 (scaffolding hecho)

**Contexto.** La app móvil es la superficie de mayor uso (escuchar podcasts caminando). Debe ser
intuitiva, profesional, muy interactiva/visual, de carga rápida y offline-first. El usuario definió
la navegación: **el centro del tab bar es lo único fijo** y lleva a la selección de módulos; desde
ahí se llega a lo transversal (costos, mensajes). Las pestañas laterales son del módulo activo.

**Decisión.**
- **Stack:** Expo (React Native) + TypeScript + expo-router (file-based). Un solo código para iOS
  (y Android gratis), push, offline y build para App Store con la cuenta de desarrollador.
- **Caparazón + módulos-plugin:** `app/_layout.tsx` monta un `<Stack>` y un **TabBar persistente**
  por encima. El TabBar lee un store (`zustand`) con las pestañas del contexto activo. El **hub
  central** (botón elevado) es fijo y navega a `/hub`.
- **Contrato de módulo en el frontend** (`src/modules/types.ts` → `ModuleDef`): id, nombre, glyph,
  pestañas y home. `registry.ts` lista los módulos; el hub y el TabBar los renderizan genéricamente.
  Agregar un módulo = sumar su `ModuleDef` + sus pantallas, sin tocar el caparazón. Espeja el
  contrato `Module` del backend ([[D-0015]]).
- **Transversal desde el hub:** `hubTabs` = Costos + Mensajes (Bandeja). Al abrir el hub, esas son
  las pestañas laterales; deja espacio para una tercera si aparece.
- **Config por módulo** ([[D-0026]]) vive dentro del módulo (`heraldo/config`): modelos por tarea,
  fuentes y —a futuro— gasto del módulo.
- **Identidad visual:** tipografía Archivo + Figtree (T4), paleta "Vocero nocturno" (P1). Todo el
  tema en `src/theme` (un solo lugar). Interacciones: pulso "en vivo", onda de audio animada,
  tarjetas por capas (LayoutAnimation), switches físicos.

**Pendiente (siguiente).** Cablear pantallas a las capacidades reales del backend (hoy con datos de
maqueta), push notifications (expo-notifications) con activación/desactivación fácil, y caché
offline-first. `npm install` + `npx expo start` desde `apps/mobile`.

**Alternativas descartadas.** iOS nativo SwiftUI (más lento, sin Android/web compartido); tab bar
estándar de expo-router con pestañas estáticas (no soporta el hub central fijo con laterales
contextuales por módulo); Context en vez de zustand (peor para estado transversal al árbol).

---

## D-0028 — Podcast: sin repetición (dedup por embeddings) + instrucción/objetivo editable por tema
**Estado:** aceptada · Fase 5 · **implementada** (2026-07-22)

**Implementación.** `angles.py` (dominio `EpisodeAngle`, puerto `AngleStore`, servicio
`AngleMemory`), `in_memory_angles.py` (coseno real) y `pg_angles.py` (pgvector, migración 0005,
índice HNSW). Cada `compose_episode` pide al modelo un campo `angle` (4–8 palabras) sin llamada
extra (va en el mismo JSON del guion), lo embebe y lo guarda por tema. Antes de generar, recupera
por similitud los ángulos ya tratados y los inyecta en el prompt vía `compile_instruction`
(`onboarding.py`, bloque "enseña un ángulo nuevo, NO repitas"). La instrucción/objetivo editable
vive en el `OnboardingForm` persistido en el `Topic` (ver [[D-0029]]).

**Contexto.** Al escuchar varios episodios de un mismo tema, el usuario nota que el contenido se
repite. Quiere que Heraldo suene como un **experto que sale todos los días pero sin repetir** lo ya
dicho. Además, distintos temas tienen **objetivos distintos** (aprender una habilidad, salud mental,
otro fin) y el usuario quiere **fijar y editar esa intención** por tema, y ajustarla con el tiempo si
cambia o no queda satisfecho.

**Decisión (a implementar).**
- **No repetición vía memoria del tema:**
  - Guardar, por cada episodio entregado, **embeddings** de sus ideas/ángulos principales (no solo la
    URL de la fuente). Reusar el `EmbeddingProvider` + pgvector ya existentes.
  - Al generar un episodio nuevo: recuperar los ángulos ya cubiertos del tema y **filtrar/penalizar
    por similitud** (dedup semántico) para forzar contenido fresco. Pasar al prompt un resumen de "ya
    dicho: no lo repitas" con **presupuesto fijo de tokens**.
  - La deduplicación de **fuentes** sigue determinística (normalizar URL / clustering); esto es una
    capa **semántica** encima, sobre el contenido entregado. Complementa [[D-0022]].
- **Instrucción/objetivo editable por tema:**
  - `TopicProfile` gana un campo **`objective`/`instruction`** editable (texto libre acotado) que
    orienta el tono y el fin del podcast (habilidad, salud mental, etc.).
  - Se define en la **disección** (punto de entrada de selección de tema) y se puede **editar después**
    (capacidad `update_topic`), sin recrear el tema. El guion lo inyecta como parte del prompt.
- Ambas cosas se cablean **después** de: subir la app por TestFlight y conectar la app al backend.

**Alternativas descartadas.** Dedup solo por URL/fuente (no evita repetir la misma idea desde otra
fuente); mandar todo el historial de episodios al LLM (caro, rompe el presupuesto de tokens); objetivo
global único para todo Heraldo (distintos temas necesitan distinta intención).

---

## D-0029 — Onboarding como formulario + cadencia por tema + scheduler determinístico
**Estado:** aceptada · Fase 5 · **implementada** (backend + app; trigger cron pendiente de ops)

**Contexto.** El usuario quiere fijar por tema: objetivo, tono, cadencia (frecuencia + hora) y
respuestas a preguntas específicas del tema, todo en un **formulario limpio**. Las partes fijas
(objetivo, tono, cadencia) **no deben gastar IA**; solo las **preguntas específicas del tema** las
genera la IA, cayendo en un lugar designado del formulario. El resultado se compila en un **prompt
ordenado** que guía la generación. Además: **noticias auto, podcast pregunta**.

**Decisión.**
- **Modelo (`onboarding.py`):** `Objective` (aprender / salud mental / informarse / otro), `Style`
  (4 switches deterministas), `TopicQuestion` (pregunta IA + respuesta), `OnboardingForm`.
  `compile_instruction(form, topic_name, covered_angles)` produce el prompt ordenado. Todo puro.
- **Persistencia:** el `Topic` gana `cadence` (`Cadence`: frecuencia→días + hora) y `onboarding`
  (`OnboardingForm`). Migración 0004 (columnas `cadence_*` + `onboarding` JSON). El `TopicDTO`
  ahora devuelve perfil + cadencia + onboarding para poder re-generar y precargar el formulario.
- **Flujo IA barato:** el onboarding reusa `propose_topic_questions` (preguntas del tema) y
  `compile_topic_profile` (perfil de búsqueda). Las mismas respuestas alimentan el `OnboardingForm`
  y el perfil, sin llamadas IA extra para las partes fijas.
- **Scheduler (`cadence.is_due` + capacidad `due_topics`):** determinístico ($0). Devuelve los
  temas cuyo podcast toca ahora (hora elegida + período cumplido desde la última entrega), cada uno
  con `needs_approval=true` (**podcast pregunta**). Las **noticias** siguen siendo candidatos en
  vivo ($0, sin IA hasta que eliges profundizar), por eso son "auto".
- **App:** pantalla `onboarding.tsx` (formulario con switches + cadencia + preguntas IA en su slot)
  que crea el tema; podcasts recibe `topicId` y lo pasa a `compose_episode`, activando instrucción
  + memoria de ángulos.

**Notificaciones push (implementadas).** Puerto `PushSender` + adaptador `ExpoPushSender` (Expo
Push API, en lote), puerto `PushTokenStore` (in-memory + Postgres, migración 0006), capacidad
`register_push_token` (la app registra su token al abrir) y `run_scheduler_tick` (revisa cadencia →
push "¿generamos hoy tu podcast de X?" con `data.topic_id`). CLI `scheduler_cli.py` + **cron en
`render.yaml`** (`0 * * * *`, `uv run python -m jarvis.interfaces.scheduler_cli`, cero IA). En la
app: `usePushSetup` registra el token y **rutea a Podcasts** con el `topicId` al tocar el aviso.

**Pendiente (activación, no código):** desplegar el `render.yaml` actualizado en Render (crea el
cron) y aceptar el permiso de push en el build de TestFlight (los tokens Expo solo existen en
dispositivo real). La entrega automática *del audio* sigue siendo bajo aprobación (podcast pregunta);
el tap abre la pantalla para generar. Deep-link de "aprobar y generar en un toque" queda como mejora.

**Alternativas descartadas.** Generar con IA las partes fijas del formulario (gasto inútil, D-0001);
mandar el `OnboardingForm` completo en cada `compose` (redundante: se carga por `topic_id`); cadencia
global única (cada tema tiene su ritmo).

---

## D-0030 — Vigencia del stack: última estable madura, upgrade Expo 52 → 56
**Estado:** aceptada · Fase 4

**Contexto.** El build de iOS falló (`XCODE_BUILD_ERROR`: `fmt/consteval` no es constante) al forzar
`image: latest` (Xcode 26) sobre **Expo SDK 52 / RN 0.76**, que no compila con ese toolchain. Apple
exige el SDK nuevo (ITMS-90725); el SDK que Apple pide es justo el que rompe la versión vieja. Ningún
build de SDK 52 es aceptable. El problema fue **quedarse atrás**, no ir adelante.

**Decisión.**
- **Regla dura:** el stack (lenguajes, frameworks, SDKs, dependencias) se mantiene en la **última
  versión estable madura** — estable con parches, no recién liberada (nada de bleeding edge día-uno).
  No se deja envejecer; si algo quedó atrás se sube en el mismo cambio. Registrada en `CLAUDE.md`.
- **Acción:** subir Expo **52 → 56** (última estable madura; la 57 salió recién). Resuelve el requisito
  de Apple (Xcode 26) y el error `fmt` de raíz, y deja el proyecto listo para el config plugin nativo
  del Share Extension del módulo de reels (D-0031, futuro).
- Upgrade con herramientas de Expo (`expo install --fix`, `expo-doctor`); gates verdes (`tsc`,
  `expo export`) antes de lanzar el build.

**Alternativas descartadas.** Parchar `fmt` con `patch-package` en SDK 52 (hack frágil, no moderniza,
reaparece en otro punto del toolchain); ir a SDK 57 recién liberada (reintroduce inestabilidad día-uno,
contra el objetivo de no repetir el error).

---

## Decisiones abiertas (pendientes)
- **Umbral y estrategia del caché semántico** (similitud mínima para considerar "equivalente").
- **Disparo exacto de la consolidación** (episodic) y política de decaimiento/olvido.
