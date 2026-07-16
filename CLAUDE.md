# CLAUDE.md — Jarvis

Reglas operativas para Claude trabajando en este repositorio. Este archivo se
carga en cada sesión: se mantiene **corto** a propósito. El detalle vive en `docs/`.

## Qué es Jarvis

Asistente virtual personal, orientado a costo mínimo y escalabilidad extrema.
El norte y el alcance están en `docs/VISION.md`. No lo repitas aquí.

## Mapa del proyecto (empieza siempre por acá)

| Documento | Para qué |
|-----------|----------|
| `docs/VISION.md` | Norte, principios y alcance. El *porqué*. |
| `docs/ARCHITECTURE.md` | Stack, capas, puertos/adaptadores, pipeline costo-primero, memoria. El *cómo*. |
| `docs/ROADMAP.md` | Fases y **estado actual**. Léelo para saber dónde retomar. |
| `docs/DECISIONS.md` | Bitácora de decisiones y su justificación. Léelo antes de cambiar algo estructural. |

**Al iniciar una sesión nueva:** lee `docs/ROADMAP.md` (estado actual) y esta tabla.
No leas todo el código; los docs están escritos para que retomes sin escanear el repo.

## Reglas duras (no negociables)

### Prioridad 1 — Ahorro de tokens
- Si algo lo puede hacer código determinístico, lo hace código. La IA es el último recurso, no el primero.
- Todo request a un LLM pasa por el **pipeline costo-primero** (ver `ARCHITECTURE.md`): reglas → caché → RAG con presupuesto de tokens → modelo más barato capaz vía OpenRouter.
- Nunca mandes historial completo a un LLM. Recupera solo lo relevante (RAG) y resume lo viejo.
- Salidas de LLM en formato estructurado (function calling / JSON), no prosa, salvo que el usuario final la lea.

### Prioridad 2 — Escalabilidad (igual de importante)
- Arquitectura hexagonal (puertos y adaptadores). El dominio no conoce infraestructura.
- Bajo acoplamiento, alta cohesión. Todo proveedor externo (OpenRouter, DB, canal, embeddings) va detrás de una interfaz propia.
- Tests obligatorios para lógica de dominio y casos de uso. Sin tests no se da por hecho.
- Código muerto se borra. Nada de bloques comentados ni imports sin uso.

### Estilo de código
- Funciones cortas (~<20 líneas), una sola responsabilidad, nombre = un verbo. Orquestadores delegan a helpers.
- Máximo 2 niveles de anidación; extrae guard clauses.
- Identificadores en **inglés** (estándar de industria e interoperabilidad).
- Texto para el usuario final y comentarios en español usan **español chileno** (tuteo: `exporta`, `revisa`, `configura`; nunca voseo).
- Sin marcas de código generado por IA. Debe leerse como escrito por un dev senior.

### Documentación
- Optimizada para que Claude retome, no para lucirse. Concisa y estructurada.
- Cambió algo estructural → actualiza `docs/DECISIONS.md` y `docs/ARCHITECTURE.md` en el mismo cambio.
- Avanzaste una fase → actualiza el **estado actual** en `docs/ROADMAP.md`.

## Flujo de trabajo
- Cambios chicos y verificables. Cada módulo con su test antes de avanzar.
- Antes de introducir una librería nueva, verifica que aporte escalabilidad real y déjala anotada en `DECISIONS.md`.
