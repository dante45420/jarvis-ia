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

## Decisiones abiertas (pendientes)
- **Modelo(s) de embeddings** económico(s) a usar por defecto.
- **Umbral y estrategia del caché semántico** (similitud mínima para considerar "equivalente").
