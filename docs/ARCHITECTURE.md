# Arquitectura — Jarvis

El *porqué* está en `VISION.md`. Acá va el *cómo*. Las decisiones concretas y su
justificación (incluyendo alternativas descartadas) están en `DECISIONS.md`.

## Stack

| Capa | Elección | Razón (resumen) |
|------|----------|-----------------|
| Lenguaje/API | Python 3.12+, FastAPI (async) | Ecosistema IA + async nativo. |
| Gestor de deps | `uv` | Rápido y reproducible. |
| Persistencia | PostgreSQL + `pgvector` | Relacional **y** vectorial en una sola base = menos servicios, menos costo. |
| LLM gateway | OpenRouter detrás del puerto `LLMProvider` | Ruteo al modelo más barato capaz. Nunca acoplado al SDK del proveedor. |
| Embeddings | Modelo económico detrás del puerto `EmbeddingProvider` | RAG barato; proveedor intercambiable. |
| Caché / cola | Redis (se introduce cuando se necesite; hasta entonces, Postgres) | No sumar infra antes de tiempo. |
| Jobs async | Empezar con scheduler liviano; graduar a cola async cuando escale | Proactividad (recordatorios, podcast) desacoplada. |
| Frontend | React + TypeScript + Vite + Tailwind + shadcn/ui | UI limpia con colapsables; deploy barato (estático). |
| Observabilidad | Logging estructurado + telemetría de **tokens y costo** | El costo es un ciudadano de primera clase, se mide. |
| Calidad | pytest, ruff, mypy | Tests + lint + tipos como parte del flujo. |
| Empaque | Docker | Local reproducible; deploy a plataforma barata. |

> Proveedor de nube concreto (Supabase / Fly.io / Railway / Render u otro): decisión
> abierta, se fija en `DECISIONS.md` cuando se elija. Criterio: free tier generoso y
> Postgres administrado. No condiciona el código porque todo va detrás de puertos.

## Capas (hexagonal / puertos y adaptadores)

```
interfaces/     Entrada-salida: API web (FastAPI), adaptadores de canal (web, luego telegram)
application/    Casos de uso: orquestan el dominio. Sin detalle de infraestructura.
domain/         Núcleo puro: entidades, reglas, PUERTOS (interfaces). Sin dependencias externas.
adapters/       Implementaciones de puertos: OpenRouter, pgvector, embeddings, caché, canales.
platform/       Config, logging, telemetría, arranque.
```

Regla de dependencia: las flechas apuntan **hacia adentro**. `domain` no importa nada de
`adapters`. Cambiar un proveedor = escribir un adaptador nuevo, sin tocar dominio ni casos de uso.

### Puertos principales (interfaces del dominio)
- `LLMProvider` — completar/chat con selección de modelo y reporte de costo.
- `EmbeddingProvider` — texto → vector.
- `VectorStore` — guardar/buscar por similitud (impl: pgvector).
- `MemoryStore` — persistencia de memoria estructurada.
- `SemanticCache` — buscar/guardar respuestas por equivalencia de intención.
- `ChannelAdapter` — recibir/emitir mensajes por canal (web, telegram…).
- `ModelRouter` — dado un contexto, elige el modelo más barato capaz.
- `UsageMeter` — emite un `UsageRecord` por cada llamada de IA (o llamada evitada).

## Pipeline costo-primero (el corazón del sistema)

Todo mensaje entrante pasa por esta cadena. Cada paso intenta **cerrar el request antes**
de llegar al LLM. El LLM es el último eslabón, no el primero.

```
1. Canal recibe el mensaje (web / telegram) y lo normaliza.
2. Intento determinístico: reglas/regex/slot-filling resuelven intenciones obvias
   ("recuérdame X a las Y", "lista mis tareas") SIN LLM. Si resuelve → responde y termina.
3. Caché semántico: ¿hay una respuesta equivalente ya calculada? Si sí → responde y termina.
4. NLU/router barato: clasifica intención y elige el modelo más barato capaz (ModelRouter).
5. Ensamblado de contexto: RAG recupera solo memorias relevantes (top-k por embeddings)
   + resumen del historial. Se aplica un PRESUPUESTO de tokens estricto.
6. Llamada al LLM vía OpenRouter con function calling (salida estructurada).
7. Post-proceso determinístico + persistencia de memoria (extracción barata de hechos).
8. Se guarda en caché semántico y se registra costo/tokens en telemetría.
```

Cada paso que evita el paso 6 es dinero ahorrado. Optimizar aquí es optimizar el negocio.

## Sistema de memoria

La memoria es lo que hace a Jarvis "personal" y también lo que controla el costo del contexto.
Cuatro tipos, cada uno con su estrategia de lectura/escritura:

| Tipo | Qué guarda | Escritura | Lectura |
|------|-----------|-----------|---------|
| **Working** | Turnos recientes de la conversación | Ventana acotada, automática | Directa (los últimos N) |
| **Episodic** | Conversaciones pasadas resumidas + embebidas | Resumen batch con modelo barato | RAG por similitud |
| **Semantic** | Hechos durables del usuario (perfil, preferencias) | Extracción determinística/barata | Estructurada + RAG |
| **Procedural** | Rutinas y "cómo hacer" del usuario | Explícita | Por intención |

Principios: escribir memoria con el método más barato disponible (determinístico > modelo
barato > modelo capaz); leer siempre lo mínimo relevante, nunca todo.

## Telemetría de costo y dashboard

El costo de IA es una métrica de primera clase: se mide en el punto de origen y se muestra.

**Registro base (`UsageRecord`).** Cada llamada que involucra un modelo (o que la evita)
emite un registro con las dimensiones que el dashboard necesita para desglosar:

| Campo | Uso |
|-------|-----|
| `occurred_at` | Agregación por día/hora. |
| `model` | Desglose por modelo. |
| `task` | Desglose por tarea/intención (ej. `chat`, `summarize_memory`, `route`, `podcast`). |
| `channel` | Web, telegram… |
| `tokens_in` / `tokens_out` | Insumo del costo y del análisis. |
| `cost` | Calculado desde el precio del modelo (tabla de precios versionada). |
| `outcome` | `llm_call` · `cache_hit` · `deterministic` (permite ver **cuánto se ahorró** evitando el LLM). |
| `request_id` | Traza y correlación. |

La emisión va detrás del puerto `UsageMeter`; el almacenamiento es Postgres. Las
agregaciones (por día/modelo/tarea) se resuelven en SQL —determinístico y barato—, no en la app.

**Dashboard (revelación progresiva).** La UI parte de lo mínimo y profundiza al hacer click:

```
Nivel 0  →  Gasto total (hoy / mes) + tendencia. Una sola cifra clara.
Nivel 1  →  click → desglose por día.
Nivel 2  →  click en un día → desglose por modelo.
Nivel 3  →  click en un modelo → desglose por tarea, y ahorro por caché/determinístico.
```

Cada nivel es una agregación SQL distinta sobre `UsageRecord`; la API expone un endpoint de
consulta con filtros (rango, modelo, tarea) y el frontend solo pinta.

## Frontend

- Revelación progresiva: el dashboard muestra lo esencial; el detalle vive en colapsables,
  paneles laterales y menú hamburguesa. Se accede solo cuando se pide.
- Habla con el backend por una API estable; no conoce proveedores ni modelos.
- Estáticamente desplegable (barato).

## Convenciones transversales
- Errores y logs con contexto suficiente para depurar sin reproducir.
- Telemetría de costo por request vía `UsageMeter` (ver sección dedicada). Es la métrica
  de salud del proyecto y el insumo del dashboard.
- Configuración por entorno (nada de secretos en el código).
